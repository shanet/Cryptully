#! /usr/bin/env python

import unittest

from tests.testClient import TestClient

testClient = unittest.TestLoader().loadTestsFromTestCase(TestClient)

unittest.TextTestRunner(verbosity=2).run(testClient)
