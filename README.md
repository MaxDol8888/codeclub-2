# codeclub respository README

Some simple projects which might prove useful in Code Club sessions.

SevenSegment.py - A visual seven-segment display with a very simple interface to control which
                  segments are lit.  Requires Tkinter python package.  To test it, run
                  python SevenSegment.py
                  
                  To use it in another Python project:
                  from SevenSegment import Display
                  disp = Display(x) # Create the blank display with x digits (will do 1 if x is omitted)
                  disp.set(val1, val2, ...) # Where each val is an integer, the lowest-order 8 bits of which determine
                                            # which of the 8 segments (seven plus a decimal point) are
                                            # illuminated in a given digit.  Just specify as many vals as there are
                                            # digits in your display.
                  
morse.py -  Set up a rudimentary Morse Code station which can connect to another station on
            a friend's computer.  Intended for use with Raspberry Pi, with a each person's
            Pi having a simple pair of circuits: one with a switch connection to a GPIO input
            and one with a buzzer connected to a GPIO output.  Press your switch and make the
            other person's buzzer go off.
           
            To use it in another Python project (very basic example):
           
            from morse import wire
            w = wire()
            w.connect()  # At this point you'll be told your IP address and prompted to enter
                         # the other person's IP address.
            # Tell the other end they should buzz.
            w.my_button(wire.PRESSED)
            # Check if my buzzer should be going.
            if w.my_buzzer():
                # Use GPIO to turn on my buzzer.
