import sys
import time
import traceback

from threading import Thread

from network.connectionManager import ConnectionManager
from utils import constants
from .waitingMock import WaitingMock


class MockClient(Thread):
    def __init__(self, nick, remoteNick):
        Thread.__init__(self)

        self.nick = nick
        self.remoteNick = remoteNick
        self.exceptions = []

        self.message1 = 'message 1'
        self.message2 = 'message 2'

        self.smpQuestion = 'when do we attack?'
        self.smpAnswer = 'at dawn'

        self.recvMessageCallback = WaitingMock()
        self.newClientCallback = WaitingMock()
        self.handshakeDoneCallback = WaitingMock()
        self.smpRequestCallback = WaitingMock()
        self.errorCallback = WaitingMock()

        self.connectionManager = ConnectionManager(self.nick, ('localhost', constants.DEFAULT_PORT),
            self.recvMessageCallback, self.newClientCallback, self.handshakeDoneCallback, self.smpRequestCallback, self.errorCallback)

    def success(self):
        sys.stdout.write('.')


    def failure(self):
        sys.stdout.write('F')


    def exception(self):
        sys.stdout.write('E')


    def printExceptions(self):
        for exception in self.exceptions:
            print("\n%s\n%s" % (exception[1], exception[0]))


class Client1(MockClient):
    def __init__(self, nick, remoteNick):
        MockClient.__init__(self, nick, remoteNick)


    def run(self):
        try:
            self.connectionManager.connectToServer()

            # There's no connected to server callback so wait for all mock clients to connect to the server before trying to connect to one
            time.sleep(1)

            # Open the chat again and expect success
            self.connectionManager.openChat(self.remoteNick)
            self.handshakeDoneCallback.assert_called_with_wait(self.remoteNick)

            client = self.connectionManager.getClient(self.remoteNick)

            # Send two regular chat messages
            client.sendChatMessage(self.message1)
            client.sendChatMessage(self.message2)

            # Expect client 1 to send two typing messages
            self.recvMessageCallback.assert_called_with_wait(constants.COMMAND_TYPING, self.remoteNick, str(constants.TYPING_STOP_WITHOUT_TEXT))
            self.recvMessageCallback.assert_called_with_wait(constants.COMMAND_TYPING, self.remoteNick, str(constants.TYPING_START))

            # Start an SMP request
            client.initiateSMP(self.smpQuestion, self.smpAnswer)
            self.smpRequestCallback.assert_called_with_wait(constants.SMP_CALLBACK_COMPLETE, self.remoteNick)

            # End the connection
            client.disconnect()

            self.success()
        except AssertionError as err:
            self.failure()
            self.exceptions.append((err, traceback.format_exc()))
        except Exception as err:
            self.exception()
            self.exceptions.append((err, traceback.format_exc()))


class Client2(MockClient):
    def __init__(self, nick, remoteNick):
        MockClient.__init__(self, nick, remoteNick)


    def run(self):
        try:
            self.connectionManager.connectToServer()

            # Expect client 1 to open a chat with us and then accept it
            self.newClientCallback.assert_called_with_wait(self.remoteNick)
            self.connectionManager.newClientAccepted(self.remoteNick)
            self.handshakeDoneCallback.assert_called_with_wait(self.remoteNick)

            # Expect client 1 to send us two messages
            # Message 1 should arrive first so check for message 2 since the callbacks are stored in a stack
            self.recvMessageCallback.assert_called_with_wait(constants.COMMAND_MSG, self.remoteNick, self.message2)
            self.recvMessageCallback.assert_called_with_wait(constants.COMMAND_MSG, self.remoteNick, self.message1)

            client = self.connectionManager.getClient(self.remoteNick)

            # Send the typing command and then the stop typing command
            client.sendTypingMessage(constants.TYPING_START)
            client.sendTypingMessage(constants.TYPING_STOP_WITHOUT_TEXT)

            # Expect an SMP request
            self.smpRequestCallback.assert_called_with_wait(constants.SMP_CALLBACK_REQUEST, self.remoteNick, self.smpQuestion)
            client.respondSMP(self.smpAnswer)

            # Expec client 1 to end the connection
            self.recvMessageCallback.assert_called_with_wait(constants.COMMAND_END, self.remoteNick, None)

            self.success()
        except AssertionError as err:
            self.failure()
            self.exceptions.append((err, traceback.format_exc()))
        except:
            self.exception()
            self.exceptions.append((err, traceback.format_exc()))
