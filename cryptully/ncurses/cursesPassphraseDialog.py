import curses

from getpass import getpass


class CursesPassphraseDialog(object):
    def __init__(self, screen, verify=False):
        self.screen = screen
        self.verify = verify


    def show(self):
        (height, width) = self.screen.getmaxyx()

        passphraseWindow = self.screen.subwin(3, 36, height/2 - 1, width/2 - 18)

        # Turn on echo and wait for enter key to read buffer
        curses.echo()
        curses.nocbreak()

        while True:
            passphraseWindow.border(0)
            passphraseWindow.addstr(1, 1, "Passphrase: ")
            passphraseWindow.refresh()
            passphrase = getpass('')

            if not self.verify:
                break

            passphraseWindow.clear()
            passphraseWindow.border(0)
            passphraseWindow.addstr(1, 1, "Verify: ")
            passphraseWindow.refresh()
            verifyPassphrase = getpass('')

            if passphrase == verifyPassphrase:
                break
            else:
                curses.cbreak()
                CursesDialog(self.screen, errors.VERIFY_PASSPHRASE_FAILED, '', isBlocking=True).show()
                curses.nocbreak()

        # Turn off echo and disable buffering
        curses.cbreak()
        curses.noecho()

        # Get rid of the passphrase window
        passphraseWindow.clear()
        passphraseWindow.refresh()

        return passphrase
