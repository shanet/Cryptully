import socket

from encSocket import EncSocket

from ..utils import exceptions


class Server(object):

    def __init__(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Allow reuse of port
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except socket.error as se:
            raise exceptions.NetworkError(str(se))

        self.isStarted = False


    def start(self, port):
        try:
            self.sock.bind(('localhost', port))
            self.sock.listen(5)
            self.isStarted = True
        except socket.error as se:
            raise exceptions.NetworkError(str(se))


    def stop(self):
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()
        except socket.error:
            pass
        finally:
            self.isStarted = False


    def accept(self, crypto=None):
        (clientSock, clientAddr) = self.sock.accept()
        return EncSocket(clientAddr, clientSock, crypto)
