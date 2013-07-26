import socket
import struct

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
        if type(data) is not str:
            raise TypeError()

        dataLength = len(data)

        print "sock sending: %d: %s\n\n" % (dataLength, data)

        # Send the length of the message (int converted to network byte order and packed as binary data)
        self._send(struct.pack("I", socket.htonl(dataLength)), 4)

        # Send the actual data
        self._send(data, dataLength)


    def _send(self, data, length):
        sentLen = 0
        while sentLen < length:
            try:
                amountSent = self.sock.send(data[sentLen:])
            except Exception:
                raise exceptions.NetworkError(errors.UNEXPECTED_CLOSE_CONNECTION)

            if amountSent == 0:
                raise exceptions.NetworkError(errors.UNEXPECTED_CLOSE_CONNECTION)

            sentLen += amountSent


    def recv(self):
        # Receive the length of the incoming message (unpack the binary data)
        try:
            dataLength = socket.ntohl(struct.unpack("I", self._recv(4))[0])
        except Exception as e:
            raise e
            raise exceptions.NetworkError(errors.UNEXPECTED_DATA)

        # Receive the actual data
        data = self._recv(dataLength)
        print "sock recv: %d: %s\n\n" % (dataLength, data)
        return data

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
