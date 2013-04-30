import socket

import Exceptions


class EncSocket:
    
    def __init__(self, addr, sock=None):
        self.addr = addr

        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock


    def connect(self):
        try:
            self.sock.connect(self.addr)
        except socket.error as se:
            raise GenericError(str(se))


    def disconnect(self):
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()


    def send(self, data):
        if type(data) is not str:
            raise TypeError()

        # Get the length of the data so the client knows how much data to expect
        length = len(data)

        # Pad the length to a fixed number of characters
        strLength = self.__padLength(length)

        # Send the length and then send the actual data
        self.__send(strLength, len(strLength))
        self.__send(data, length)


    def __send(self, data, length):
        # Add a newline to all outgoing data
        data += '\n'

        sentLen = 0
        while sentLen < length:
            amountSent = self.sock.send(data[sentLen:])
            if amountSent == 0:
                raise Exceptions.NetworkError("Remote unexpectedly closed connection")
            sentLen += amountSent


    def recv(self):
        try:
            # Recieve the amount of incoming data
            length = self.__recv(5)
    
            # Strip the newline from the length so it can be converted to an int
            try:
                length = (int(length[:-1]))
            except ValueError as ve:
                raise GenericError(str(ve))
    
            # Recieve the actual data
            return self.__recv(length)
        except socket.error as se:
            raise NetworkError(str(se))


    def __recv(self, length):
        # Increment the length to accomodate the newline
        length += 1

        data = ''
        while len(data) < length:
            chunk = self.sock.recv(length - len(data))
            if chunk == '':
                raise Exceptions.NetworkError("Remote unexpectedly closed connection")
            data += chunk

        return data


    def getHostName(self):
        return self.addr[0]


    def __padLength(self, length):
        strLength = str(length)
        while(len(strLength) < 5):
            strLength = '0' + strLength

        return strLength
