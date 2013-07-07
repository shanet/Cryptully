#! /usr/bin/env python

import unittest

from cryptully.network.client import Client
from cryptully.network.server import Server

from cryptully.utils import constants


class TestServerClientCommunication(unittest.TestCase):
    def setUp(self):
        self.server = Server()
        self.client = Client(constants.MODE_CLIENT, ('127.0.0.1', constants.DEFAULT_PORT))


    def testStartServer(self):
        try:
            self.server.start(9000)
            self.assertTrue(self.server.isStarted)
        except Exception as e:
            self.fail("Failed to start server: " + str(e))

    def testConnectClient(self):
        try:
            pass
            #self.client.connect()
        except Exception as e:
            self.fail("Failed to connect to server: " + str(e))

    @unittest.skip("test not implemented yet")
    def testGetHostname(self):
        pass

    @unittest.skip("test not implemented yet")
    def testBasicServerClientCommunication(self):
        pass

    @unittest.skip("test not implemented yet")
    def testProtocolHandshake(self):
        pass

    @unittest.skip("test not implemented yet")
    def testRsaCommunication(self):
        pass

    @unittest.skip("test not implemented yet")
    def testAesCommunication(self):
        pass

    @unittest.skip("test not implemented yet")
    def testEndConnection(self):
        pass

    @unittest.skip("test not implemented yet")
    def testStopClient(self):
        pass

    @unittest.skip("test not implemented yet")
    def testStopServer(self):
        pass


testServerClientCommunication = unittest.TestLoader().loadTestsFromTestCase(TestServerClientCommunication)
unittest.TextTestRunner(verbosity=2).run(testServerClientCommunication)
