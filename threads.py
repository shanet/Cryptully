import os
import signal
import curses

import utils
import _exceptions
from threading import Thread, Lock

from cursesDialog import CursesDialog

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
            self.ncurses.chatWindow.scroll(1)
            self.ncurses.chatWindow.addstr(height-1, 0, chatInput[:-1], curses.color_pair(2))

            # Send the input to the client
            try:
                self.ncurses.sock.send(chatInput[:-1])
            except _exceptions.NetworkError as ne:
                self.ncurses.sock.disconnect()
                CursesDialog(self.ncurses.chatWindow, str(ne), "Network Error", isError=True).show()

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
                response = self.ncurses.sock.recv()
            except _exceptions.NetworkError as ne:
                self.ncurses.sock.disconnect()
                CursesDialog(self.ncurses.chatWindow, str(ne), "Network Error", isError=True).show()

            mutex.acquire()

            # Check if the client requested to end the connection
            if response == "__END__":
                self.ncurses.sock.disconnect()
                CursesDialog(self.ncurses.chatWindow, "Connection Terminated", "The client requested to end the connection", isError=True).show()

            # Put the received data in the chat window
            self.ncurses.chatWindow.scroll(1)
            self.ncurses.chatWindow.addstr(height-1, 0, response, curses.color_pair(3))

            # Move the cursor back to the chat input window
            self.ncurses.textboxWindow.move(0, 0)

            self.ncurses.chatWindow.refresh()
            self.ncurses.textboxWindow.refresh()

            mutex.release()
