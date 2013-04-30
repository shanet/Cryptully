#! /usr/bin/env python

import sys
import signal
import Exceptions

from Server import Server

def signalHandler(signal, frame):
    print "Shutting down server..."
    sys.exit(0)


try:
    server = Server()
    server.startServer(9000)
    print "Server started. Waiting for connections..."
except GenericError as ge:
    print "Error starting server: " + str(ge)
    sys.exit(1)


signal.signal(signal.SIGINT, signalHandler)

client = server.accept()
print "Got connection from: " + client.getHostName()

while(1):
    sys.stdout.write(">>> ")
    try:
        client.send(raw_input())
    except Exceptions.NetworkError as ne:
        print "Network error: " + str(ne)
        break

    try:
        print "Response: " + client.recv()
    except Exceptions.NetworkError as ne:
        print "Network error: " + str(ne)
        break

client.disconnect()
