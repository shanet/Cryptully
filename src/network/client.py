import base64
import queue

from crypto.crypto import Crypto
from crypto.smp import SMP

from .message import Message

from threading import Thread

from utils import constants
from utils import errors
from utils import exceptions
from utils import utils


class Client(Thread):
    def __init__(self, connectionManager, remoteNick, sendMessageCallback, recvMessageCallback, handshakeDoneCallback, smpRequestCallback, errorCallback, initiateHandkshakeOnStart=False):
        Thread.__init__(self)
        self.daemon = True

        self.connectionManager = connectionManager
        self.remoteNick = remoteNick
        self.sendMessageCallback = sendMessageCallback
        self.recvMessageCallback = recvMessageCallback
        self.handshakeDoneCallback = handshakeDoneCallback
        self.smpRequestCallback = smpRequestCallback
        self.errorCallback = errorCallback
        self.initiateHandkshakeOnStart = initiateHandkshakeOnStart

        self.incomingMessageNum = 0
        self.outgoingMessageNum = 0
        self.isEncrypted = False
        self.wasHandshakeDone = False
        self.messageQueue = queue.Queue()

        self.crypto = Crypto()
        self.crypto.generateDHKey()
        self.smp = None


    def sendChatMessage(self, text):
        self.sendMessage(constants.COMMAND_MSG, text)


    def sendTypingMessage(self, status):
        self.sendMessage(constants.COMMAND_TYPING, str(status))


    def sendMessage(self, command, payload=None):
        message = Message(clientCommand=command, destNick=self.remoteNick)

        # Encrypt all outgoing data
        if payload is not None and self.isEncrypted:
            payload = self.crypto.aesEncrypt(payload)
            message.setEncryptedPayload(payload)

            # Generate and set the HMAC for the message
            message.setBinaryHmac(self.crypto.generateHmac(payload))

            # Encrypt the message number of the message
            message.setBinaryMessageNum(self.crypto.aesEncrypt(str(self.outgoingMessageNum)))
            self.outgoingMessageNum += 1
        else:
            message.payload = payload

        self.sendMessageCallback(message)


    def postMessage(self, message):
        self.messageQueue.put(message)


    def initiateSMP(self, question, answer):
        self.sendMessage(constants.COMMAND_SMP_0, question)

        self.smp = SMP(answer)
        buffer = self.smp.step1()
        self.sendMessage(constants.COMMAND_SMP_1, buffer)


    def respondSMP(self, answer):
        self.smp = SMP(answer)
        self.__doSMPStep1(self.smpStep1)


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

            # Handle SMP commands specially
            if command in constants.SMP_COMMANDS:
               self.__handleSMPCommand(command, payload)
            else:
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
            self.crypto.computeDHSecret(int(base64.b64decode(clientPublicKey)))

            # Send our public key
            publicKey = base64.b64encode(str(self.crypto.getDHPubKey()))
            self.sendMessage(constants.COMMAND_PUBLIC_KEY, publicKey)

            # Switch to AES encryption for the remainder of the connection
            self.isEncrypted = True

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
            self.crypto.computeDHSecret(int(base64.b64decode(clientPublicKey)))

            # Switch to AES encryption for the remainder of the connection
            self.isEncrypted = True

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
            encryptedMessageNumber = message.getMessageNumAsBinaryString()

            # Check the HMAC
            if not self.__verifyHmac(message.hmac, payload):
                self.errorCallback(message.sourceNick, errors.ERR_BAD_HMAC)
                raise exceptions.CryptoError(errno=errors.BAD_HMAC)

            try:
                # Check the message number
                messageNumber = int(self.crypto.aesDecrypt(encryptedMessageNumber))

                # If the message number is less than what we're expecting, the message is being replayed
                if self.incomingMessageNum > messageNumber:
                    raise exceptions.ProtocolError(errno=errors.ERR_MESSAGE_REPLAY)
                # If the message number is greater than what we're expecting, messages are being deleted
                elif self.incomingMessageNum < messageNumber:
                    raise exceptions.ProtocolError(errno=errors.ERR_MESSAGE_DELETION)
                self.incomingMessageNum += 1

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


    def __handleSMPCommand(self, command, payload):
        try:
            if command == constants.COMMAND_SMP_0:
                # Fire the SMP request callback with the given question
                self.smpRequestCallback(constants.SMP_CALLBACK_REQUEST, self.remoteNick, payload)
            elif command == constants.COMMAND_SMP_1:
                # If there's already an smp object, go ahead to step 1.
                # Otherwise, save the payload until we have an answer from the user to respond with
                if self.smp:
                    self.__doSMPStep1(payload)
                else:
                    self.smpStep1 = payload
            elif command == constants.COMMAND_SMP_2:
                self.__doSMPStep2(payload)
            elif command == constants.COMMAND_SMP_3:
                self.__doSMPStep3(payload)
            elif command == constants.COMMAND_SMP_4:
                self.__doSMPStep4(payload)
            else:
                # This shouldn't happen
                raise exceptions.CryptoError(errno=errors.ERR_SMP_CHECK_FAILED)
        except exceptions.CryptoError as ce:
            self.smpRequestCallback(constants.SMP_CALLBACK_ERROR, self.remoteNick, '', ce.errno)


    def __doSMPStep1(self, payload):
        buffer = self.smp.step2(payload)
        self.sendMessage(constants.COMMAND_SMP_2, buffer)


    def __doSMPStep2(self, payload):
        buffer = self.smp.step3(payload)
        self.sendMessage(constants.COMMAND_SMP_3, buffer)


    def __doSMPStep3(self, payload):
        buffer = self.smp.step4(payload)
        self.sendMessage(constants.COMMAND_SMP_4, buffer)

        # Destroy the SMP object now that we're done
        self.smp = None


    def __doSMPStep4(self, payload):
        self.smp.step5(payload)

        if self.__checkSMP():
            self.smpRequestCallback(constants.SMP_CALLBACK_COMPLETE, self.remoteNick)

        # Destroy the SMP object now that we're done
        self.smp = None


    def __checkSMP(self):
        if not self.smp.match:
            raise exceptions.CryptoError(errno=errors.ERR_SMP_MATCH_FAILED)
        return True


    def __handleHandshakeError(self, exception):
        self.errorCallback(self.remoteNick, exception.errno)

        # For all errors except the connection being rejected, tell the client there was an error
        if exception.errno != errors.ERR_CONNECTION_REJECTED:
            self.sendMessage(constants.COMMAND_ERR)
        else:
            self.connectionManager.destroyClient(self.remoteNick)
