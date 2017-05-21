#! /usr/bin/env python2.7

import sys

from .tests.mockServer import MockServer
from .tests.mockClient import MockClient, Client1, Client2


def test():
    # Start a server thread to test against
    serverThread = MockServer()
    serverThread.start()

    # Wait for the server to start
    while not hasattr(serverThread.server, 'serversock'):
        pass

    clients = [
        Client1('alice', 'bob'),
        Client2('bob', 'alice'),
    ]

    for client in clients:
        client.start()

    # Wait for each client to finish so we can print exceptions/failures
    for client in clients:
        client.join()

    print('')

    for client in clients:
        client.printExceptions()

    # Exit with failure if any client has exceptions/failures
    for client in clients:
        if len(client.exceptions) > 0:
            sys.exit(1)

    sys.exit(0)

if __name__ == '__main__':
    test()
