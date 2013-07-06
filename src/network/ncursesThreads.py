import curses

from threading  import Thread
from threading  import Lock

from ncurses.cursesDialog import CursesDialog

from utils import constants
from utils import errors
from utils import exceptions
from utils import utils


mutex = Lock()


class CursesSendThread(Thread):
    def __init__(self, ncurses):
        self.ncurses = ncurses

        Thread.__init__(self)
        self.daemon = True


    def run(self):
        (height, width) = self.ncurses.chatWindow.getmaxyx()

        while True:
            chatInput = self.ncurses.textbox.edit(self.inputValidator)

            mutex.acquire()

            # Clear the chat input
            self.ncurses.textboxWindow.deleteln()
            self.ncurses.textboxWindow.move(0, 0)
            self.ncurses.textboxWindow.deleteln()

            # Add the new input to the chat window
            timestamp = utils.getTimestamp()
            self.ncurses.chatWindow.scroll(1)
            self.ncurses.chatWindow.addstr(height-1, 0, timestamp)
            self.ncurses.chatWindow.addstr(height-1, len(timestamp), chatInput[:-1], curses.color_pair(2))

            # Send the input to the client
            try:
                self.ncurses.client.sendMessage(constants.COMMAND_MSG, chatInput[:-1])
            except exceptions.NetworkError as ne:
                self.ncurses.client.disconnect()
                CursesDialog(self.ncurses.chatWindow, str(ne), errors.TITLE_NETWORK_ERROR, isError=True).show()

            # Move the cursor back to the chat input window
            self.ncurses.textboxWindow.move(0, 0)

            self.ncurses.chatWindow.refresh()
            self.ncurses.textboxWindow.refresh()

            mutex.release()


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
        return char


class CursesRecvThread(Thread):
    def __init__(self, ncurses):
        self.ncurses = ncurses

        Thread.__init__(self)
        self.daemon = True


    def run(self):
        (height, width) = self.ncurses.chatWindow.getmaxyx()

        while True:
            try:
                response = self.ncurses.client.receiveMessage(constants.COMMAND_MSG)
            except exceptions.ProtocolEnd:
                self.ncurses.client.disconnect()
                CursesDialog(self.ncurses.chatWindow, errors.CLIENT_ENDED_CONNECTION, errors.TITLE_END_CONNECTION, isError=True).show()
                return
            except (exceptions.NetworkError, exceptions.CryptoError) as e:
                self.handleNetworkError(e)

            mutex.acquire()

            # Put the received data in the chat window
            timestamp = utils.getTimestamp()
            self.ncurses.chatWindow.scroll(1)
            self.ncurses.chatWindow.addstr(height-1, 0, timestamp)
            self.ncurses.chatWindow.addstr(height-1, len(timestamp), response, curses.color_pair(3))

            # Move the cursor back to the chat input window
            self.ncurses.textboxWindow.move(0, 0)

            self.ncurses.chatWindow.refresh()
            self.ncurses.textboxWindow.refresh()

            mutex.release()


    def handleNetworkError(self, error):
        try:
            self.ncurses.client.disconnect()
        except Exception:
            pass
        finally:
            CursesDialog(self.ncurses.chatWindow, str(error), errors.TITLE_NETWORK_ERROR, isError=True).show()
