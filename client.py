#! /usr/bin/env python

import sys
import Exceptions

from EncSocket import EncSocket


try:
    sock = EncSocket(('127.0.0.1', 9000))
    sock.connect()
    print "Connecting to server..."
except GenericError as ge:
    print "Error starting server: " + str(ge)
    sys.exit(1)


print "Connected to " + sock.getHostName()

while(1):
    try:
        print "Response: " + sock.recv()
    except Exceptions.NetworkError as ne:
        print "Network error: " + str(ne)
        break

    sys.stdout.write(">>> ")
    try:
        sock.send(raw_input())
    except Exceptions.NetworkError as ne:
        print "Network error: " + str(ne)
        break

sock.disconnect()
