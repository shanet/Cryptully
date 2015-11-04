import curses

class CursesDialog:
    def __init__(self, screen, message, title="", isError=False, isFatal=False, isBlocking=False):
        self.screen  = screen
        self.title   = title
        self.message = message

        self.isError    = isError
        self.isFatal    = isFatal
        self.isBlocking = isBlocking

        if curses.has_colors():
            curses.init_pair(6, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.init_pair(7, curses.COLOR_RED, curses.COLOR_BLACK)


    def show(self):
        (height, width) = self.screen.getmaxyx()

        if self.isFatal:
            exitMessage = "Press enter to exit"
        elif self.isError:
            exitMessage = "Press enter to continue"
        elif self.isBlocking:
            exitMessage = "Press any key to continue"
        else:
            exitMessage = ""

        # Determine the max width of the dialog window
        dialogWidth = max(len(self.title), len(self.message), len(exitMessage)) + 2

        if self.title:
            dialogHeight = 7
        elif self.isError or self.isBlocking:
            dialogHeight = 5
        else:
            dialogHeight = 3

        self.dialogWindow = self.screen.subwin(dialogHeight, dialogWidth, height/2 - int(dialogHeight/2), width/2 - int(dialogWidth/2))
        self.dialogWindow.clear()
        self.dialogWindow.border(0)

        # Add the title if provided
        if self.title:
            self.dialogWindow.addstr(1, 1, self.title, curses.color_pair(7) if self.isError else curses.color_pair(6))
            self.dialogWindow.hline(2, 1, 0, dialogWidth-2)

        # Add the message
        if self.message:
            verticalPos = 3 if self.title else 1
            self.dialogWindow.addstr(verticalPos, 1, self.message)

            # Add the exit message if the dialog is an error dialog or is blocking
            if self.isError or self.isBlocking:
                if self.title:
                    verticalPos = 5
                else:
                    verticalPos = 3
                self.dialogWindow.addstr(verticalPos, 1, exitMessage)

        # Disable the cursor
        curses.curs_set(0)

        self.dialogWindow.refresh()

        if self.isBlocking:
            self.dialogWindow.getch()
            self.hide()


    def hide(self):
        curses.curs_set(2)
        self.dialogWindow.clear()
        self.dialogWindow.refresh()
