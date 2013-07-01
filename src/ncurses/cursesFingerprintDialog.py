import curses
import os
import signal

from cursesDialog import CursesDialog

class CursesFingerprintDialog(CursesDialog):

    def __init__(self, screen, serverFingerprint, clientFingerprint):
        CursesDialog.__init__(self, screen, "", "", isError=False, isBlocking=True)
        self.screen            = screen
        self.serverFingerprint = serverFingerprint
        self.clientFingerprint = clientFingerprint


    def show(self):
        (height, width) = self.screen.getmaxyx()

        dialogWidth = len(max(self.serverFingerprint, self.clientFingerprint)) + 2
        dialogHeight = 11

        self.dialogWindow = self.screen.subwin(dialogHeight, dialogWidth, height/2 - int(dialogHeight/2), width/2 - int(dialogWidth/2))
        self.dialogWindow.clear()
        self.dialogWindow.border(0)

        # Add the title
        self.dialogWindow.addstr(1, 1, "Public Key Fingerprints")
        self.dialogWindow.hline(2, 1, 0, dialogWidth-2)

        # Add the fingerprints
        self.dialogWindow.addstr(3, 1, "Server fingerprint:")
        self.dialogWindow.addstr(4, 1, self.serverFingerprint)
        self.dialogWindow.addstr(6, 1, "Client fingerprint:")
        self.dialogWindow.addstr(7, 1, self.clientFingerprint)

        # Add the exit message
        self.dialogWindow.addstr(9, 1, "Press any key to dismiss")

        # Disable the cursor
        curses.curs_set(0)

        self.dialogWindow.refresh()

        # Block the dialog until the user presses a button
        self.dialogWindow.getch()
        self.hide()
