import curses
import httplib
import json
import os
import Queue
import signal
import socket

from PyQt4.QtCore import QCoreApplication
from PyQt4.QtCore import QThread
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QMessageBox
from PyQt4.QtGui import QWidget

from threading  import Thread
from threading  import Lock

from encSocket import EncSocket

from ncurses.cursesDialog import CursesDialog

from qt import qtUtils

from utils import constants
from utils import exceptions
from utils import utils


mutex = Lock()


class QtRecvThread(QThread):
    errorSignal = pyqtSignal(str, str)

    def __init__(self, sock, recvCallback, errorSlot):
        QThread.__init__(self)

        self.recvCallback = recvCallback
        self.errorSignal.connect(errorSlot)
        self.sock = sock


    def run(self):
        while True:
            try:
                message = self.sock.recv()

                # Check if the client requested to end the connection
                if message == "__END__":
                    self.sock.disconnect()
                    self.errorSignal.emit("Connection Ended", "The client requested to end the connection")
                    return

                # Send the message to the given callback
                self.recvCallback(message, constants.RECEIVER)
            except exceptions.NetworkError as ne:
                self.sock.disconnect()
                self.errorSignal.emit("Network Error", str(ne))
                return


class QtSendThread(QThread):
    errorSignal = pyqtSignal(str, str)

    def __init__(self, sock, errorSlot):
        QThread.__init__(self)

        self.sock = sock
        self.errorSignal.connect(errorSlot)
        self.messageQueue = Queue.Queue()


    def run(self):
        while True:
            # Get (or wait) for a message in the message queue
            message = self.messageQueue.get()

            try:
                self.sock.send(message)
            except exceptions.NetworkError as ne:
                self.sock.disconnect()
                self.errorSignal.emit("NetworkError", str(ne))
                return
            finally:
                # Mark the operation as done
                self.messageQueue.task_done()


class QtServerAcceptThread(QThread):
    successSignal = pyqtSignal(EncSocket)

    def __init__(self, server, crypto, successSlot):
        QThread.__init__(self)

        self.server = server
        self.crypto = crypto
        self.successSignal.connect(successSlot)


    def run(self):
        try:
            sock = self.server.accept(self.crypto)
            self.successSignal.emit(sock)
        except socket.error:
            pass


class QtServerConnectThread(QThread):
    successSignal = pyqtSignal()
    failureSignal = pyqtSignal(str)

    def __init__(self, sock, successSlot, failureSlot):
        QThread.__init__(self)

        self.sock = sock
        self.successSignal.connect(successSlot)
        self.failureSignal.connect(failureSlot)


    def run(self):
        try:
            self.sock.connect()

            # Do the handshake with the server
            utils.doClientHandshake(self.sock)

            self.successSignal.emit()
        except exceptions.GenericError as ge:
            self.onFailure(str(ge))
        except exceptions.NetworkError as ne:
            self.onFailure(str(ne))


    def onFailure(self, errorMessage):
        self.sock.disconnect()
        self.failureSignal.emit(errorMessage)


class GetIPAddressThread(QThread):
    successSignal = pyqtSignal(str)
    failureSignal = pyqtSignal(str)

    def __init__(self, successSlot, failureSlot):
        QThread.__init__(self)

        self.successSignal.connect(successSlot)
        self.failureSignal.connect(failureSlot)


    def run(self):
        try:
            httpConnection = httplib.HTTPConnection("jsonip.com")
            httpConnection.request("GET", "/index.html")
            response = httpConnection.getresponse()
            if response.status == 200:
                data = response.read()[11:-1]
                jsonData = json.loads(data)
                self.successSignal.emit(jsonData["ip"])
            else:
                self.failureSignal.emit("Bad HTTP status: " + str(response.status))
            httpConnection.close()
        except Exception as e:
            self.failureSignal.emit(e)


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
                self.ncurses.sock.send(chatInput[:-1])
            except exceptions.NetworkError as ne:
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
            except exceptions.NetworkError as ne:
                self.networkError(ne)
            except exceptions.CryptoError as ce:
                self.networkError(ne)

            mutex.acquire()

            # Check if the client requested to end the connection
            if response == "__END__":
                self.ncurses.sock.disconnect()
                CursesDialog(self.ncurses.chatWindow, "Connection Terminated", "The client requested to end the connection", isError=True).show()

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


    def networkError(self, error):
        self.ncurses.sock.disconnect()
        CursesDialog(self.ncurses.chatWindow, str(error), "Network Error", isError=True).show()
