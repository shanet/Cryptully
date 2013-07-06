import httplib
import json
import Queue
import signal
import socket

from network.client import Client

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


class QtRecvThread(QThread):
    recvSignal = pyqtSignal(str, int, bool)
    errorSignal = pyqtSignal(str, str)

    def __init__(self, client, recvSlot, errorSlot):
        QThread.__init__(self)

        self.client = client
        self.recvSignal.connect(recvSlot)
        self.errorSignal.connect(errorSlot)


    def run(self):
        while True:
            try:
                message = self.client.receiveMessage(constants.COMMAND_MSG)

                # Send the message to the given callback
                self.recvSignal.emit(message, constants.RECEIVER, True)
            except exceptions.ProtocolEnd:
                self.errorSignal.emit(errors.TITLE_END_CONNECTION, errors.CLIENT_ENDED_CONNECTION)
                return
            except (exceptions.NetworkError, exceptions.CryptoError) as e:
                self.errorSignal.emit(errors.TITLE_NETWORK_ERROR, str(e))
                return


class QtSendThread(QThread):
    errorSignal = pyqtSignal(str, str)

    def __init__(self, client, errorSlot):
        QThread.__init__(self)

        self.client = client
        self.errorSignal.connect(errorSlot)
        self.messageQueue = Queue.Queue()


    def run(self):
        while True:
            # Get (or wait) for a message in the message queue
            message = self.messageQueue.get()

            try:
                self.client.sendMessage(constants.COMMAND_MSG, message)
            except (exceptions.NetworkError, exceptions.CryptoError) as e:
                self.errorSignal.emit(errors.TITLE_NETWORK_ERROR, str(e))
                return
            finally:
                # Mark the operation as done
                self.messageQueue.task_done()


class QtServerAcceptThread(QThread):
    successSignal = pyqtSignal(Client)
    failureSignal = pyqtSignal(str)

    def __init__(self, server, crypto, successSlot, failureSlot):
        QThread.__init__(self)

        self.server = server
        self.crypto = crypto
        self.successSignal.connect(successSlot)
        self.failureSignal.connect(failureSlot)


    def run(self):
        try:
            client = self.server.accept(self.crypto)
            self.successSignal.emit(client)
        except socket.error as se:
            self.server.disconnect()
            self.failureSignal.emit(str(se))


class QtServerConnectThread(QThread):
    successSignal = pyqtSignal()
    failureSignal = pyqtSignal(str)

    def __init__(self, client, successSlot, failureSlot):
        QThread.__init__(self)

        self.client = client
        self.successSignal.connect(successSlot)
        self.failureSignal.connect(failureSlot)


    def run(self):
        try:
            self.client.connect()

            # Do the handshake with the server
            self.client.doHandshake()

            self.successSignal.emit()
        except exceptions.GenericError as ge:
            self.onFailure(str(ge))
        except exceptions.NetworkError as ne:
            self.onFailure(str(ne))


    def onFailure(self, errorMessage):
        self.client.disconnect()
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
