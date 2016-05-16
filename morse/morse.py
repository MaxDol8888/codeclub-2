# morse.py
# Utility to communicate with another device running Python and
#   - tell it whether to buzz or not
#   - listen to it to decide whether we need to buzz or not at this end.
#
# The decoding aspects of this utility (to automatically decode received
# messages) are lifted from raspberrypi.org's learning resources.
# https://www.raspberrypi.org/learning/morse-code-virtual-radio/worksheet
# Provided under Creative Commons license
# http://creativecommons.org/licenses/by-sa/4.0
import threading
import subprocess
import socket
import select
import time
from morse_lookup import *

# Set up some constants for the duration of a DOT.  This is the time unit
# about which everything else is based.  If you get good at Morse code,
# reduce the time unit.
TIME_UNIT = 0.2
LETTER_GAP = 3 * TIME_UNIT
WORD_GAP = 7 * TIME_UNIT

class Wire():

    PRESSED = "1"
    RELEASED = "0"
    ON = "1"
    OFF = "0"
    SERVER = 1
    CLIENT = 2
    UNSPECIFIED = 3
    DASH = "-"
    DOT = "."

    # Gets the local IP address of the system.  Assumes there's only 1 IPv4
    # address which isn't the loopback address, and it only works with IPv4.
    def get_local_ip(self):
        # Run the native "ip addr show" command and parse the output to find
        # the system's IP address.
        output = subprocess.check_output(
            'ip addr show | grep "inet " | grep -v "127.0.0.1"',
            shell=True)
        output = output.decode('utf-8')
        prefix = output.split()[1]
        ipaddr = prefix.split('/')[0]
        return ipaddr

    def __init__(self, role=UNSPECIFIED):
        self.localip = self.get_local_ip()
        self.connected = False
        self.key_up_time = 0
        self.buffer = []
        print("Your address is %s" % self.localip)
        self.remoteip = input("Please enter the other person's address: ")

        if role == self.UNSPECIFIED:
            # The user hasn't specified which role they want, so arbitrarily
            # choose who's going to be client and server by comparing the IP
            # addresses.
            #
            # You might want to specify the role if, for example, your doing
            # some testing and you want client and server roles on the same
            # system, with the same IP address
            if self.remoteip < self.localip:
                role = self.SERVER
            else:
                role = self.CLIENT
        self.role = role

        self.button_state = self.RELEASED
        self.buzzer_state = self.OFF

    # Connect to the other end and start listening.
    def connect(self):
        if not self.connected:
            if self.role == self.SERVER:
                self.start_server()
            else:
                self.start_client()

        decoder_t = threading.Thread(target=self.decoder_thread, args=())
        decoder_t.start()
        t = threading.Thread(target=self.listen_for_signal, args=())
        t.start()

    # Start the connection, acting as server.
    def start_server(self):
        # Create and bind a listen socket.
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (self.localip, 10000)
        self.sock.bind(server_address)
        self.sock.listen(1)

        # Wait for a connection
        print("Waiting for the other end to connect")
        self.connection, self.client_address = self.sock.accept()
        print("Connected!")
        self.connected = True

    # Start the connection, acting as client.
    def start_client(self):
        # Connect a socket and attempt to connect to the server.
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (self.remoteip, 10000)
        print("Connecting to the other end...")

        # Keep trying until connected.  If the other end refuses the connection
        # then that probably means the other end just hasn't started up yet, so
        # wait and try again.  Any other exceptions (e.g. the other end isn't
        # routable) should be re-raised.
        while not self.connected:
            try:
                self.sock.connect(server_address)
                self.connected = True
            except socket.error as exp:
                if exp.errno == socket.errno.ECONNREFUSED:
                    print("...waiting for the other end to start up...")
                    time.sleep(5)
                else:
                    raise
            except:
                raise

        print("Connected!")
        self.connection = self.sock

    @property
    def is_receiving(self):
        return self._is_receiving

    @is_receiving.setter
    def is_receiving(self, callback):
        self._is_receiving = callback

    @property
    def not_receiving(self):
        return self._not_reeiving

    @not_receiving.setter
    def not_receiving(self, callback):
        self._not_receiving = callback

    def send_signal(self):
        self._signal_on_wire(self.ON)

    def stop_signal(self):
        self._signal_on_wire(self.OFF)

    # Function for the user code to call to tell us the state of its button.
    # Sends a signal to the other end whenever the button state changes.
    def _signal_on_wire(self, state):
        if state != self.button_state:
            self.button_state = state
            # Attempt to send a message consisting of an ASCII digit to
            # represent the button state.  In the event of socket failure we
            # should attempt to reconnect, but other exceptions (e.g. the user
            # trying to kill the program with Ctrl-C) should be raised.
            try:
                message = "%s" % self.button_state
                self.connection.sendall(bytes(message, 'utf-8'))
            except socket.error:
                print("Connection lost - retrying.")
                self.connected = False
                try:
                    self.sock.close()
                finally:
                    self.connect()
            except:
                self.connected = False
                raise

    def listen_for_signal(self):
        try:
            while True:
                ready = select.select([self.connection], [], [])
                if ready[0]:
                    data = self.connection.recv(4096)
                    data = data.decode('utf-8')
                    data = data[-1:]
                    if data == self.ON:
                        self._is_receiving()
                        # Record time that the other person's button was pressed.
                        key_down_time = time.time()
                    else:
                        self._not_receiving()
                        # Record time that the other person's button was released.
                        self.key_up_time = time.time()
                        key_down_length = self.key_up_time - key_down_time
                        self.buffer.append(self.DASH if key_down_length > TIME_UNIT else self.DOT)
        except:
            try:
                self.sock.close()
            finally:
                self.connected = False

    def decoder_thread(self):
        new_word = False
        while True:
            time.sleep(.01)
            key_up_length = time.time() - self.key_up_time
            if len(self.buffer) > 0 and key_up_length >= WORD_GAP:
                new_word = True
                bit_string = "".join(self.buffer)
                try_decode(bit_string)
                del self.buffer[:]
            elif new_word and key_up_length >= 4.5:
                new_word = False
                sys.stdout.write(" ")
                sys.stdout.flush()
