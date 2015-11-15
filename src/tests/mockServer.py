from threading import Thread

from server.turnServer import TURNServer
from utils import constants


class MockServer(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.server = None


    def run(self):
        self.server = TURNServer(constants.DEFAULT_PORT, showConsole=False)
        self.server.start()
