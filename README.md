# Richard-Code-Club-Projects

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
                  
