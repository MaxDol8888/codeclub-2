# morse.py
# Utility to communicate with another device running Python and
#   - tell it whether to buzz or not
#   - listen to it to decide whether we need to buzz or not at this end.

import subprocess
import socket
import select
import time

class wire():

    PRESSED = "1"
    RELEASED = "0"
    ON = "1"
    OFF = "0"
    SERVER = 1
    CLIENT = 2

    def get_local_ip(self):
        output = subprocess.check_output('ip addr show | grep "inet " | grep -v "127.0.0.1"', shell=True)
        prefix = output.split()[1]
        ipaddr = prefix.split('/')[0]
        return ipaddr

    def __init__(self, role):
        self.localip = self.get_local_ip()
        self.connected = False
        print "Your address is %s" % self.localip
        self.remoteip = raw_input("Please enter the other person's address: ")

        # Arbitrarily choose who's going to be client and server in the pair.
        # Just trust that people will pair up correctly, entering their
        # respective IP addresses.
        self.role = role
        # if self.remoteip < self.localip:
        #     self.role = self.SERVER
        # else:
        #     self.role = self.CLIENT
        self.button_state = self.RELEASED
        self.buzzer_state = self.OFF

    def connect(self):
        if not self.connected:
            if self.role == self.SERVER:
                self.start_server()
            else:
                self.start_client()

    def start_server(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (self.localip, 10000)
        self.sock.bind(server_address)
        self.sock.listen(1)

        # Wait for a connection
        print 'Waiting for the other end to connect'
        self.connection, self.client_address = self.sock.accept()
        print 'Connected!'
        self.connected = True

    def start_client(self):
        # Create a TCP/IP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect the socket to the port where the server is listening
        server_address = (self.remoteip, 10000)
        print 'Connecting to the other end...'

        while not self.connected:
            try:
                self.sock.connect(server_address)
                self.connected = True
            except socket.error, v:
                errorcode = v[0]
                if errorcode == socket.errno.ECONNREFUSED:
                    print '...waiting for the other end to start up...'
                    time.sleep(5)
                else:
                    raise

        print 'Connected!'
        self.connection = self.sock

    def my_button(self, state):
        if state != self.button_state:
            self.button_state = state
            try:
                # Send data
                message = "%s" % self.button_state
                self.connection.sendall(message)
            except socket.error:
                print 'Connection lost - retrying.'
                self.connected = False
                try:
                    self.sock.close()
                finally:
                    self.connect()
            except:
                self.connected = False
                raise

    def my_buzzer(self):
        try:
            ready = select.select([self.connection], [], [], 0.05)
            if ready[0]:
                data = self.connection.recv(4096)
                self.buzzer_state = data[-1:]
        except socket.error:
            print 'Connection lost - retrying.'
            self.connected = False
            try:
                self.sock.close()
            finally:
                self.connect()
        except:
            self.connected = False
            raise

        if self.buzzer_state == "1":
            return True
        else:
            return False
