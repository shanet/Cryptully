from encSocket import EncSocket

from utils import constants
from utils import errors
from utils import exceptions

class Client(object):
    def __init__(self, mode, clientAddr, clientSock=None, crypto=None, disconnectOnError=False):
        self.mode = mode
        self.sock = EncSocket(clientAddr, clientSock, crypto)
        self.disconnectOnError = disconnectOnError


    def sendMessage(self, command, payload=''):
        self.sock.send(command + constants.COMMAND_SEPARATOR + payload)


    def receiveMessage(self, expectedCommand=None):
        (command, payload) = self.parseMessage(self.sock.recv())

        if command == constants.COMMAND_END:
            raise exceptions.ProtocolEnd()

        if expectedCommand is not None or not self._isValidCommand(command):
            if command != expectedCommand:
                sock.send(constructMessage(constants.COMMAND_ERR))
                if self.disconnectOnError:
                    sock.disconnect()
                raise exceptions.protocolError(errors.UNEXPECTED_COMMAND)

            return payload

        return (command, payload)


    def parseMessage(self, message):
        # Separate the command from the payload
        separatorIndex = message.find(constants.COMMAND_SEPARATOR)
        if separatorIndex == -1:
            raise exceptions.ProtocolError(errors.NO_COMMAND_SEPARATOR)

        command = message[:separatorIndex]
        payload = message[separatorIndex+1:]

        return command, payload


    def connect(self):
        self.sock.connect()


    def disconnect(self):
        if self.sock.isConnected:
            try:
                self.sendMessage(constants.COMMAND_END)
            except Exception:
                pass
        self.sock.disconnect()


    def getHostname(self):
        return self.sock.getHostname()


    def doHandshake(self):
        if self.mode == constants.MODE_SERVER:
            self.__doHandshakeAsServer()
        else:
            self.__doHandshakeAsClient()


    def __doHandshakeAsServer(self):
        # Fail if there are any protocol errors during the handshake
        self.disconnectOnError = True

        try:
            # Receive the hello command
            self.receiveMessage(constants.COMMAND_HELO)

            # Send the ready command
            self.sendMessage(constants.COMMAND_REDY)

            # Receive the client's public key
            clientPublicKey = self.receiveMessage(constants.COMMAND_PUBLIC_KEY)
            self.sock.crypto.setRemotePubKey(clientPublicKey)

            # Send the server's public key
            serverPublicKey = self.sock.crypto.getLocalPubKeyAsString()
            self.sendMessage(constants.COMMAND_PUBLIC_KEY, serverPublicKey)

            # Switch to RSA encryption to exchange the AES key, IV, and salt
            self.sock.setEncryptionType(self.sock.RSA)

            # Send the AES key, IV, and salt
            self.sendMessage(constants.COMMAND_AES_KEY, self.sock.crypto.aesKey)
            self.sendMessage(constants.COMMAND_AES_IV, self.sock.crypto.aesIv)
            self.sendMessage(constants.COMMAND_AES_SALT, self.sock.crypto.aesSalt)

            # Switch to AES encryption for the remainder of the connection
            self.sock.setEncryptionType(self.sock.AES)
        except exceptions.ProtocolEnd:
            self.isConnected = False
            self.disconnect()

        # No longer fail on fail on protocol error
        self.disconnectOnError = False


    def __doHandshakeAsClient(self):
        # Fail if there are any protocol errors during the handshake
        self.disconnectOnError = True

        try:
            # Send the hello command
            self.sendMessage(constants.COMMAND_HELO)

            # Receive the redy command
            self.receiveMessage(constants.COMMAND_REDY)

            # Send the client's public key
            clientPublicKey = self.sock.crypto.getLocalPubKeyAsString()
            self.sendMessage(constants.COMMAND_PUBLIC_KEY, clientPublicKey)

            # Receive the server's public key
            serverPublicKey = self.receiveMessage(constants.COMMAND_PUBLIC_KEY)
            self.sock.crypto.setRemotePubKey(serverPublicKey)

            # Switch to RSA encryption to receive the AES key, IV, and salt
            self.sock.setEncryptionType(self.sock.RSA)

            # Receive the AES key
            self.sock.crypto.aesKey = self.receiveMessage(constants.COMMAND_AES_KEY)

            # Receive the AES IV
            self.sock.crypto.aesIv = self.receiveMessage(constants.COMMAND_AES_IV)

            # Receive the AES salt
            self.sock.crypto.aesSalt = self.receiveMessage(constants.COMMAND_AES_SALT)

            # Switch to AES encryption for the remainder of the connection
            self.sock.setEncryptionType(self.sock.AES)
        except exceptions.ProtocolEnd:
            self.isConnected = False
            self.disconnect()

        # No longer fail on fail on protocol error
        self.disconnectOnError = False


    def _isValidCommand(self, command):
        return (command in constants.COMMANDS)
