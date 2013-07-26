import time
import sys

from sock import Socket

from utils import constants
from utils import errors
from utils import exceptions
from utils.crypto import Crypto


class EncSocket(object):
    RSA = 0
    AES = 1

    def __init__(self, addr, sock=None, crypto=None):
        self.sock = Socket(addr, sock)
        self.isEncrypted = False
        self.encryptType = None

        # Create a crypto object if one was not given
        if crypto is None:
            self.crypto = Crypto()
            self.crypto.generateKeys()
        else:
            self.crypto = crypto


    def connect(self):
        self.sock.connect()


    def disconnect(self):
        self.sock.disconnect()


    def send(self, serverData, data):
        if type(data) is not str:
            raise TypeError()

        # Encrypt all outgoing data
        if self.encryptType is not None:
            if self.encryptType == self.RSA:
                data = self.crypto.rsaEncrypt(data)
            elif self.encryptType == self.AES:
                data = self.crypto.aesEncrypt(data)
            else:
                raise exceptions.ServerError(errors.UNKNOWN_ENCRYPTION_TYPE)

        self.sock.send(serverData + constants.COMMAND_SEPARATOR + data)


    def recv(self):
        data = self.sock.recv()

        # Decrypt the incoming data
        if self.encryptType is not None:
            if self.encryptType == self.RSA:
                data = self.crypto.rsaDecrypt(data)
            elif self.encryptType == self.AES:
                data = self.crypto.aesDecrypt(data)
            else:
                raise exceptions.ServerError(errors.UNKNOWN_ENCRYPTION_TYPE)

        return data


    def getHostname(self):
        return self.sock.addr[0]
