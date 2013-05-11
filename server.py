#! /usr/bin/env python

import sys
import time
import signal

import utils
import threads
import Crypto
import Exceptions

from Server    import Server
from EncSocket import EncSocket

server = None

def main():
    signal.signal(signal.SIGINT, signalHandler)

    try:
        global server
        server = Server()
        server.startServer(9000)
        print "Server started. Waiting for connections..."
    except Exceptions.GenericError as ge:
        print "Error starting server: " + str(ge)
        sys.exit(1)

    client = server.accept()
    print "Got connection from: " + client.getHostName()

    doHandshake(client)

    threads.SendThread(client).start()
    threads.RecvThread(client).start()

    #while(1):
    #    sys.stdout.write(">>> ")
    #    send(client, raw_input())
    #    print "Response: " + recv(client)

    #client.disconnect()
    #stopServer()


def doHandshake(client):
    # Send the server's public key
    localPubKey = client.crypto.getLocalPubKeyAsString()
    utils.send(client, localPubKey)

    # Receive the client's public key
    remotePubKey = utils.recv(client)
    client.crypto.setRemotePubKey(remotePubKey)

    # Switch to RSA encryption to exchange the AES key, IV, and salt
    client.setEncryptionType(EncSocket.RSA)

    # Send the AES key, IV, and salt
    utils.send(client, client.crypto.aesKey)
    utils.send(client, client.crypto.aesIv)
    utils.send(client, client.crypto.aesSalt)

    # Switch to AES encryption for the remainder of the connection
    client.setEncryptionType(EncSocket.AES)


def stopServer():
    server.stopServer()
    sys.exit(0)


def signalHandler(signal, frame):
    print "Shutting down server..."
    stopServer()


if __name__ == "__main__":
    main()
