import sys

from network.client import Client
from network.server import Server
from network import qtThreads

from qAcceptDialog import QAcceptDialog
from qChatWindow import QChatWindow
from qModeDialog import QModeDialog
import qtUtils
from qWaitingDialog import QWaitingDialog

from PyQt4.QtCore import pyqtSlot
from PyQt4.QtCore import QTimer
from PyQt4.QtGui import QApplication
from PyQt4.QtGui import QInputDialog
from PyQt4.QtGui import QMessageBox
from PyQt4.QtGui import QPalette

from utils import constants
from utils import errors
from utils import exceptions
from utils import utils
from utils.crypto import Crypto


class QtUI(QApplication):
    def __init__(self, argv, mode, port, host):
        QApplication.__init__(self, argv)

        self.mode = mode
        self.port = port
        self.host = host
        self.isEventLoopRunning = False
        self.connectedToClient = False
        self.isLightTheme = qtUtils.isLightTheme(self.palette().color(QPalette.Window))

        self.aboutToQuit.connect(self.stop)


    def start(self):
        self.timer = QTimer()
        self.timer.start(500)
        self.timer.timeout.connect(lambda: None)

        # Show mode dialog if a mode wasn't given
        if self.mode is None:
            self.mode = QModeDialog.getMode(self.isLightTheme)
            # If the user closed the mode dialog by not selected a mode, stop the app
            if self.mode is None:
                qtUtils.exitApp()

        # Show the chat window
        self.chatWindow = QChatWindow(None, None, self.isLightTheme)
        self.chatWindow.show()

        self.__loadOrGenerateKepair()

        if self.mode == constants.MODE_SERVER:
            self.__startServer()
            self.__waitForClient()
        elif self.mode == constants.MODE_CLIENT:
            # Get the host if not given
            if self.host is None:
                self.host, ok = QInputDialog.getText(self.chatWindow, "Hostname", "Host:")
                if not ok:
                    self.__restart()
                    return

            self.__connectToServer()

        if not self.isEventLoopRunning:
            self.exec_()
            self.isEventLoopRunning = True


    def stop(self):
        self.__endConnections()
        self.quit()


    def __restart(self):
        self.__endConnections()
        self.__restartHelper()
        self.start()


    def __endConnections(self):
        if hasattr(self, 'acceptThread'):
            self.acceptThread.quit()
        elif hasattr(self, 'connectThread'):
            self.connectThread.quit()

        if hasattr(self, 'sendThread'):
            self.sendThread.quit()

        if hasattr(self, 'recvThread'):
            self.recvThread.quit()

        # If a client is connected, try to end the connection gracefully
        if hasattr(self, 'client'):
            self.client.disconnect()

        if hasattr(self, 'server'):
            self.server.stop()


    def __restartHelper(self):
        self.mode = None
        self.host = None

        self.closeAllWindows()

        if hasattr(self, 'waitingDialog'):
            del self.waitingDialog

        if hasattr(self, 'chatWindow'):
            del self.chatWindow


    def __loadOrGenerateKepair(self):
        self.crypto = Crypto()
        if utils.doesSavedKeypairExist():
            while(True):
                passphrase = qtUtils.getKeypairPassphrase(self.isLightTheme, self.__restart)
                try:
                    utils.loadKeypair(self.crypto, passphrase)
                    break
                except exceptions.CryptoError:
                    QMessageBox.warning(self.chatWindow, errors.BAD_PASSPHRASE, errors.BAD_PASSPHRASE_VERBOSE)

            # We still need to generate an AES key
            self.crypto.generateAESKey()
        else:
            self.crypto.generateKeys()


    def __startServer(self):
        try:
            self.server = Server()
            self.server.start(int(self.port))
        except exceptions.NetworkError as ne:
            QMessageBox.critical(self.chatWindow, errors.FAILED_TO_START_SERVER, errors.FAILED_TO_START_SERVER + ": " + str(ne))


    def __waitForClient(self):
        # Start the accept thread
        self.acceptThread = qtThreads.QtServerAcceptThread(self.server, self.crypto, self.__postAccept)
        self.acceptThread.start()

        # Show the waiting dialog
        self.waitingDialog = QWaitingDialog(self.chatWindow, "Waiting for connection...", self.isLightTheme, self.__userClosedWaitingDialog, showIP=True)
        self.waitingDialog.exec_()


    def __connectToServer(self):
        # Create the client object to use for the connection
        self.client = Client(constants.MODE_CLIENT, (self.host, self.port), crypto=self.crypto)

        # Start the connect thread
        self.connectThread = qtThreads.QtServerConnectThread(self.client, self.__postConnect, self.__connectFailure)
        self.connectThread.start()

        # Show the waiting dialog
        self.waitingDialog = QWaitingDialog(self.chatWindow, "Connecting to server...", self.isLightTheme, self.__userClosedWaitingDialog)
        self.waitingDialog.exec_()


    @pyqtSlot(Client)
    def __postAccept(self, client):
        self.connectedToClient = True
        self.client = client
        self.waitingDialog.close()

        # Show the accept dialog
        accept = QAcceptDialog.getAnswer(self.chatWindow, self.client.getHostname())

        # If not accepted, disconnect and wait for a client again
        if not accept:
            self.client.disconnect()
            self.__waitForClient()
            return

        # Do the handshake with the client
        try:
            client.doHandshake()
        except exceptions.NetworkError as ne:
            self.client.disconnect()
            self.__waitForClient()

        self.__startChat()


    @pyqtSlot()
    def __postConnect(self):
        self.connectedToClient = True
        self.waitingDialog.close()
        self.__startChat()


    @pyqtSlot(str)
    def __connectFailure(self, errorMessage):
        QMessageBox.critical(self.chatWindow, errors.FAILED_TO_CONNECT, errorMessage)
        self.__restart()


    @pyqtSlot()
    def __userClosedWaitingDialog(self):
        self.waitingDialog.hide()
        # If the waiting dialog was closed before we connected to the client,
        # it means that the user closed the dialog and we should restart the app
        if not self.connectedToClient:
            self.__restart()


    def __startChat(self):
        # Start the sending and receiving thread
        self.recvThread = qtThreads.QtRecvThread(self.client, self.chatWindow.appendMessage, self.__threadError)
        self.recvThread.start()
        self.sendThread = qtThreads.QtSendThread(self.client, self.__threadError)
        self.sendThread.start()

        self.chatWindow.client = self.client
        self.chatWindow.messageQueue = self.sendThread.messageQueue
        self.chatWindow.showNowChattingMessage()


    @pyqtSlot(str, str)
    def __threadError(self, title, message):
        QMessageBox.critical(self.chatWindow, title, message)
        self.__restart()

