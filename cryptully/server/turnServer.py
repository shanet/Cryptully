import Queue
import socket
import sys
import time

from threading import Thread

from network.message import Message
from network.sock import Socket

from utils import constants
from utils import errors
from utils import exceptions
from utils import utils


# Dict to store connected clients in
nickMap = {}

# Dict for new clients that haven't registered a nick yet
ipMap = {}


class TURNServer(object):
    def __init__(self, listenPort):
        self.listenPort = listenPort

    def start(self):
        serversock = self.startServer()

        while True:
            # Wait for a client to connect
            print "Waiting for client..."
            (clientSock, clientAddr) = serversock.accept()

            # Wrap the socket in our socket object
            clientSock = Socket(clientAddr, clientSock)

            # Store the client's IP and port in the IP map
            print "Adding to map with value: " + str(clientSock)
            ipMap[str(clientSock)] = Client(clientSock)


    def startServer(self):
        print "Starting server..."
        serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            serversock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            serversock.bind(('0.0.0.0', self.listenPort))
            serversock.listen(10)
            return serversock
        except exceptions.NetworkError as ne:
            print "Failed to start server"
            sys.exit(1)


    def stop(self):
        for nick, client in nickMap.iteritems():
            client.send(Message(serverCommand=constants.COMMAND_END, destNick=nick, error=errors.ERR_SERVER_SHUTDOWN))

        # Give the send threads time to get their messages out
        time.sleep(.25)


class Client(object):
    def __init__(self, sock):
        self.sock = sock
        self.nick = None
        self.sendThread = SendThread(sock)
        self.recvThread = RecvThread(sock, self.__nickRegistered)

        self.sendThread.start()
        self.recvThread.start()


    def send(self, message):
        self.sendThread.queue.put(message)


    def __nickRegistered(self, nick):
        # Add the client to the nick map and remove it from the ip map
        print "Adding '" + nick + "' to client map"
        self.nick = nick
        nickMap[nick] = self
        del ipMap[str(self.sock)]


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
            except socket.error:
                print "Error sending data to client"
                # TODO: handle broken connections
            finally:
                self.queue.task_done()


class RecvThread(Thread):
    def __init__(self, sock, nickRegisteredCallback):
        Thread.__init__(self)
        self.daemon = True

        self.sock = sock
        self.nickRegisteredCallback = nickRegisteredCallback


    def run(self):
        # The first communcation with the client is registering a nick
        message = Message.createFromJSON(self.sock.recv())

        # Check that the client sent the register command
        if message.serverCommand != constants.COMMAND_REGISTER:
            print "Client sent invalid command"
            self.__handleError(errors.ERR_INVALID_COMMAND)
            return

        # Check that the nick is valid
        if utils.isValidNick(message.sourceNick) != errors.VALID_NICK:
            print "Client sent invalid nick"
            self.__handleError(errors.ERR_INVALID_NICK)
            return

        # Check that the nick is not already in use
        if message.sourceNick in nickMap:
            print "Client tried to register nick already in use"
            self.__handleError(errors.ERR_NICK_IN_USE)
            return

        self.nick = message.sourceNick
        self.nickRegisteredCallback(message.sourceNick)

        while True:
            try:
                message = Message.createFromJSON(self.sock.recv())
            
                if message.serverCommand == constants.COMMAND_END:
                    print self.nick + " requested to end connection"
                    nickMap[self.nick].disconnect()
                    return
                elif message.serverCommand != constants.COMMAND_RELAY:
                    print "got bad message from client: " + message
                    self.__handleError(errors.ERR_INVALID_COMMAND)
                    return

                try:
                    client = nickMap[message.destNick]

                    # Rewrite the nick to prevent nick spoofing
                    message.sourceNick = self.nick

                    client.send(message)
                except KeyError:
                    print "Nick not found: " + message.destNick
                    self.sock.send(str(Message(serverCommand=constants.COMMAND_ERR, destNick=message.destNick, error=errors.ERR_NICK_NOT_FOUND)))
            except exceptions.NetworkError as ne:
                print self.nick + ": " + str(ne)
                # TODO: handle broken connections
                return


    def __handleError(self, errorCode):
        self.sock.send(str(Message(serverCommand=constants.COMMAND_ERR, error=errorCode)))
        self.sock.disconnect()

        # Remove the client from the ip or nick maps (it may be in either)
        try:
            del ipMap[str(self.sock)]
        except Exception:
            pass
        try:
            del nickMap[self.nick]
        except Exception:
            pass
