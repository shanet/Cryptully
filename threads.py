import os
import signal
import curses

import utils
import _exceptions
from threading import Thread, Lock

from cursesDialog import CursesDialog

mutex = Lock()


class CursesSendThread(Thread):
    def __init__(self, sock, screen, chatWindow, textboxWindow, textbox):
        self.sock          = sock
        self.screen        = screen
        self.chatWindow    = chatWindow
        self.textboxWindow = textboxWindow
        self.textbox       = textbox

        Thread.__init__(self)
        self.daemon = True


    def run(self):
        (height, width) = self.chatWindow.getmaxyx()

        while True:
            chatInput = self.textbox.edit(self.inputValidator)

            mutex.acquire()

            # Clear the chat input
            self.textboxWindow.deleteln()
            self.textboxWindow.move(0, 0)
            self.textboxWindow.deleteln()

            # Add the new input to the chat window
            self.chatWindow.scroll(1)
            self.chatWindow.addstr(height-1, 0, chatInput[:-1], curses.color_pair(2))

            # Send the input to the client
            try:
                self.sock.send(chatInput[:-1])
            except _exceptions.NetworkError as ne:
                self.sock.disconnect()
                CursesDialog(self.chatWindow, str(ne), "Network Error", isError=True).show()

            # Move the cursor back to the chat input window
            self.textboxWindow.move(0, 0)

            self.chatWindow.refresh()
            self.textboxWindow.refresh()

            mutex.release()


    def inputValidator(self, char):
        if char == 21: # Ctrl+U
            utils.showOptionsMenuWindow(self.screen, self.sock.crypto)
            return 0
        elif char == curses.KEY_HOME:
            return curses.ascii.SOH
        elif char == curses.KEY_END:
            return curses.ascii.ENQ
        elif char == curses.KEY_ENTER or char == ord('\n'):
             return curses.ascii.BEL
        return char


class CursesRecvThread(Thread):
    def __init__(self, sock, screen, chatWindow, textboxWindow):
        self.sock          = sock
        self.screen        = screen
        self.chatWindow    = chatWindow
        self.textboxWindow = textboxWindow

        Thread.__init__(self)
        self.daemon = True


    def run(self):
        (height, width) = self.chatWindow.getmaxyx()

        while True:
            try:
                response = self.sock.recv()
            except _exceptions.NetworkError as ne:
                self.sock.disconnect()
                CursesDialog(self.chatWindow, str(ne), "Network Error", isError=True).show()

            mutex.acquire()

            # Check if the client requested to end the connection
            if response == "__END__":
                self.sock.disconnect()
                CursesDialog(self.chatWindow, "Connection Terminated", "The client requested to end the connection", isError=True).show()

            # Put the received data in the chat window
            self.chatWindow.scroll(1)
            self.chatWindow.addstr(height-1, 0, response, curses.color_pair(3))

            # Move the cursor back to the chat input window
            self.textboxWindow.move(0, 0)

            self.chatWindow.refresh()
            self.textboxWindow.refresh()

            mutex.release()
