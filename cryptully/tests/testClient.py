import unittest

from network.client import Client
from network.server import Server

from threading import Thread

from utils import constants
from utils import errors
from utils import exceptions
from utils import utils
from utils.crypto import Crypto

CLIENT_TEST_MESSAGE_1 = "client test message 1"
SERVER_TEST_MESSAGE_1 = "server test message 1"
SERVER_TEST_MESSAGE_2 = "server test message 2"
SERVER_TEST_MESSAGE_3 = "server test message 3"

class TestClient(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        try:
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


    def testClientCommuncation(self):
        self.client = Client(constants.MODE_CLIENT, ('127.0.0.1', constants.DEFAULT_PORT))

        try:
            self.client.connect()
        except Exception as e:
            print "Failed to connect to server: " + str(e)
            raise e

        self.assertEqual(self.client.getHostname(), "127.0.0.1")

        # Do the handshake
        try:
            self.client.doHandshake()
        except Exception as e:
            self.fail(str(e))

        # Confirm AES is being used
        self.assertEqual(self.client.sock.encryptType, self.client.sock.AES)

        # Send a message
        self.client.sendMessage(constants.COMMAND_MSG, CLIENT_TEST_MESSAGE_1)

        # Receive messages from the server
        message = self.client.receiveMessage(constants.COMMAND_MSG)
        self.assertEqual(message, SERVER_TEST_MESSAGE_1)
        message = self.client.receiveMessage(constants.COMMAND_MSG)
        self.assertEqual(message, SERVER_TEST_MESSAGE_2)
        message = self.client.receiveMessage(constants.COMMAND_MSG)
        self.assertEqual(message, SERVER_TEST_MESSAGE_3)

        # Send an unexpected command to the server
        self.client.sendMessage(constants.COMMAND_REDY)
        # Server should respond with error command
        self.client.receiveMessage(constants.COMMAND_ERR)

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
