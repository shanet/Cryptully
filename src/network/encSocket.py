import sys
import time
import socket

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
        length = len(data)

        # Send the data until the proper number of bytes sent is reached
        sentLen = 0
        while sentLen < length:
            amountSent = self.sock.send(data[sentLen:])

            if amountSent == 0:
                raise exceptions.NetworkError("Remote unexpectedly closed connection")

            sentLen += amountSent

        # Sleep for 10ms to ensure that the system has time to send the data
        # in the case of this function being called in rapid succession
        time.sleep(.05)


    def recv(self):
        try:
            # Recieve the actual data
            data = self.sock.recv(4096)

            if data == '':
                raise exceptions.NetworkError("Remote unexpectedly closed connection")

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
        except socket.error as se:
            raise exceptions.NetworkError(str(se))


    def getHostname(self):
        return self.addr[0]
