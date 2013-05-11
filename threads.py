import sys
import curses
from threading import Thread

import utils


class CursesSendThread(Thread):
    def __init__(self, client, chatWindow, textboxWindow, textbox):
        self.client        = client
        self.chatWindow    = chatWindow
        self.textboxWindow = textboxWindow
        self.textbox       = textbox

        Thread.__init__(self)


    def run(self):
        (height, width) = self.chatWindow.getmaxyx()

        while True:
            self.chatWindow.refresh()
            chatInput = self.textbox.edit(utils.inputValidator)

            # Clear the chat input
            self.textboxWindow.deleteln()
            self.textboxWindow.move(0, 0)
            self.textboxWindow.deleteln()

            # Add the new input to the chat window
            self.chatWindow.scroll(1)
            self.chatWindow.addstr(height-1, 0, chatInput[:-1], curses.color_pair(2))

            # Send the input to the client
            utils.send(self.client, chatInput[:-1])

    
class CursesRecvThread(Thread):
    def __init__(self, client, chatWindow, textboxWindow):
        self.client        = client
        self.chatWindow    = chatWindow
        self.textboxWindow = textboxWindow
        Thread.__init__(self)


    def run(self):
        (height, width) = self.chatWindow.getmaxyx()

        while True:
            self.chatWindow.refresh()
            self.textboxWindow.refresh()

            # Put the received data in the chat window
            response = utils.recv(self.client)
            self.chatWindow.scroll(1)
            self.chatWindow.addstr(height-1, 0, response, curses.color_pair(3))

            # Move the cursor back to the chat input window
            self.textboxWindow.move(0, 0)


class SendThread(Thread):
    def __init__(self, client):
        self.client = client
        Thread.__init__(self)


    def run(self):
        while(1):
            sys.stdout.write(">>> ")
            utils.send(self.client, raw_input())

    
class RecvThread(Thread):
    def __init__(self, client):
        self.client = client
        Thread.__init__(self)


    def run(self):
        while(1):
            print "Response: " + utils.recv(self.client)

