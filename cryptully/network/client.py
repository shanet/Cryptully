import base64
import Queue

from threading import Thread

from message import Message

from utils import constants
from utils import errors
from utils import exceptions
from utils import utils
from utils.crypto import Crypto


class Client(Thread):
    RSA = 0
    AES = 1

    def __init__(self, connectionManager, remoteNick, crypto, sendMessageCallback, recvMessageCallback, handshakeDoneCallback, errorCallback, initiateHandkshakeOnStart=False):
        Thread.__init__(self)
        self.daemon = True

        self.connectionManager = connectionManager
        self.remoteNick = remoteNick
        self.sendMessageCallback = sendMessageCallback
        self.recvMessageCallback = recvMessageCallback
        self.handshakeDoneCallback = handshakeDoneCallback
        self.errorCallback = errorCallback
        self.initiateHandkshakeOnStart = initiateHandkshakeOnStart

        self.encryptionType = None
        self.wasHandshakeDone = False
        self.messageQueue = Queue.Queue()

        # We need to generate a new AES key so each client uses a unique AES key
        self.crypto = crypto
        self.crypto.generateAESKey()


    def sendChatMessage(self, text):
        self.sendMessage(constants.COMMAND_MSG, text)


    def sendMessage(self, command, payload=None):
        message = Message(clientCommand=command, destNick=self.remoteNick)

        # Encrypt all outgoing data
        if payload is not None and self.encryptionType is not None:
            if self.encryptionType == self.AES:
                payload = self.crypto.aesEncrypt(payload)

                # Generate and set the HMAC for the message
                message.setBinaryHmac(self.crypto.generateHmac(payload))
            elif self.encryptionType == self.RSA:
                payload = self.crypto.rsaEncrypt(payload)
            else:
                raise exceptions.CryptoError(errors.UNKNOWN_ENCRYPTION_TYPE)

            message.setEncryptedPayload(payload)
        else:
            message.payload = payload

        self.sendMessageCallback(message)


    def postMessage(self, message):
        self.messageQueue.put(message)


    def run(self):
        if self.initiateHandkshakeOnStart:
            self.__initiateHandshake()
        else:
            self.__doHandshake()

        while True:
            message = self.messageQueue.get()

            command = message.clientCommand
            payload = message.payload

            # Check if the client requested to end the connection
            if command == constants.COMMAND_END:
                self.errorCallback(self.remoteNick, errors.ERR_CONNECTION_ENDED)
                self.connectionManager.destroyClient(self.remoteNick)
                return
            # Ensure we got a valid command
            elif self.wasHandshakeDone and command not in constants.LOOP_COMMANDS:
                self.errorCallback(self.remoteNick, errors.ERR_INVALID_COMMAND)
                self.connectionManager.destroyClient(self.remoteNick)
                return

            # Decrypt the incoming data
            payload = self.__getDecryptedPayload(message)

            self.messageQueue.task_done()
            self.recvMessageCallback(command, message.sourceNick, payload)


    def connect(self):
        self.__initiateHandshake()


    def disconnect(self):
        try:
            self.sendMessage(constants.COMMAND_END)
        except Exception:
            pass


    def __doHandshake(self):
        try:
            # The caller of this function (should) checks for the initial HELO command

            # Send the ready command
            self.sendMessage(constants.COMMAND_REDY)

            # Receive the client's public key
            clientPublicKey = self.__getHandshakeMessagePayload(constants.COMMAND_PUBLIC_KEY)
            self.crypto.setRemotePubKey(clientPublicKey[:-1])

            # Send the server's public key
            serverPublicKey = self.crypto.getLocalPubKeyAsString()
            self.sendMessage(constants.COMMAND_PUBLIC_KEY, serverPublicKey)

            # Switch to RSA encryption to exchange the AES key, IV, and salt
            self.encryptionType = self.RSA

            # Send the AES key, IV, and salt
            self.sendMessage(constants.COMMAND_AES_KEY, self.crypto.aesKey)
            self.sendMessage(constants.COMMAND_AES_IV, self.crypto.aesIv)
            self.sendMessage(constants.COMMAND_AES_SALT, self.crypto.aesSalt)

            # Switch to AES encryption for the remainder of the connection
            self.encryptionType = self.AES

            self.wasHandshakeDone = True
            self.handshakeDoneCallback(self.remoteNick)
        except exceptions.ProtocolEnd:
            self.disconnect()
            self.connectionManager.destroyClient(self.remoteNick)
        except exceptions.ProtocolError as pe:
            self.__handleHandshakeError(pe)


    def __initiateHandshake(self):
        try:
            # Send the hello command
            self.sendMessage(constants.COMMAND_HELO)

            # Receive the redy command
            self.__getHandshakeMessagePayload(constants.COMMAND_REDY)

            # Send the client's public key
            clientPublicKey = self.crypto.getLocalPubKeyAsString()
            self.sendMessage(constants.COMMAND_PUBLIC_KEY, clientPublicKey)

            # Receive the server's public key
            serverPublicKey = self.__getHandshakeMessagePayload(constants.COMMAND_PUBLIC_KEY)
            self.crypto.setRemotePubKey(serverPublicKey)

            # Switch to RSA encryption to receive the AES key, IV, and salt
            self.encryptionType = self.RSA

            # Receive the AES key
            self.crypto.aesKey = self.__getHandshakeMessagePayload(constants.COMMAND_AES_KEY)

            # Receive the AES IV
            self.crypto.aesIv = self.__getHandshakeMessagePayload(constants.COMMAND_AES_IV)

            # Receive the AES salt
            self.crypto.aesSalt = self.__getHandshakeMessagePayload(constants.COMMAND_AES_SALT)

            # Switch to AES encryption for the remainder of the connection
            self.encryptionType = self.AES

            self.wasHandshakeDone = True
            self.handshakeDoneCallback(self.remoteNick)
        except exceptions.ProtocolEnd:
            self.disconnect()
            self.connectionManager.destroyClient(self.remoteNick)
        except exceptions.ProtocolError as pe:
            self.__handleHandshakeError(pe)


    def __getHandshakeMessagePayload(self, expectedCommand):
        message = self.messageQueue.get()

        if message.clientCommand != expectedCommand:
            if message.clientCommand == constants.COMMAND_END:
                raise exceptions.ProtocolEnd
            elif message.clientCommand == constants.COMMAND_REJECT:
                raise exceptions.ProtocolError(errors.ERR_CONNECTION_REJECTED)
            else:
                raise exceptions.ProtocolError(errors.ERR_BAD_HANDSHAKE)

        payload = self.__getDecryptedPayload(message)

        self.messageQueue.task_done()
        return payload


    def __getDecryptedPayload(self, message):
        if self.encryptionType is not None:
            payload = message.getEncryptedPayloadAsString()
            if self.encryptionType == self.AES:
                # Check the HMAC
                if not self.__verifyHmac(message.hmac, message.getEncryptedPayloadAsString()):
                    self.errorCallback(message.sourceNick, errors.ERR_BAD_HMAC)
                    raise exceptions.CryptoError(errors.BAD_HMAC)

                try:
                    payload = self.crypto.aesDecrypt(payload)
                except exceptions.CryptoError as ce:
                    self.errorCallback(message.sourceNick, errors.ERR_BAD_DECRYPT)
                    raise ce
            elif self.encryptionType == self.RSA:
                try:
                    payload = self.crypto.rsaDecrypt(payload)
                except exceptions.CryptoError as ce:
                    self.errorCallback(message.sourceNick, errors.ERR_BAD_DECRYPT)
                    raise ce
            else:
                raise exceptions.CryptoError(errors.UNKNOWN_ENCRYPTION_TYPE)
        else:
            payload = message.payload

        return payload


    def __verifyHmac(self, givenHmac, payload):
        generatedHmac = self.crypto.generateHmac(payload)
        return utils.secureStrcmp(generatedHmac, base64.b64decode(givenHmac))


    def __handleHandshakeError(self, exception):
        self.errorCallback(self.remoteNick, exception.errno)

        # For all errors except the connection being rejected, tell the client there was an error
        if exception.errno != errors.ERR_CONNECTION_REJECTED:
            self.sendMessage(constants.COMMAND_ERR)
        # For reject errors, delete this client
        else:
            self.connectionManager.destroyClient(self.remoteNick)
