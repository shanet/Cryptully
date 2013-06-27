#! /usr/bin/env python

import unittest

import _exceptions
from server    import Server
from encSocket import EncSocket


class TestServerClientCommunication(unittest.TestCase):
    def setUp(self):
        self.server = Server()
        self.client = EncSocket(('127.0.0.1', 9000))


    def testStartServer(self):
        try:
            self.server.start(9000)
            self.assertTrue(self.server.isStarted)
        except _exceptions.NetworkError:
            self.fail("Failed to start server")

    @unittest.skip("test not implemented yet")
    def testConnectClient(self):
        pass

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