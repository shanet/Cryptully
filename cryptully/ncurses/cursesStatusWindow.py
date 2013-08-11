import curses

from utils import constants


class CursesStatusWindow(object):
    def __init__(self, screen, text):
        self.screen = screen
        self.text = text


    def show(self):
        (height, width) = self.screen.getmaxyx()

        self.statusWindow = self.screen.subwin(height-3, width-34)

        self.setText(self.text)


    def setText(self, text):
        (height, width) = self.statusWindow.getmaxyx()

        self.text = text

        self.statusWindow.clear()
        self.statusWindow.border(0)
        self.statusWindow.addstr(1, width-len(text)-1, text)
        self.statusWindow.refresh()
