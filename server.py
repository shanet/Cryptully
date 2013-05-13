import socket

import _exceptions
from encSocket import EncSocket


class Server:

    def __init__(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Allow reuse of port
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except socket.error as se:
            raise _exceptions.NetworkError(str(se))


    def startServer(self, port):
        try:
            self.sock.bind(('localhost', port))
            self.sock.listen(5)
        except socket.error as se:
            raise _exceptions.NetworkError(str(se))


    def stopServer(self):
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()


    def accept(self):
        (clientSock, clientAddr) = self.sock.accept()
        return EncSocket(clientAddr, clientSock)
