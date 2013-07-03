import sys

from network.server import Server
from network.encSocket import EncSocket
from network import threads

from qAcceptDialog import QAcceptDialog
from qChatWindow import QChatWindow
from qModeDialog import QModeDialog
import qtUtils
from qWaitingDialog import QWaitingDialog

from PyQt4.QtCore import QTimer
from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QApplication
from PyQt4.QtGui import QInputDialog
from PyQt4.QtGui import QMessageBox
from PyQt4.QtGui import QPalette

from utils import constants
from utils.crypto import Crypto
from utils import exceptions
from utils import utils


class QtUI(QApplication):
    def __init__(self, argv, mode, port, host):
        QApplication.__init__(self, argv)

        self.mode = mode
        self.port = port
        self.host = host
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
            # If the user closed the mode dialog by not selected a mode,
            # stop the application
            if self.mode is None:
                self.stop()
                return

        # Show the chat window
        self.chatWindow = QChatWindow(None, None, self.isLightTheme)
        self.chatWindow.show()

        self.__loadOrGenerateKepair()

        if self.mode == constants.SERVER:
            self.__startServer()
            self.__waitForClient()
        elif self.mode == constants.CLIENT:
            # Get the host if not given
            if self.host is None:
                self.host, ok = QInputDialog.getText(self.chatWindow, "Hostname", "Host:")
                if not ok:
                    self.__restart()
                    return

            self.__connectToServer()

        self.exec_()


    def stop(self):
        print "Cleaning up..."
        self.__stopHelper()
        self.quit()


    def __restart(self):
        self.__stopHelper()
        self.start()


    def __stopHelper(self):
        # If a client is connected, try to end the connection gracefully
        if hasattr(self, 'sock') and self.sock.isConnected:
            self.sock.send("__END__")
            self.sock.disconnect()

        if hasattr(self, 'server') and self.server.isStarted:
            self.server.stop()

        if hasattr(self, 'acceptThread'):
            self.acceptThread.quit()
        elif hasattr(self, 'connectThread'):
            self.connectThread.quit()

        self.mode = None
        self.host = None
        self.closeAllWindows()


    def __loadOrGenerateKepair(self):
        self.crypto = Crypto()
        if utils.doesSavedKeypairExist():
            while(True):
                passphrase = qtUtils.getKeypairPassphrase(self.isLightTheme, self.__restart)
                try:
                    utils.loadKeypair(self.crypto, passphrase)
                    break
                except exceptions.CryptoError:
                    QMessageBox.warning(self.chatWindow, "Wrong passphrase", "An incorrect passphrase was entered")

            # We still need to generate an AES key
            self.crypto.generateAESKey()
        else:
            self.crypto.generateKeys()


    def __startServer(self):
        try:
            self.server = Server()
            self.server.start(int(self.port))
        except exceptions.NetworkError as ne:
            QMessageBox.critical(self.chatWindow, "Error starting server", "Error starting server: " + str(ne))


    def __waitForClient(self):
        # Start the accept thread
        self.acceptThread = threads.QtServerAcceptThread(self.server, self.crypto, self.__postAccept)
        self.acceptThread.start()

        # Show the waiting dialog
        self.waitingDialog = QWaitingDialog(self.chatWindow, "Waiting for connection...", self.isLightTheme, self.__userClosedWaitingDialog)
        self.waitingDialog.exec_()


    def __connectToServer(self):
        # Create the socket to use for the connection
        self.sock = EncSocket((self.host, self.port), crypto=self.crypto)

        # Start the connect thread
        self.connectThread = threads.QtServerConnectThread(self.sock, self.__postConnect, self.__connectFailure)
        self.connectThread.start()

        # Show the waiting dialog
        self.waitingDialog = QWaitingDialog(self.chatWindow, "Connecting to server...", self.isLightTheme, self.__userClosedWaitingDialog)
        self.waitingDialog.exec_()


    @pyqtSlot(EncSocket)
    def __postAccept(self, sock):
        self.connectedToClient = True
        self.sock = sock
        self.waitingDialog.close()

        # Show the accept dialog
        accept = QAcceptDialog.getAnswer(self.chatWindow, self.sock.getHostname())

        # If not accepted, disconnect and wait for a client again
        if not accept:
            self.sock.disconnect()
            self.__waitForClient()
            return

        # Do the handshake with the client
        try:
            utils.doServerHandshake(self.sock)
        except exceptions.NetworkError as ne:
            self.sock.disconnect()
            self.__waitForClient()

        self.__startChat()


    @pyqtSlot(EncSocket)
    def __postConnect(self):
        self.connectedToClient = True
        self.waitingDialog.close()
        self.__startChat()


    @pyqtSlot(str)
    def __connectFailure(self, errorMessage):
        QMessageBox.critical(self.chatWindow, "Error connecting to server", errorMessage)
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
        self.recvThread = threads.QtRecvThread(self.sock, self.chatWindow.appendMessage, self.__threadError)
        self.recvThread.start()
        self.sendThread = threads.QtSendThread(self.sock, self.__threadError)
        self.sendThread.start()

        self.chatWindow.sock = self.sock
        self.chatWindow.messageQueue = self.sendThread.messageQueue
        self.chatWindow.showNowChattingMessage()


    @pyqtSlot(str, str)
    def __threadError(self, title, message):
        QMessageBox.critical(self.chatWindow, title, message)
        self.__restart()

