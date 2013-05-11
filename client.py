#! /usr/bin/env python

import sys
import signal
import Exceptions

import utils
import threads
from EncSocket import EncSocket

sock = None

def main():
    signal.signal(signal.SIGINT, signalHandler)

    try:        
        global sock
        sock = EncSocket(('127.0.0.1', 9000))
        sock.connect()
        print "Connecting to server..."
    except Exceptions.GenericError as ge:
        print "Error starting server: " + str(ge)
        sys.exit(1)

    print "Connected to " + sock.getHostName()
    utils.doClientHandshake(sock)

    threads.SendThread(sock).start()
    threads.RecvThread(sock).start()

    #while(1):
    #    print "Response: " + recv(sock)
    #    sys.stdout.write(">>> ")
    #    send(sock, raw_input())

    #sock.disconnect()


def doHandshake(client):
    # Receive the server's public key
    remotePubKey = utils.recv(sock)
    sock.crypto.setRemotePubKey(remotePubKey)

    # Send the client's public key
    localPubKey = sock.crypto.getLocalPubKeyAsString()
    utils.send(sock, localPubKey)

    # Switch to RSA encryption to receive the AES key, IV, and salt
    sock.setEncryptionType(EncSocket.RSA)

    # Receive the AES key, IV, and salt
    sock.crypto.aesKey  = utils.recv(sock)
    sock.crypto.aesIv   = utils.recv(sock)
    sock.crypto.aesSalt = utils.recv(sock)

    # Switch to AES encryption for the remainder of the connection
    sock.setEncryptionType(EncSocket.AES)


def send(sock, data):
    try:
        sock.send(data)
    except Exceptions.NetworkError as ne:
        print ne
        exit()


def recv(sock):
    try:
        return sock.recv()
    except Exceptions.NetworkError as ne:
        print ne
        exit()


def exit():
    sock.disconnect()
    sys.exit(0)


def signalHandler(signal, frame):
    print "Shutting down client..."
    exit()


if __name__ == "__main__":
    main()
