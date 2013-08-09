import curses

from utils import constants


class CursesAcceptDialog(object):
    def __init__(self, ncurses, nick):
        self.ncurses = ncurses
        self.nick = nick


    def show(self):
        dialogWidth = 28 + len(self.nick);
        acceptWindow = self.ncurses.screen.subwin(6, dialogWidth, self.ncurses.height/2 - 3, self.ncurses.width/2 - int(dialogWidth/2))
        acceptWindow.border(0)

        # Enable arrow key detection for this window
        acceptWindow.keypad(True)

        # Disable the cursor
        curses.curs_set(0)

        acceptWindow.addstr(1, 1, "Recveived connection from %s" % self.nick)

        position = constants.ACCEPT

        while True:
            if position == constants.ACCEPT:
                acceptWindow.addstr(3, 2, "Accept", curses.color_pair(4))
                acceptWindow.addstr(4, 2, "Reject")
            else:
                acceptWindow.addstr(3, 2, "Accept")
                acceptWindow.addstr(4, 2, "Reject", curses.color_pair(4))

            self.ncurses.screen.refresh()
            key = acceptWindow.getch()
            # Enter key
            if key == ord('\n'):
                break
            elif position == constants.ACCEPT:
                position = constants.REJECT
            elif position == constants.REJECT:
                position = constants.ACCEPT

        # Re-enable the cursor
        curses.curs_set(2)

        acceptWindow.clear()
        acceptWindow.refresh()

        return position
