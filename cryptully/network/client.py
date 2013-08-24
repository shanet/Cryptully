import base64
import Queue

from crypto.crypto import Crypto
from crypto.smp import SMP

from message import Message

from threading import Thread

from utils import constants
from utils import errors
from utils import exceptions
from utils import utils


class Client(Thread):
    def __init__(self, connectionManager, remoteNick, sendMessageCallback, recvMessageCallback, handshakeDoneCallback, errorCallback, initiateHandkshakeOnStart=False):
        Thread.__init__(self)
        self.daemon = True

        self.connectionManager = connectionManager
        self.remoteNick = remoteNick
        self.sendMessageCallback = sendMessageCallback
        self.recvMessageCallback = recvMessageCallback
        self.handshakeDoneCallback = handshakeDoneCallback
        self.errorCallback = errorCallback
        self.initiateHandkshakeOnStart = initiateHandkshakeOnStart

        self.isEncrypted = False
        self.wasHandshakeDone = False
        self.messageQueue = Queue.Queue()

        self.crypto = Crypto()
        self.crypto.generateDHKey()


    def sendChatMessage(self, text):
        self.sendMessage(constants.COMMAND_MSG, text)


    def sendMessage(self, command, payload=None):
        message = Message(clientCommand=command, destNick=self.remoteNick)

        # Encrypt all outgoing data
        if payload is not None and self.isEncrypted:
            payload = self.crypto.aesEncrypt(payload)
            message.setEncryptedPayload(payload)

            # Generate and set the HMAC for the message
            message.setBinaryHmac(self.crypto.generateHmac(payload))
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

        if not self.wasHandshakeDone:
            return

        while True:
            message = self.messageQueue.get()

            command = message.clientCommand
            payload = message.payload

            # Check if the client requested to end the connection
            if command == constants.COMMAND_END:
                self.connectionManager.destroyClient(self.remoteNick)
                self.errorCallback(self.remoteNick, errors.ERR_CONNECTION_ENDED)
                return
            # Ensure we got a valid command
            elif self.wasHandshakeDone and command not in constants.LOOP_COMMANDS:
                self.connectionManager.destroyClient(self.remoteNick)
                self.errorCallback(self.remoteNick, errors.ERR_INVALID_COMMAND)
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
        except:
            pass


    def __doHandshake(self):
        try:
            # The caller of this function (should) checks for the initial HELO command

            # Send the ready command
            self.sendMessage(constants.COMMAND_REDY)

            # Receive the client's public key
            clientPublicKey = self.__getHandshakeMessagePayload(constants.COMMAND_PUBLIC_KEY)
            self.crypto.computeDHSecret(long(base64.b64decode(clientPublicKey)))

            # Send our public key
            publicKey = base64.b64encode(str(self.crypto.getDHPubKey()))
            self.sendMessage(constants.COMMAND_PUBLIC_KEY, publicKey)

            # Switch to AES encryption for the remainder of the connection
            self.isEncrypted = True

            # Do SMP
            secret = long(self.crypto.dhSecret)
            self.__doSMP(SMP(secret))

            self.wasHandshakeDone = True
            self.handshakeDoneCallback(self.remoteNick)
        except exceptions.ProtocolEnd:
            self.disconnect()
            self.connectionManager.destroyClient(self.remoteNick)
        except (exceptions.ProtocolError, exceptions.CryptoError) as e:
            self.__handleHandshakeError(e)


    def __initiateHandshake(self):
        try:
            # Send the hello command
            self.sendMessage(constants.COMMAND_HELO)

            # Receive the redy command
            self.__getHandshakeMessagePayload(constants.COMMAND_REDY)

            # Send our public key
            publicKey = base64.b64encode(str(self.crypto.getDHPubKey()))
            self.sendMessage(constants.COMMAND_PUBLIC_KEY, publicKey)

            # Receive the client's public key
            clientPublicKey = self.__getHandshakeMessagePayload(constants.COMMAND_PUBLIC_KEY)
            self.crypto.computeDHSecret(long(base64.b64decode(clientPublicKey)))

            # Switch to AES encryption for the remainder of the connection
            self.isEncrypted = True

            # Do SMP
            secret = long(self.crypto.dhSecret)
            self.__initiateSMP(SMP(secret))

            self.wasHandshakeDone = True
            self.handshakeDoneCallback(self.remoteNick)
        except exceptions.ProtocolEnd:
            self.disconnect()
            self.connectionManager.destroyClient(self.remoteNick)
        except (exceptions.ProtocolError, exceptions.CryptoError) as e:
            self.__handleHandshakeError(e)


    def __getHandshakeMessagePayload(self, expectedCommand):
        message = self.messageQueue.get()

        if message.clientCommand != expectedCommand:
            if message.clientCommand == constants.COMMAND_END:
                raise exceptions.ProtocolEnd
            elif message.clientCommand == constants.COMMAND_REJECT:
                raise exceptions.ProtocolError(errno=errors.ERR_CONNECTION_REJECTED)
            else:
                raise exceptions.ProtocolError(errno=errors.ERR_BAD_HANDSHAKE)

        payload = self.__getDecryptedPayload(message)

        self.messageQueue.task_done()
        return payload


    def __getDecryptedPayload(self, message):
        if self.isEncrypted:
            payload = message.getEncryptedPayloadAsBinaryString()

            # Check the HMAC
            if not self.__verifyHmac(message.hmac, payload):
                self.errorCallback(message.sourceNick, errors.ERR_BAD_HMAC)
                raise exceptions.CryptoError(errno=errors.BAD_HMAC)

            try:
                # Decrypt the payload
                payload = self.crypto.aesDecrypt(payload)
            except exceptions.CryptoError as ce:
                self.errorCallback(message.sourceNick, errors.ERR_BAD_DECRYPT)
                raise ce
        else:
            payload = message.payload

        return payload


    def __verifyHmac(self, givenHmac, payload):
        generatedHmac = self.crypto.generateHmac(payload)
        return utils.secureStrcmp(generatedHmac, base64.b64decode(givenHmac))


    def __initiateSMP(self, smp):
        buffer = smp.step1()
        self.sendMessage(constants.COMMAND_SMP_1, buffer)

        buffer = self.__getHandshakeMessagePayload(constants.COMMAND_SMP_2)
        buffer = smp.step3(buffer)
        self.sendMessage(constants.COMMAND_SMP_3, buffer)

        buffer = self.__getHandshakeMessagePayload(constants.COMMAND_SMP_4)
        smp.step5(buffer)

        self.__checkSMP(smp)


    def __doSMP(self, smp):
        buffer = self.__getHandshakeMessagePayload(constants.COMMAND_SMP_1)
        buffer = smp.step2(buffer)
        self.sendMessage(constants.COMMAND_SMP_2, buffer)

        buffer = self.__getHandshakeMessagePayload(constants.COMMAND_SMP_3)
        buffer = smp.step4(buffer)
        self.sendMessage(constants.COMMAND_SMP_4, buffer)

        self.__checkSMP(smp)


    def __checkSMP(self, smp):
        if not smp.match:
            raise exceptions.CryptoError(errno=errors.ERR_SMP_MATCH_FAILED)


    def __handleHandshakeError(self, exception):
        self.errorCallback(self.remoteNick, exception.errno)

        # For all errors except the connection being rejected, tell the client there was an error
        if exception.errno != errors.ERR_CONNECTION_REJECTED:
            self.sendMessage(constants.COMMAND_ERR)
        else:
            self.connectionManager.destroyClient(self.remoteNick)
