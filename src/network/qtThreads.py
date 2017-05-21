from .client import Client

from PyQt4.QtCore import QThread
from PyQt4.QtCore import pyqtSignal

from utils import exceptions


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
