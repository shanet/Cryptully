import unittest

from crypto.crypto import Crypto

from network.client import Client
from network.server import Server

from threading import Thread

from utils import constants
from utils import errors
from utils import exceptions
from utils import utils


CLIENT_TEST_MESSAGE_1 = "client test message 1"
SERVER_TEST_MESSAGE_1 = "server test message 1"
SERVER_TEST_MESSAGE_2 = "server test message 2"
SERVER_TEST_MESSAGE_3 = "server test message 3"


class TestClient(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        try:
            self.client = Client(constants.MODE_CLIENT, ('127.0.0.1', constants.DEFAULT_PORT))

            self.server = Server()
            self.server.start(constants.DEFAULT_PORT)

            # Run the test server thread
            self.testsServerThread = TestsServerThread(self.server)
            self.testsServerThread.start()
        except Exception as e:
            print "Failed to start server: " + str(e)
            raise e


    @classmethod
    def tearDownClass(self):
        try:
            self.server.stop()
        except Exception as e:
            self.fail("Failed to stop server: " + str(e))
            raise 3


    def testConncecToServer(self):
        try:
            self.client.connect()
        except Exception as e:
            print "Failed to connect to server: " + str(e)
            raise e


    def testCheckHostname(self):
        self.assertEqual(self.client.getHostname(), "127.0.0.1")


    def testHandshake(self):
        try:
            self.client.doHandshake()
        except Exception as e:
            self.fail(str(e))


    def checkEncryptType(self):
        # Confirm AES is being used
        self.assertEqual(self.client.sock.encryptType, self.client.sock.AES)


    def testSendMessageToServer(self):
        self.client.sendMessage(constants.COMMAND_MSG, CLIENT_TEST_MESSAGE_1)


    def testReceiveMessageFromServer(self):
        message = self.client.receiveMessage(constants.COMMAND_MSG)
        self.assertEqual(message, SERVER_TEST_MESSAGE_1)
        message = self.client.receiveMessage(constants.COMMAND_MSG)
        self.assertEqual(message, SERVER_TEST_MESSAGE_2)
        message = self.client.receiveMessage(constants.COMMAND_MSG)
        self.assertEqual(message, SERVER_TEST_MESSAGE_3)

    def testSendUnexpectCommandToServer(self):
        self.client.sendMessage(constants.COMMAND_REDY)

        # Server should respond with error command
        self.client.receiveMessage(constants.COMMAND_ERR)


    def testDisconnect(self):
        self.client.disconnect()


class TestsServerThread(Thread):
    def __init__(self, server):
        Thread.__init__(self)
        self.daemon = True

        self.server = server
        self.crypto = Crypto(generateKeys=True)


    def run(self):
        try:
            # Wait for a client to connect
            client = self.server.accept(self.crypto)

            client.doHandshake()

            message = client.receiveMessage(constants.COMMAND_MSG)
            
            client.sendMessage(constants.COMMAND_MSG, SERVER_TEST_MESSAGE_1)
            client.sendMessage(constants.COMMAND_MSG, SERVER_TEST_MESSAGE_2)
            client.sendMessage(constants.COMMAND_MSG, SERVER_TEST_MESSAGE_3)

            command = client.receiveMessage()
            if command != constants.COMMAND_MSG:
                client.sendMessage(constants.COMMAND_ERR)
            
            client.disconnect()
        except Exception as e:
            print str(e)
