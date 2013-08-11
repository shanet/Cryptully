import curses

from utils import constants


class CursesModeDialog(object):
    def __init__(self, screen):
        self.screen = screen


    def show(self):
        (height, width) = self.screen.getmaxyx()

        modeDialog = self.screen.subwin(4, 23, height/2 - 3, width/2 - 11)
        modeDialog.border(0)

        # Enable arrow key detection for this window
        modeDialog.keypad(True)

        # Disable the cursor
        curses.curs_set(0)

        position = constants.CONNECT

        while True:
            if position == constants.CONNECT:
                modeDialog.addstr(1, 2, "Initiate connection", curses.color_pair(4))
                modeDialog.addstr(2, 2, "Wait for connection")
            else:
                modeDialog.addstr(1, 2, "Initiate connection")
                modeDialog.addstr(2, 2, "Wait for connection", curses.color_pair(4))

            self.screen.refresh()
            key = modeDialog.getch()
            # Enter key
            if key == ord('\n'):
                break
            elif position == constants.CONNECT:
                position = constants.WAIT
            elif position == constants.WAIT:
                position = constants.CONNECT

        # Re-enable the cursor
        curses.curs_set(2)

        modeDialog.clear()
        modeDialog.refresh()

        return position
