#! /usr/bin/env python

import sys
import time
import signal
import curses
import curses.ascii
import curses.textpad

import utils
import threads
import constants
import _exceptions

from crypto       import Crypto
from server       import Server
from encSocket    import EncSocket
from cursesDialog import CursesDialog

ACCEPT = 0
REJECT = 1


def main(screen, mode, port, host):
    (height, width) = screen.getmaxyx()

    # Change the colors, clear the screen and set the overall border
    setColors(screen)
    screen.clear()
    screen.border(0)

    # Create the status and chat input windows
    chatWindow               = makeChatWindow(screen)
    statusWindow             = makeStatusWindow(screen)
    (textboxWindow, textbox) = makeChatInputWindow(screen)
    screen.refresh()

    # Try to load a keypair if one was saved or generate a new keypair
    crypto = utils.loadOrGenerateKepair(screen)

    # Show the options menu
    utils.showOptionsMenuWindow(screen, crypto, showStartOption=True)

    # Get the server/client mode if not given
    if mode == None:
        mode = showOptionsWindow(screen)

    context = {'host': host, 'port': port, 'mode': mode, 'chatWindow': chatWindow,
               'statusWindow': statusWindow, 'textboxWindow': textboxWindow,
               'textbox': textbox, 'screen': screen, 'crypto': crypto}

    if mode == constants.SERVER:
        context['server'] = startServer(screen, port)
        waitForClient(context)
    elif mode == constants.CLIENT:
        # Get the host if not given
        if context['host'] == None:
            context['host'] = getHost(screen)
        connectToServer(context)


def waitForClient(context):
    while True:
        # Show the waiting for connections dialog
        dialogWindow = CursesDialog(context['screen'], "Waiting for connection...")
        dialogWindow.show()

        global sock
        sock = context['server'].accept(context['crypto'])
        context['sock'] = sock

        dialogWindow.hide()

        # Show the accept dialog
        if showAcceptWindow(context['screen'], sock.getHostname()) == ACCEPT:
            break
        else:
            sock.disconnect()

    # Do the handshake with the client
    try:
        utils.doServerHandshake(sock)
    except _exceptions.NetworkError as ne:
        sock.disconnect()
        CursesDialog(context['chatWindow'], "Network Error", str(ne), isError=True).show()

    handleNewConnection(context)


def connectToServer(context):
    try:
        dialogWindow = CursesDialog(context['screen'], "Connecting to server...", "", False)
        dialogWindow.show()

        sock = EncSocket((context['host'], context['port']), crypto=context['crypto'])
        sock.connect()
        context['sock'] = sock
    except _exceptions.GenericError as ge:
        CursesDialog(screen, "Error connecting to server", str(ge), isError=True).show()

    # Do the handshake with the client
    try:
        utils.doClientHandshake(sock)
        dialogWindow.hide()
    except _exceptions.NetworkError as ne:
        sock.disconnect()
        dialogWindow.hide()
        CursesDialog(context['chatWindow'], "Network Error", str(ne), isError=True).show()

    handleNewConnection(context)


def handleNewConnection(context):
    # Set the hostname of who we're connected to in the status window
    setStatusWindow(context['statusWindow'], context['sock'].getHostname())

    # Add a hint on how to display the options menu
    context['screen'].addstr(0, 5, "Ctrl+U for options")
    context['screen'].refresh()

    # Start the sending and receiving threads
    startThreads(context['screen'], context['sock'], context['chatWindow'], context['textboxWindow'], context['textbox'])

    # Keep the main thread alive so the daemon threads don't die
    while True:
        time.sleep(10)


def startThreads(screen, sock, chatWindow, textboxWindow, textbox):
    threads.CursesSendThread(sock, screen, chatWindow, textboxWindow, textbox).start()
    threads.CursesRecvThread(sock, screen, chatWindow, textboxWindow).start()


def setColors(screen):
    if curses.has_colors():
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED,   curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_CYAN,  curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_GREEN)
        screen.bkgd(curses.color_pair(1))


def showOptionsWindow(screen):
    (height, width) = screen.getmaxyx()
    optionsWindow = screen.subwin(6, 11, height/2 - 3, width/2 - 6)
    optionsWindow.border(0)

    # Enable arrow key detection for this window
    optionsWindow.keypad(True)

    # Disable the cursor
    curses.curs_set(0)

    optionsWindow.addstr(1, 1, "Run as:")

    pos = constants.SERVER

    while True:
        if pos == constants.SERVER:
            optionsWindow.addstr(3, 2, "Server", curses.color_pair(4))
            optionsWindow.addstr(4, 2, "Client")
        else:
            optionsWindow.addstr(3, 2, "Server")
            optionsWindow.addstr(4, 2, "Client", curses.color_pair(4))

        screen.refresh()
        key = optionsWindow.getch()
        if key == curses.KEY_DOWN and pos == constants.SERVER:
            pos = constants.CLIENT
        elif key == curses.KEY_UP and pos == constants.CLIENT:
            pos = constants.SERVER
        # Enter key
        elif key == ord('\n'):
            break

    # Re-enable the cursor
    curses.curs_set(2)

    # Get rid of the options window
    optionsWindow.clear()
    optionsWindow.refresh()

    return pos


def showAcceptWindow(screen, hostname):
    (height, width) = screen.getmaxyx()
    dialogWidth = 23 + len(hostname);
    acceptWindow = screen.subwin(6, dialogWidth, height/2 - 3, width/2 - int(dialogWidth/2))
    acceptWindow.border(0)

    # Enable arrow key detection for this window
    acceptWindow.keypad(True)

    # Disable the cursor
    curses.curs_set(0)

    acceptWindow.addstr(1, 1, "Got connection from %s" % hostname)

    pos = ACCEPT

    while True:
        if pos == ACCEPT:
            acceptWindow.addstr(3, 2, "Accept", curses.color_pair(4))
            acceptWindow.addstr(4, 2, "Reject")
        else:
            acceptWindow.addstr(3, 2, "Accept")
            acceptWindow.addstr(4, 2, "Reject", curses.color_pair(4))

        screen.refresh()
        key = acceptWindow.getch()
        if key == curses.KEY_DOWN and pos == ACCEPT:
            pos = REJECT
        elif key == curses.KEY_UP and pos == REJECT:
            pos = ACCEPT
        # Enter key
        elif key == ord('\n'):
            break

    # Re-enable the cursor
    curses.curs_set(2)

    # Get rid of the accept window
    acceptWindow.clear()
    acceptWindow.refresh()

    return pos


def makeChatWindow(screen):
    (height, width) = screen.getmaxyx()
    chatWindow = screen.subwin(height-4, width-2, 1, 1)
    chatWindow.scrollok(True)
    return chatWindow


def makeStatusWindow(screen):
    (height, width) = screen.getmaxyx()
    statusWindow = screen.subwin(height-3, width-23)
    statusWindow.border(0)
    statusWindow.addstr(1, 1, "Disconnected")
    return statusWindow


def makeChatInputWindow(screen):
    (height, width) = screen.getmaxyx()
    textboxWindow = screen.subwin(1, width-25, height-2, 1)

    textbox = curses.textpad.Textbox(textboxWindow, insert_mode=True)
    curses.textpad.rectangle(screen, height-3, 0, height-1, width-24)
    textboxWindow.move(0, 0)
    return (textboxWindow, textbox)


def getHost(screen):
    (height, width) = screen.getmaxyx()
    hostWindow = screen.subwin(3, 26, height/2 - 1, width/2 - 13)
    hostWindow.border(0)
    hostWindow.addstr(1, 1, "Host: ")
    hostWindow.refresh()

    # Turn on echo and wait for enter key to read buffer
    curses.echo()
    curses.nocbreak()

    host = hostWindow.getstr(1, 7)

    # Turn off echo and disable buffering
    curses.cbreak()
    curses.noecho()

    # Get rid of the host window
    hostWindow.clear()
    screen.refresh()

    return host


def setStatusWindow(statusWindow, hostname):
    statusWindow.clear()
    statusWindow.border(0)
    statusWindow.addstr(1, 1, hostname)
    statusWindow.refresh()


def startServer(screen, port):
    try:
        global server
        server = Server()
        server.start(int(port))
    except _exceptions.NetworkError as ne:
        CursesDialog(screen, "Error starting server", str(ne), isError=True).show()

    return server


def signalHandler(signal, frame):
    exit()


def exit():
    try:
        # If a client is connected, try to end the connection gracefully
        if sock.isConnected:
            sock.send("__END__")
            sock.disconnect()

        if server.isStarted:
            server.stop()
    except NameError:
        pass
    sys.exit(0)


def start(mode, port, host):
    signal.signal(signal.SIGINT, signalHandler)
    curses.wrapper(main, mode, port, host)
