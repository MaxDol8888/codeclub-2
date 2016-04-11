# SevenSegment.py
# Produces a visual representation of a seven-segment display which the user
# can control.

# Import Tkinter to do the graphics and the time package for the demo mode.
import Tkinter
import time

# Display - a seven-segment display
class Display(Tkinter.Tk):

    # Set up some colours to use for background, segment outlines and
    # segment colours when they're on and off.
    bgcolor = '#111111'
    linecolor = '#222222'
    oncolor = '#00FF00'
    offcolor = '#111111'

    # Set up size of each cell and the border around them (pixels).
    cell_width = 100
    cell_height = 150
    border = 5

    max_cells = 10


    # Class representing a single cell in a 7-segment display.
    class Cell():

        class Segment():

            ON=1
            OFF=0

            # Constructor.
            # Parms:
            #     flag_value  - the bit(s) that this segment responds to.
            #     x_pos       - the x-position of the top-left corner of the
            #                   space where this segment exists on a canvas.
            #     y_pos       - the y-position of the top-left corner of the
            #                   space where this segment exists on a canvas.
            #     width       - the width of the canvas where this segment can
            #                   be drawn.
            #     height      - the height of the canvas where this segment can
            #                   be drawn.
            #     coordinates - a list of (x,y) tuples giving coordinates of a
            #                   polygon (expressed as % of width and height)
            #                   where the segment is drawn.
            #     line_color  - the line colour to use when drawing.
            #     on_colour   - the colour to use when the segment is active.
            #     off_colour  - the colour to use when the segment in inactive.
            def __init__(self, flag_value, x_pos, y_pos, width, height, coordinates, line_color, on_color, off_color):

                # Save off the colours to use.
                self.line_color = line_color
                self.on_color = on_color
                self.off_color = off_color

                # Save the value this segment is responsive to.
                self.flag_value = flag_value

                # Convert raw coordinate tuples to a list of absolute
                # coordinates.
                self.coords = []
                for coord in coordinates:
                    (x, y) = coord
                    x = x_pos + ((width * x) / 100)
                    y = y_pos + ((height * y) / 147)
                    self.coords.append(x)
                    self.coords.append(y)

                self.set_state(self.OFF)

            # Set the state of the segment and update the colour accordingly.
            def set_state(self, new_state):
                self.state = new_state
                if self.state == self.ON:
                    self.color = self.on_color
                else:
                    self.color = self.off_color

            # Draw the segment on a canvas.
            def draw(self, canvas):
                canvas.create_polygon(self.coords,
                    outline=self.line_color,
                    fill=self.color)

        # END class Segment

        def __init__(self, x_pos, y_pos, width, height, line_color, on_color, off_color):
            self.bitflags = 0

            # Create the cell's segments, giving them each coordinates for
            # their polygons as a list of x,y pairs where the coordinate assume
            # a cell 100 pixels wide and 150 high.  The segments will scale
            # appropriately based on the actual width and height.
            self.segments = []
            self.segments.append(self.Segment(0b00000001, x_pos, y_pos, width, height, [(17,0),(65,0),(73,8),(65,16),(17,16),(9,8)], line_color, on_color, off_color))
            self.segments.append(self.Segment(0b00000010, x_pos, y_pos, width, height, [(74,9),(82,17),(82,65),(74,73),(66,65),(66,17)], line_color, on_color, off_color))
            self.segments.append(self.Segment(0b00000100, x_pos, y_pos, width, height, [(74,74),(82,82),(82,130),(74,138),(66,130),(66,82)], line_color, on_color, off_color))
            self.segments.append(self.Segment(0b00001000, x_pos, y_pos, width, height, [(17,131),(65,131),(73,139),(65,147),(17,147),(9,139)], line_color, on_color, off_color))
            self.segments.append(self.Segment(0b00010000, x_pos, y_pos, width, height, [(8,74),(16,82),(16,130),(8,138),(0,130),(0,82)], line_color, on_color, off_color))
            self.segments.append(self.Segment(0b00100000, x_pos, y_pos, width, height, [(8,9),(16,17),(16,65),(8,73),(0,65),(0,17)], line_color, on_color, off_color))
            self.segments.append(self.Segment(0b01000000, x_pos, y_pos, width, height, [(17,66),(65,66),(73,74),(65,82),(17,82),(9,74)], line_color, on_color, off_color))
            self.segments.append(self.Segment(0b10000000, x_pos, y_pos, width, height, [(83,139),(91,131),(99,139),(91,147)], line_color, on_color, off_color))

        def set(self, bitflags = 0):
            self.bitflags = bitflags

            # Loop through the cell's segments, setting them on or off based
            # on the bitflags.
            for segment in self.segments:
                if bitflags & segment.flag_value:
                    segment.set_state(segment.ON)
                else:
                    segment.set_state(segment.OFF)

        def draw(self, canvas):
            # Loop through the segments, adding each one to the canvas.
            for segment in self.segments:
                segment.draw(canvas)

        # END class Cell

    def __init__(self, num_cells=1):
        # Initialization just creates a blank display.
        Tkinter.Tk.__init__(self)
        self.title("Seven Segment Display")

        try:
            num_cells = min(num_cells, self.max_cells)
            num_cells = max(num_cells, 1)
            self.canvas = Tkinter.Canvas(self, width=(self.cell_width*num_cells + 2*self.border), height=(self.cell_height + 2*self.border), borderwidth=0, highlightthickness=0, background=self.bgcolor)

            # Create a line of cells with a border above and to the left.
            self.cells = []
            for ii in range(num_cells):
                new_cell = self.Cell(self.border + ii*self.cell_width, self.border, self.cell_width, self.cell_height, self.linecolor, self.oncolor, self.offcolor)
                self.cells.append(new_cell)

            self.redraw()
        except:
            print("You tried something silly")

    def redraw(self):
        # Clear the canvas and redraw each cell.
        self.canvas.delete("all")
        for cell in self.cells:
            cell.draw(self.canvas)
        self.canvas.pack()
        self.update()


    # set()
    # Sets which segments of the display are lit.
    # Params: Variable number of integers indicating what each cell should
    #         display.
    # Examples: set(0)
    #           set(0b00000110, 0b01011011)
    def set(self, *args):
        try:
            arglist = list(args)

            # Before setting new values, clear the existing values for each
            # cell.
            for cell in self.cells:
                cell.set(0)

            # Make sure we set the right-most cells in the display.
            num_cells_to_set = min(len(self.cells), len(arglist))
            cells_to_set = self.cells[num_cells_to_set * -1:]

            # Now set the cells according to the passed in arguments
            for cell, value in zip(cells_to_set, arglist):
                cell.set(value)
            self.redraw()
        except:
            print("You did something silly")

    # scroll()
    # Scroll a sequence across the display from right to left.
    # Params: sequence - List of integers which make up the "message" to scroll
    #                    across the display.
    #         delay    - The delay, in seconds, between movements.
    def scroll(self, sequence, delay=0.5):
        # Put a load of 'blank' entries at either end of the passed in
        # sequence so that we get something like this.
        #
        #    | | | | | |s|e|q|u|e|n|c|e| | | | | |
        #
        # We can then display a chunk of that at a time to make the
        # "sequence" bit appear to scroll.
        # The number of blanks we need at either end needs to match the
        # size of the display so that scrolling starts and finishes with a
        # blank display.
        blanks = []
        for ii in range(len(self.cells)):
            blanks.append(0)
        sequence.extend(blanks)
        sequence[:0] = blanks

        # Now display the message one chunk at a time.
        for ii in range(1 + len(sequence) - len(self.cells)):
            self.set(*sequence[ii:ii+len(self.cells)])
            time.sleep(delay)


    # A cheater's way to make a display show a number.  If the display isn't
    # big enough then it will only show the lowest-order digits.
    def show_number(self, number):
        # Have a helper array of the bit-patterns for each digit.
        numbers = [0b00111111, # 0
            0b00000110,        # 1
            0b01011011,        # 2
            0b01001111,        # 3
            0b01100110,        # 4
            0b01101101,        # 5
            0b01111101,        # 6
            0b00000111,        # 7
            0b01111111,        # 8
            0b01101111]        # 9

        try:
            # Start by blanking all cells except the last, which is a zero.
            for ii in range(len(self.cells)):
                self.cells[ii].set(0)
            self.cells[len(self.cells)-1].set(numbers[0])

            number = int(number)
            dig_pos = len(self.cells)
            values_to_set = []
            while number > 0 and dig_pos > 0:
                dig_pos = dig_pos - 1
                self.cells[dig_pos].set(numbers[number % 10])
                number = number / 10
            self.redraw()

        except:
            print("You did something silly")


    # demo()
    # Do a demo of the display, Showing the word "HELLO" scrolling on and off
    # Params: none.
    def demo(self):
        self.scroll([0b01110110,0b01111001,0b00111000,0b00111000,0b00111111], 0.2)


def main ():
    disp = Display(8)
    disp.demo()

if __name__ == '__main__':
    main()
