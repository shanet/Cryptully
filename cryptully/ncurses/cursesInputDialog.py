import curses

from utils import constants


class CursesInputDialog(object):
    def __init__(self, screen, prompt):
        self.screen = screen
        self.prompt = prompt


    def show(self):
        (height, width) = self.screen.getmaxyx()

        dialogWidth = len(self.prompt) + 32
        inputWindow = self.screen.subwin(3, dialogWidth, height/2 - 1, width/2 - dialogWidth/2)
        inputWindow.border(0)
        inputWindow.addstr(1, 1, self.prompt)
        inputWindow.refresh()

        # Turn on echo and wait for enter key to read buffer
        curses.echo()
        curses.nocbreak()

        input = inputWindow.getstr(1, len(self.prompt) + 1)

        # Turn off echo and disable buffering
        curses.cbreak()
        curses.noecho()

        # Clear the window
        inputWindow.clear()
        inputWindow.refresh()

        return input
