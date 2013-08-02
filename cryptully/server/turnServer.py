import os
import Queue
import signal
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
        global logFile
        try:
            logFile = open('cryptully.log', 'a')
        except:
            logFile = None
            print "Error opening logfile"

        Console().start()
        serversock = self.startServer()

        while True:
            # Wait for a client to connect
            #print "Waiting for client..."
            (clientSock, clientAddr) = serversock.accept()

            # Wrap the socket in our socket object
            clientSock = Socket(clientAddr, clientSock)

            # Store the client's IP and port in the IP map
            printAndLog("Got connection: " + str(clientSock))
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
        for nick, client in nickMap.iteritems():
            client.send(Message(serverCommand=constants.COMMAND_END, destNick=nick, error=errors.ERR_SERVER_SHUTDOWN))

        # Give the send threads time to get their messages out
        time.sleep(.25)

        if logFile is not None:
            logFile.close()


class Console(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True


    def run(self):
        while True:
            input = raw_input(">> ").split()

            if len(input) == 0:
                continue

            command = input[0]

            if command == 'list' or command == 'nicks':
                print "Registered nicks"
                print "================"
                for nick, client in nickMap.iteritems():
                    print nick + " - " + str(client.sock)

            elif command == 'zombies':
                print "Zombie Connections"
                print "=================="
                for addr, client in ipMap.iteritems():
                    print addr

            elif command == 'kick':
                if len(input) != 2:
                    print "Kick command requires an argument"
                else:
                    try:
                        client = nickMap[input[1]]
                        client.kick()
                        print input[1] + " kicked from server"
                    except KeyError:
                        print input[1] + " is not a registered nick"

            elif command == 'kill':
                if len(input) != 2:
                    print "Kill command requires an argument"
                else:
                    try:
                        client = ipMap[input[1]]
                        client.kick()
                        print input[1] + " killed"
                    except KeyError:
                        print input[1] + " is not a zombie"

            elif command == 'stop':
                os.kill(os.getpid(), signal.SIGINT)

            else:
                print "Unrecognized command"


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
        printAndLog(str(self.sock) + " -> " + nick)
        self.nick = nick
        nickMap[nick] = self
        del ipMap[str(self.sock)]


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
        self.queue = Queue.Queue()


    def run(self):
        while True:
            message = self.queue.get()

            try:
                self.sock.send(str(message))
            except Exception as e:
                nick = message.destNick
                printAndLog(nick + ": error sending data to: " + str(e))
                nickMap[nick].disconnect
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
        # The first communcation with the client is registering a nick
        message = Message.createFromJSON(self.sock.recv())

        # Check that the client sent the register command
        if message.serverCommand != constants.COMMAND_REGISTER:
            printAndLog(str(self.sock) + ": did not register a nick")
            self.__handleError(errors.ERR_INVALID_COMMAND)
            return

        # Check that the nick is valid
        if utils.isValidNick(message.sourceNick) != errors.VALID_NICK:
            printAndLog(str(self.sock) + ": tried to register an invalid nick")
            self.__handleError(errors.ERR_INVALID_NICK)
            return

        # Check that the nick is not already in use
        if message.sourceNick in nickMap:
            printAndLog(str(self.sock) + ": tried to register an in-use nick")
            self.__handleError(errors.ERR_NICK_IN_USE)
            return

        self.nick = message.sourceNick
        self.nickRegisteredCallback(message.sourceNick)

        while True:
            try:
                message = Message.createFromJSON(self.sock.recv())
            
                if message.serverCommand == constants.COMMAND_END:
                    printAndLog(self.nick + ": requested to end connection")
                    nickMap[self.nick].disconnect()
                    return
                elif message.serverCommand != constants.COMMAND_RELAY:
                    printAndLog(self.nick + ": sent invalid command")
                    self.__handleError(errors.ERR_INVALID_COMMAND)
                    return

                try:
                    destNick = message.destNick
                    # Validate the destination nick
                    if utils.isValidNick(destNick) != errors.VALID_NICK:
                        printAndLog(self.nick + ": requested to send message to invalid nick")
                        self.__handleError(errors.ERR_INVALID_NICK)
                        
                    client = nickMap[destNick]

                    # Rewrite the nick to prevent nick spoofing
                    message.sourceNick = self.nick

                    client.send(message)
                except KeyError:
                    printAndLog(self.nick + ": sent message to non-existant nick")
                    self.sock.send(str(Message(serverCommand=constants.COMMAND_ERR, destNick=message.destNick, error=errors.ERR_NICK_NOT_FOUND)))
            except Exception as e:
                if hasattr(e, 'errno') and e.errno != errors.ERR_CLOSED_CONNECTION:
                    printAndLog(self.nick + ": error receiving from: " + str(e))

                if self.nick in nickMap:
                    nickMap[self.nick].disconnect()
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


def printAndLog(message):
    sys.stdout.write("\b\b\b" + message + "\n>> ")
    sys.stdout.flush()
    log(message)


def log(message):
    if logFile is not None:
        logFile.write(message + '\n')
        logFile.flush()
