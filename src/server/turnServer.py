import queue
import socket
import sys
import time

from threading import Thread

from .console import Console

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

quiet = False


class TURNServer(object):
    def __init__(self, listenPort, showConsole=True):
        self.listenPort = listenPort

        global quiet
        quiet = showConsole


    def start(self):
        self.openLog()
        self.serversock = self.startServer()

        if quiet:
            Console(nickMap, ipMap).start()

        while True:
            # Wait for a client to connect
            (clientSock, clientAddr) = self.serversock.accept()

            # Wrap the socket in our socket object
            clientSock = Socket(clientAddr, clientSock)

            # Store the client's IP and port in the IP map
            printAndLog("Got connection: %s" % str(clientSock))
            ipMap[str(clientSock)] = Client(clientSock)


    def startServer(self):
        printAndLog("Starting server...")
        serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            serversock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            serversock.bind(('0.0.0.0', self.listenPort))
            serversock.listen(10)

            return serversock
        except exceptions.NetworkError as ne:
            printAndLog("Failed to start server")
            sys.exit(1)


    def stop(self):
        printAndLog("Requested to stop server")

        for nick, client in nickMap.items():
            client.send(Message(serverCommand=constants.COMMAND_END, destNick=nick, error=errors.ERR_SERVER_SHUTDOWN))

        # Give the send threads time to get their messages out
        time.sleep(.25)

        if logFile is not None:
            logFile.close()


    def openLog(self):
        global logFile
        try:
            logFile = open('cryptully.log', 'a')
        except:
            logFile = None
            print("Error opening logfile")


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
        printAndLog("%s -> %s" % (str(self.sock), nick))
        self.nick = nick
        nickMap[nick] = self
        try:
            del ipMap[str(self.sock)]
        except KeyError:
            pass


    def disconnect(self):
        self.sock.disconnect()
        del nickMap[self.nick]


    def kick(self):
        self.send(Message(serverCommand=constants.COMMAND_ERR, destNick=self.nick, error=errors.ERR_KICKED))
        time.sleep(.25)
        self.disconnect()



class SendThread(Thread):
    def __init__(self, sock):
        Thread.__init__(self)
        self.daemon = True

        self.sock = sock
        self.queue = queue.Queue()


    def run(self):
        while True:
            message = self.queue.get()

            try:
                self.sock.send(str(message))
            except Exception as e:
                nick = message.destNick
                printAndLog("%s: error sending data to: %s" % (nick, str(e)))
                nickMap[nick].disconnect()
                return
            finally:
                self.queue.task_done()


class RecvThread(Thread):
    def __init__(self, sock, nickRegisteredCallback):
        Thread.__init__(self)
        self.daemon = True

        self.sock = sock
        self.nickRegisteredCallback = nickRegisteredCallback


    def run(self):
        # The client should send the protocol version its using first
        try:
            message = Message.createFromJSON(self.sock.recv())
        except KeyError:
            printAndLog("%s: send a command with missing JSON fields" % self.sock)
            self.__handleError(errors.ERR_INVALID_COMMAND)
            return

        # Check that the client sent the version command
        if message.serverCommand != constants.COMMAND_VERSION:
            printAndLog("%s: did not send version command" % self.sock)
            self.__handleError(errors.ERR_INVALID_COMMAND)
            return

        # Check the protocol versions match
        if message.payload != constants.PROTOCOL_VERSION:
            printAndLog("%s: is using a mismatched protocol version" % self.sock)
            self.__handleError(errors.ERR_PROTOCOL_VERSION_MISMATCH)
            return

        # The client should then register a nick
        try:
            message = Message.createFromJSON(self.sock.recv())
        except KeyError:
            printAndLog("%s: send a command with missing JSON fields" % self.sock)
            self.__handleError(errors.ERR_INVALID_COMMAND)
            return

        # Check that the client sent the register command
        if message.serverCommand != constants.COMMAND_REGISTER:
            printAndLog("%s: did not register a nick" % self.sock)
            self.__handleError(errors.ERR_INVALID_COMMAND)
            return

        # Check that the nick is valid
        self.nick = message.sourceNick
        if utils.isValidNick(self.nick) != errors.VALID_NICK:
            printAndLog("%s: tried to register an invalid nick" % self.sock)
            self.__handleError(errors.ERR_INVALID_NICK)
            return

        # Check that the nick is not already in use
        self.nick = self.nick.lower()
        if self.nick in nickMap:
            printAndLog("%s: tried to register an in-use nick" % self.sock)
            self.__handleError(errors.ERR_NICK_IN_USE)
            return

        self.nickRegisteredCallback(self.nick)

        while True:
            try:
                try:
                    message = Message.createFromJSON(self.sock.recv())
                except KeyError:
                    printAndLog("%s: send a command with missing JSON fields" % self.sock)
                    self.__handleError(errors.ERR_INVALID_COMMAND)
                    return

                if message.serverCommand == constants.COMMAND_END:
                    printAndLog("%s: requested to end connection" % self.nick)
                    nickMap[self.nick].disconnect()
                    return
                elif message.serverCommand != constants.COMMAND_RELAY:
                    printAndLog("%s: sent invalid command" % self.nick)
                    self.__handleError(errors.ERR_INVALID_COMMAND)
                    return

                try:
                    destNick = message.destNick
                    # Validate the destination nick
                    if utils.isValidNick(destNick) != errors.VALID_NICK:
                        printAndLog("%s: requested to send message to invalid nick" % self.nick)
                        self.__handleError(errors.ERR_INVALID_NICK)

                    client = nickMap[destNick.lower()]

                    # Rewrite the source nick to prevent nick spoofing
                    message.sourceNick = self.nick

                    client.send(message)
                except KeyError:
                    printAndLog("%s: sent message to non-existant nick" % self.nick)
                    self.sock.send(str(Message(serverCommand=constants.COMMAND_ERR, destNick=message.destNick, error=errors.ERR_NICK_NOT_FOUND)))
            except Exception as e:
                if hasattr(e, 'errno') and e.errno != errors.ERR_CLOSED_CONNECTION:
                    printAndLog("%s: error receiving from: %s" % (self.nick, str(e)))

                if self.nick in nickMap:
                    nickMap[self.nick].disconnect()
                return


    def __handleError(self, errorCode):
        self.sock.send(str(Message(serverCommand=constants.COMMAND_ERR, error=errorCode)))
        self.sock.disconnect()

        # Remove the client from the ip or nick maps (it may be in either)
        try:
            del ipMap[str(self.sock)]
            # If found the ip map, don't try to delete from the nick map (it can't be in both)
            return
        except:
            pass
        try:
            del nickMap[self.nick]
        except:
            pass


def printAndLog(message):
    if quiet:
        sys.stdout.write("\b\b\b%s\n>> " % message)
        sys.stdout.flush()

    log(message)


def log(message):
    if logFile is not None:
        logFile.write('%s\n' % message)
        logFile.flush()
