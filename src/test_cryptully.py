#! /usr/bin/env python

import sys
import unittest

from tests.testClient import TestClient

clientSuite = unittest.TestSuite()

clientSuite.addTest(TestClient('testConncecToServer'))
clientSuite.addTest(TestClient('testCheckHostname'))
clientSuite.addTest(TestClient('testHandshake'))
clientSuite.addTest(TestClient('checkEncryptType'))
clientSuite.addTest(TestClient('testSendMessageToServer'))
clientSuite.addTest(TestClient('testReceiveMessageFromServer'))
clientSuite.addTest(TestClient('testSendUnexpectCommandToServer'))
clientSuite.addTest(TestClient('testDisconnect'))

result = unittest.TextTestRunner(verbosity=2).run(clientSuite)

sys.exit(0 if result.wasSuccessful() else 1)
