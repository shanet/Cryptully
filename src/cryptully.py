#! /usr/bin/env python2.7

import sys
import signal
import argparse

from .utils import constants


turnServer = None
ncursesUI = None
qtUI = None


def main():
    args = parse_cmdline_args()

    signal.signal(signal.SIGINT, signalHandler)

    if args.server:
        from .server.turnServer import TURNServer
        global turnServer

        turnServer = TURNServer(args.port)
        turnServer.start()
    elif args.ncurses:
        from .ncurses.ncurses import NcursesUI
        global ncursesUI

        ncursesUI = NcursesUI(args.nick, args.turn, args.port)
        ncursesUI.start()
    else:
        from .qt.qt import QtUI
        global qtUI

        qtUI = QtUI(sys.argv, args.nick, args.turn, args.port)
        qtUI.start()

    sys.exit(0)


def parse_cmdline_args():
    argvParser = argparse.ArgumentParser()
    argvParser.add_argument('-k', '--nick', dest='nick', nargs='?', type=str, help="Nickname to use.")
    argvParser.add_argument('-r', '--relay', dest='turn', nargs='?', type=str, default=str(constants.DEFAULT_TURN_SERVER), help="The relay server to use.")
    argvParser.add_argument('-p', '--port', dest='port', nargs='?', type=int, default=str(constants.DEFAULT_PORT), help="Port to connect listen on (server) or connect to (client).")
    argvParser.add_argument('-s', '--server', dest='server', default=False, action='store_true', help="Run as TURN server for other clients.")
    argvParser.add_argument('-n', '--ncurses', dest='ncurses', default=False, action='store_true', help="Use the NCurses UI.")

    args = argvParser.parse_args()

    # Check the port range
    if args.port <= 0 or args.port > 65536:
        print("The port must be between 1 and 65536 inclusive.")
        sys.exit(1)

    return args


def signalHandler(signal, frame):
    if turnServer is not None:
        turnServer.stop()
    elif ncursesUI is not None:
        ncursesUI.stop()
    elif qtUI is not None:
        qtUI.stop()

    sys.exit(0)


if __name__ == "__main__":
    main()
