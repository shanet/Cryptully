import curses

import utils
import _exceptions
from threading import Thread, Lock


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
            mutex.acquire()
            self.chatWindow.refresh()
            self.textboxWindow.refresh()
            mutex.release()

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
                utils.showDialog(self.chatWindow, "Network Error", str(ne), True)
                
            # Move the cursor back to the chat input window
            self.textboxWindow.move(0, 0)
            
            mutex.release()


    def inputValidator(self, char):
        if char == curses.KEY_HOME:
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
            mutex.acquire()
            self.chatWindow.refresh()
            self.textboxWindow.refresh()
            mutex.release()

            try:
                response = self.sock.recv()
            except _exceptions.NetworkError as ne:
                self.sock.disconnect()
                utils.showDialog(self.chatWindow, "Network Error", str(ne), True)

            # Check if the client requested to end the connection
            if response == "__END__":
                self.sock.disconnect()
                utils.showDialog(self.chatWindow, "Connection Terminated", "The client requested to end the connection", True)

            # Put the received data in the chat window
            mutex.acquire()
            self.chatWindow.scroll(1)
            self.chatWindow.addstr(height-1, 0, response, curses.color_pair(3))

            # Move the cursor back to the chat input window
            self.textboxWindow.move(0, 0)

            mutex.release()
