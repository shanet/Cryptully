import curses
import threading

from utils import utils


class CursesSendThread(threading.Thread):
    def __init__(self, ncurses):
        threading.Thread.__init__(self)
        self.daemon = True

        self.ncurses = ncurses
        self.stop = threading.Event()
        self.smpRequested = threading.Event()


    def run(self):
        (height, width) = self.ncurses.chatWindow.getmaxyx()
        self.ncurses.textboxWindow.move(0, 0)

        while True:
            message = self.ncurses.textbox.edit(self.inputValidator)[:-1]
            self.ncurses.screen.refresh()

            # Don't send anything if we're not connected to a nick
            if self.ncurses.connectedNick is None:
                self.ncurses.appendMessage('', "Not connected to client", curses.color_pair(0))

            # Stop the thread if the stop flag is set
            if self.stop.is_set():
                self.ncurses.dialogDismissed.acquire()
                self.ncurses.dialogDismissed.notify()
                self.ncurses.dialogDismissed.release()
                return

            # If requesting an SMP answer, set the given message as the answer
            if self.smpRequested.is_set():
                self.ncurses.setSmpAnswer(message)
                self.smpRequested.clear()
            else:
                self.__addMessageToChat(message)
                self.__sendMessageToClient(message)

            self.__clearChatInput()


    def inputValidator(self, char):
        if char == 21: # Ctrl+U
            self.ncurses.showOptionsMenuWindow()
            return 0
        elif char == curses.KEY_HOME:
            return curses.ascii.SOH
        elif char == curses.KEY_END:
            return curses.ascii.ENQ
        elif char == curses.KEY_ENTER or char == ord('\n'):
            return curses.ascii.BEL
        else:
            return char


    def __clearChatInput(self):
        self.ncurses.textboxWindow.deleteln()
        self.ncurses.textboxWindow.move(0, 0)
        self.ncurses.textboxWindow.deleteln()


    def __addMessageToChat(self, message):
        prefix = "(%s) %s: " % (utils.getTimestamp(), self.ncurses.nick)
        self.ncurses.appendMessage(prefix, message, curses.color_pair(3))


    def __sendMessageToClient(self, message):
        self.ncurses.connectionManager.getClient(self.ncurses.connectedNick).sendChatMessage(message)
