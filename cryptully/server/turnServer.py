import Queue
import socket
import sys

from threading import Thread

from network.message import Message
from network.sock import Socket

from utils import constants
from utils import errors
from utils import exceptions
from utils import utils


# Init the IP map
nickMap = {}

class Client(object):
    def __init__(self, sock, nick):
        self.sock = sock
        self.nick = nick
        self.sendThread = SendThread(sock)
        self.recvThread = RecvThread(sock, nick)

        self.sendThread.start()
        self.recvThread.start()


    def send(self, message):
        self.sendThread.queue.put(message)


    def disconnect(self):
        self.sock.disconnect()
        del nickMap[self.nick]


class SendThread(Thread):
    def __init__(self, sock):
        Thread.__init__(self)
        self.daemon = True

        self.sock = sock
        self.queue = Queue.Queue()


    def run(self):
        while True:
            message = self.queue.get()

            try:
                self.sock.send(str(message))
            except socket.error as se:
                print str(se)
            finally:
                self.queue.task_done()


class RecvThread(Thread):
    def __init__(self, sock, nick):
        Thread.__init__(self)
        self.daemon = True

        self.sock = sock
        self.nick = nick


    def run(self):
        while True:
            try:
                message = Message.createFromJSON(self.sock.recv())
            
                print str(message)
                if message.serverCommand == constants.COMMAND_END:
                    print self.nick + " requested to end connection"
                    nickMap[self.nick].disconnect()
                elif message.serverCommand != constants.COMMAND_RELAY:
                    # TODO: handle error
                    print "got bad message from client: " + message
                    continue

                try:
                    client = nickMap[message.destNick]

                    # Rewrite the nick to prevent nick spoofing
                    message.sourceNick = self.nick

                    client.send(message)
                except KeyError:
                    print "Nick not found: " + message.destNick
                    nickMap[self.nick].send(Message(serverCommand=constants.COMMAND_ERR, destNick=message.destNick, error=errors.ERR_NICK_NOT_FOUND))
            except exceptions.NetworkError as ne:
                print self.nick + ": " + str(ne)
                return


class TURNServer(object):
    def __init__(self, listenPort):
        self.listenPort = listenPort

    def start(self):
        threads = []

        # Start the server
        print "Starting server..."
        serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            serversock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            serversock.bind(('0.0.0.0', self.listenPort))
            serversock.listen(10)
        except exceptions.NetworkError as ne:
            print "Failed to start server"
            sys.exit(1)

        while True:
            # Wait for a client to connect
            print "Waiting for client..."
            (clientSock, clientAddr) = serversock.accept()

            # Wrap the socket in our socket object
            clientSock = Socket(clientAddr, clientSock)

            # Get the new client's nick
            message = Message.createFromJSON(clientSock.recv())
            if message.serverCommand != constants.COMMAND_REGISTER or \
               utils.isValidNick(message.sourceNick) != errors.VALID_NICK:
                print "Client sent invalid command or nickname"
                clientSock.send(constants.COMMAND_ERR)
                clientSock.disconnect()
                continue

            self.newClient = Client(clientSock, message.sourceNick)

            # Store the client's IP and port in the IP map
            print "Adding '" + message.sourceNick + "' to map with value: " + clientAddr[0] + ":" + str(clientAddr[1])
            nickMap[message.sourceNick] = self.newClient


    def stop(self):
        for nick in nickMap:
            nick.send(Message(serverCommand=constants.COMMAND_END, destNick=nick.nick, error=errors.ERR_SERVER_SHUTDOWN))
