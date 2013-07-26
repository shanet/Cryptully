import Queue
import signal
import socket

from client import Client

from PyQt4.QtCore import QCoreApplication
from PyQt4.QtCore import QThread
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QMessageBox
from PyQt4.QtGui import QWidget

from qt import qtUtils

from utils import constants
from utils import errors
from utils import exceptions
from utils import utils


class QtServerAcceptThread(QThread):
    successSignal = pyqtSignal(Client)

    def __init__(self, server, crypto, successSlot):
        QThread.__init__(self)

        self.server = server
        self.crypto = crypto
        self.successSignal.connect(successSlot)


    def run(self):
        try:
            client = self.server.accept(self.crypto)
            self.successSignal.emit(client)
        except socket.error as se:
            self.server.stop()


class QtServerConnectThread(QThread):
    successSignal = pyqtSignal()
    failureSignal = pyqtSignal(str)

    def __init__(self, connectionManager, successSlot, failureSlot):
        QThread.__init__(self)

        self.connectionManager = connectionManager
        self.successSignal.connect(successSlot)
        self.failureSignal.connect(failureSlot)


    def run(self):
        try:
            self.connectionManager.connectToServer()
            self.successSignal.emit()
        except exceptions.GenericError as ge:
            self.failureSignal.emit(str(ge))
        except exceptions.NetworkError as ne:
            self.failureSignal.emit(str(ne))
