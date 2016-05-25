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
        self.is_receiving = None
        self.not_receiving = None
        self.role = role
        self.test_mode = False
        self.button_state = self.RELEASED
        self.buzzer_state = self.OFF

    # Connect to the other end and start listening.
    def connect(self, self_test=True):
        # By default we do a quick self-test so it's easy to see when people
        # haven't wired up properly.
        if self_test:
            self.self_test()
        
        print("Your address is %s" % self.localip)
        self.remoteip = input("Please enter the other person's address: ")

        if self.role == self.UNSPECIFIED:
            # The user hasn't specified which role they want, so arbitrarily
            # choose who's going to be client and server by comparing the IP
            # addresses.
            #
            # You might want to specify the role if, for example, your doing
            # some testing and you want client and server roles on the same
            # system, with the same IP address
            if self.remoteip < self.localip:
                self.role = self.SERVER
            else:
                self.role = self.CLIENT
        self.reconnect()

    def reconnect(self):        
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
        print("Connected!\n\n  PRESS CTRL-C TO STOP THE PROGRAM\n\n")
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

        print("Connected!\n\n  PRESS CTRL-C TO STOP THE PROGRAM\n\n")
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
        if self.test_mode:
            # We're in test mode, so just print a message to say that the button
            # was pushed ok.
            print("Button press works.  Hooray.  Now release the button.")
        else:
            self._signal_on_wire(self.ON)

    def stop_signal(self):
        if self.test_mode:
            # We're in test mode, so print a message to say that the button release
            # has registered ok, and turn off the buzzer.
            print("Button release works.  Hooray.  Turning buzzer off.")
            self._not_receiving()
            self.test_mode = False
        else:
            self._signal_on_wire(self.OFF)

    # Function for the user code to call to tell us the state of its button.
    # Sends a signal to the other end whenever the button state changes.
    def _signal_on_wire(self, state):
        if state != self.button_state:
            self.button_state = state
            # Send a message consisting of an ASCII digit to
            # represent the button state.
            message = "%s" % self.button_state
            self.connection.sendall(bytes(message, 'utf-8'))

    def listen_for_signal(self):
        received_a_signal = False
        try:
            while True:
                ready = select.select([self.connection], [], [])
                if ready[0]:
                    if not received_a_signal:
                        print("Receiving OK")
                        received_a_signal = True
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
            self.sock.close()
        finally:
            self.connected = False

    def self_test(self):
        """Perform a self-test to make sure the button and buzzer are
        correctly connected."""
        all_good = True
        # Set a flag to indicate to the functions triggered by the button that
        # we're in test mode, so we don't really need to send signals - we
        # just need to print a message and exit test mode.
        self.test_mode = True
        if self._is_receiving is None:
            print ("You haven't set the wire's is_receiving function. Check the code")
            all_good = False
        if self._not_receiving is None:
            print ("You haven't set the wire's not_receiving function. Check the code")
            all_good = False
        print("You should now hear your buzzer. If you don't, check your code and wiring")
        self._is_receiving()
        print("Push your button to turn the buzzer off.  If this doesn't work,\npress Ctrl-C to stop the program, then check your code and wiring.")

        while self.test_mode:
            pass

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
