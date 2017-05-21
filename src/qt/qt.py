import sys
import time

from network.client import Client
from network.connectionManager import ConnectionManager
from network import qtThreads

from PyQt4.QtCore import pyqtSlot
from PyQt4.QtCore import QTimer
from PyQt4.QtGui import QApplication
from PyQt4.QtGui import QInputDialog
from PyQt4.QtGui import QMessageBox
from PyQt4.QtGui import QPalette
from PyQt4.QtGui import QWidget

from .qAcceptDialog import QAcceptDialog
from .qChatWindow import QChatWindow
from .qLoginWindow import QLoginWindow
from . import qtUtils
from .qWaitingDialog import QWaitingDialog

from utils import constants
from utils import errors
from utils import exceptions
from utils import utils


class QtUI(QApplication):
    def __init__(self, argv, nick, turn, port):
        QApplication.__init__(self, argv)

        self.nick = nick
        self.turn = turn
        self.port = port
        self.isEventLoopRunning = False

        qtUtils.setIsLightTheme(self.palette().color(QPalette.Window))

        self.aboutToQuit.connect(self.stop)


    def start(self):
        # Start a timer to allow for ctrl+c handling
        self.timer = QTimer()
        self.timer.start(500)
        self.timer.timeout.connect(lambda: None)

        # Show the login window and get the nick
        nick = QLoginWindow.getNick(QWidget(), self.nick)

        # If the nick is None, the user closed the window so we should quit the app
        if nick is None:
            qtUtils.exitApp()
        else:
            self.nick = str(nick)

        # Show the chat window
        self.chatWindow = QChatWindow(self.restart)
        self.chatWindow.show()

        self.__connectToServer()

        # Don't start the event loop again if it's already running
        if not self.isEventLoopRunning:
            self.isEventLoopRunning = True
            self.exec_()


    def stop(self):
        if hasattr(self, 'connectionManager'):
            self.connectionManager.disconnectFromServer()

        # Give the send thread time to get the disconnect messages out before exiting
        # and killing the thread
        time.sleep(.25)

        self.quit()


    def restart(self):
        if hasattr(self, 'connectionManager'):
            self.connectionManager.disconnectFromServer()

        self.closeAllWindows()
        if hasattr(self, 'chatWindow'):
            del self.chatWindow

        self.start()


    def __connectToServer(self):
        # Create the connection manager to manage all communcation to the server
        self.connectionManager = ConnectionManager(self.nick, (self.turn, self.port), self.chatWindow.postMessage, self.chatWindow.newClient, self.chatWindow.clientReady, self.chatWindow.smpRequest, self.chatWindow.handleError)
        self.chatWindow.connectionManager = self.connectionManager

        # Start the connect thread
        self.connectThread = qtThreads.QtServerConnectThread(self.connectionManager, self.__postConnect, self.__connectFailure)
        self.connectThread.start()

        # Show the waiting dialog
        self.waitingDialog = QWaitingDialog(self.chatWindow, "Connecting to server...")
        self.waitingDialog.show()


    @pyqtSlot()
    def __postConnect(self):
        self.waitingDialog.close()
        self.chatWindow.connectedToServer()


    @pyqtSlot(str)
    def __connectFailure(self, errorMessage):
        # Show a more friendly error if the connection was refused (errno 111)
        if errorMessage.contains('Errno 111'):
            errorMessage = "Unable to contact the server. Try again later."

        QMessageBox.critical(self.chatWindow, errors.FAILED_TO_CONNECT, errorMessage)
        self.restart()
