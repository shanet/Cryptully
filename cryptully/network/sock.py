import socket

from utils import errors
from utils import exceptions


class Socket(object):
    def __init__(self, addr, sock=None):
        self.addr = addr
        self.sock = sock

        # Create a new socket if one was not given
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.isConnected = False
        else:
            self.sock = sock
            self.isConnected = True


    def connect(self):
        try:
            self.sock.connect(self.addr)
            self.isConnected = True
        except socket.error as se:
            raise exceptions.GenericError(str(se))


    def disconnect(self):
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        except Exception:
            pass
        finally:
            self.isConnected = False


    def send(self, data):
        dataLength = len(data)

        # Send the length of the message (int converted to network byte order and padded to 32 bytes)
        self._send(str('%32s' % socket.htonl(dataLength)), 32)
        print str('%32s' % socket.htonl(dataLength))

        # Send the actual data
        self._send(data, dataLength)


    def _send(self, data, length):
        sentLen = 0
        while sentLen < length:
            try:
                amountSent = self.sock.send(data[sentLen:])
            except socket.error, IOError:
                raise exceptions.NetworkError(errors.UNEXPECTED_CLOSE_CONNECTION)

            if amountSent == 0:
                raise exceptions.NetworkError(errors.UNEXPECTED_CLOSE_CONNECTION)

            sentLen += amountSent


    def recv(self):
        # Receive the length of the incoming message
        try:
            dataLength = socket.ntohl(int(self._recv(32)))
        except ValueError:
            raise exceptions.NetworkError(errors.UNEXPECTED_DATA)

        # Receive the actual data
        return self._recv(dataLength)


    def _recv(self, length):
        try:
            data = ''
            recvLen = 0
            while recvLen < length:
                newData = self.sock.recv(length-recvLen)

                if newData == '':
                    raise exceptions.NetworkError(errors.UNEXPECTED_CLOSE_CONNECTION)

                data = data + newData
                recvLen += len(newData)

            return data
        except socket.error as se:
            raise exceptions.NetworkError(str(se))


    def getHostname(self):
        return self.addr[0]
