import time
import socket
import sys

from utils.crypto import Crypto
from utils import exceptions
from utils import utils


class EncSocket(object):
    RSA = 0
    AES = 1

    def __init__(self, addr, sock=None, crypto=None):
        self.addr        = addr
        self.isEncrypted = False
        self.encryptType = None

        # Create a new socket if one was not given
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.isConnected = False
        else:
            self.sock = sock
            self.isConnected = True

        # Create a crypto object if one was not given
        if crypto is None:
            self.crypto = Crypto()
            self.crypto.generateKeys()
        else:
            self.crypto = crypto


    def setEncryptionType(self, type=None):
        self.encryptType = type


    def connect(self):
        try:
            self.sock.connect(self.addr)
            self.isConnected = True
        except socket.error as se:
            raise exceptions.GenericError(str(se))


    def disconnect(self):
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()
        except socket.error:
            pass
        finally:
            self.isConnected = False


    def send(self, data):
        if type(data) is not str:
            raise TypeError()

        # Encrypt all outgoing data
        if self.encryptType is not None:
            if self.encryptType == self.RSA:
                data = self.crypto.rsaEncrypt(data)
            elif self.encryptType == self.AES:
                data = self.crypto.aesEncrypt(data)
            else:
                raise exceptions.ServerError("Unknown encryption type.")

        # Add a newline to all outgoing data so that any line buffers are flushed
        data += '\n'
        dataLength = len(data)

        # Send the length of the message (int converted to network byte order and padded to 32 bytes)
        self._send(str('%32s' % socket.htonl(dataLength)), 32)

        # Send the actual data
        self._send(data, dataLength)


    def _send(self, data, length):
        sentLen = 0
        while sentLen < length:
            amountSent = self.sock.send(data[sentLen:])

            if amountSent == 0:
                raise exceptions.NetworkError("Remote unexpectedly closed connection")

            sentLen += amountSent


    def recv(self):
        # Receive the length of the incoming message
        try:
            dataLength = socket.ntohl(int(self._recv(32)))
        except ValueError:
            raise exceptions.NetworkError("Remote sent unexpected data")

        # Receive the actual data
        data = self._recv(dataLength)

        # Remove the newline at the end of the data
        data = data[:-1]

        # Decrypt the incoming data
        if self.encryptType is not None:
            if self.encryptType == self.RSA:
                data = self.crypto.rsaDecrypt(data)
            elif self.encryptType == self.AES:
                data = self.crypto.aesDecrypt(data)
            else:
                raise exceptions.ServerError("Unknown encryption type.")

        return data


    def _recv(self, length):
        try:
            data = ''
            recvLen = 0
            while recvLen < length:
                newData = self.sock.recv(length-recvLen)

                if newData == '':
                    raise exceptions.NetworkError("Remote unexpectedly closed connection")

                data = data + newData
                recvLen += len(newData)

            return data
        except socket.error as se:
            raise exceptions.NetworkError(str(se))


    def getHostname(self):
        return self.addr[0]
