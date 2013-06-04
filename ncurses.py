#! /usr/bin/env python

import sys
import time
import curses
import curses.ascii
import curses.textpad

import utils
import threads
import constants
import _exceptions

from getpass      import getpass
from crypto       import Crypto
from server       import Server
from encSocket    import EncSocket
from cursesDialog import CursesDialog

ACCEPT = 0
REJECT = 1

class NcursesUI():
    def __init__(self, mode, port, host):
        self.mode   = mode
        self.port   = port
        self.host   = host

        curses.wrapper(self.start)

    def start(self, screen):
        self.screen = screen
        (self.height, self.width) = self.screen.getmaxyx()

        # Change the colors, clear the screen and set the overall border
        self.setColors()
        self.screen.clear()
        self.screen.border(0)

        # Create the status and chat input windows
        self.makeChatWindow()
        self.makeStatusWindow()
        self.makeChatInputWindow()
        self.screen.refresh()

        # Try to load a keypair if one was saved or generate a new keypair
        self.loadOrGenerateKepair()

        # Show the options menu
        self.showOptionsMenuWindow(showStartOption=True)

        # Get the server/client mode if not given
        if self.mode == None:
            self.showOptionsWindow()

        if self.mode == constants.SERVER:
            self.startServer()
            self.waitForClient()
        elif self.mode == constants.CLIENT:
            # Get the host if not given
            if self.host == None:
                self.getHost()
            self.connectToServer()

        self.handleNewConnection()


    def waitForClient(self):
        while True:
            # Show the waiting for connections dialog
            dialogWindow = CursesDialog(self.screen, "Waiting for connection...")
            dialogWindow.show()

            self.sock = self.server.accept(self.crypto)

            dialogWindow.hide()

            # Show the accept dialog
            if self.showAcceptWindow() == ACCEPT:
                break
            else:
                self.sock.disconnect()

        # Do the handshake with the client
        try:
            utils.doServerHandshake(self.sock)
        except _exceptions.NetworkError as ne:
            self.sock.disconnect()
            CursesDialog(self.screen, "Network Error", str(ne), isError=True).show()


    def connectToServer(self):
        try:
            dialogWindow = CursesDialog(self.screen, "Connecting to server...", "", False)
            dialogWindow.show()

            self.sock = EncSocket((self.host, self.port), crypto=self.crypto)
            self.sock.connect()
        except _exceptions.GenericError as ge:
            CursesDialog(self.screen, "Error connecting to server", str(ge), isError=True).show()

        # Do the handshake with the client
        try:
            utils.doClientHandshake(self.sock)
            dialogWindow.hide()
        except _exceptions.NetworkError as ne:
            self.sock.disconnect()
            dialogWindow.hide()
            CursesDialog(self.screen, "Network Error", str(ne), isError=True).show()


    def handleNewConnection(self):
        # Set the hostname of who we're connected to in the status window
        self.setStatusWindow()

        # Add a hint on how to display the options menu
        self.screen.addstr(0, 5, "Ctrl+U for options")
        self.screen.refresh()

        # Start the sending and receiving threads
        self.startThreads()

        # Keep the main thread alive so the daemon threads don't die
        while True:
            time.sleep(10)


    def startThreads(self):
        threads.CursesSendThread(self).start()
        threads.CursesRecvThread(self).start()


    def setColors(self):
        if curses.has_colors():
            curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_RED,   curses.COLOR_BLACK)
            curses.init_pair(3, curses.COLOR_CYAN,  curses.COLOR_BLACK)
            curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_GREEN)
            self.screen.bkgd(curses.color_pair(1))


    def showOptionsWindow(self):
        optionsWindow = self.screen.subwin(6, 11, self.height/2 - 3, self.width/2 - 6)
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

            self.screen.refresh()
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

        self.mode = pos


    def showAcceptWindow(self):
        dialogWidth = 23 + len(self.sock.getHostname());
        acceptWindow = self.screen.subwin(6, dialogWidth, self.height/2 - 3, self.width/2 - int(dialogWidth/2))
        acceptWindow.border(0)

        # Enable arrow key detection for this window
        acceptWindow.keypad(True)

        # Disable the cursor
        curses.curs_set(0)

        acceptWindow.addstr(1, 1, "Got connection from %s" % self.host)

        pos = ACCEPT

        while True:
            if pos == ACCEPT:
                acceptWindow.addstr(3, 2, "Accept", curses.color_pair(4))
                acceptWindow.addstr(4, 2, "Reject")
            else:
                acceptWindow.addstr(3, 2, "Accept")
                acceptWindow.addstr(4, 2, "Reject", curses.color_pair(4))

            self.screen.refresh()
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


    def makeChatWindow(self):
        self.chatWindow = self.screen.subwin(self.height-4, self.width-2, 1, 1)
        self.chatWindow.scrollok(True)


    def makeStatusWindow(self):
        self.statusWindow = self.screen.subwin(self.height-3, self.width-23)
        self.statusWindow.border(0)
        self.statusWindow.addstr(1, 1, "Disconnected")


    def makeChatInputWindow(self):
        self.textboxWindow = self.screen.subwin(1, self.width-25, self.height-2, 1)

        self.textbox = curses.textpad.Textbox(self.textboxWindow, insert_mode=True)
        curses.textpad.rectangle(self.screen, self.height-3, 0, self.height-1, self.width-24)
        self.textboxWindow.move(0, 0)


    def getHost(self):
        self.hostWindow = self.screen.subwin(3, 26, self.height/2 - 1, self.width/2 - 13)
        self.hostWindow.border(0)
        self.hostWindow.addstr(1, 1, "Host: ")
        self.hostWindow.refresh()

        # Turn on echo and wait for enter key to read buffer
        curses.echo()
        curses.nocbreak()

        self.host = self.hostWindow.getstr(1, 7)

        # Turn off echo and disable buffering
        curses.cbreak()
        curses.noecho()

        # Get rid of the host window
        self.hostWindow.clear()
        self.screen.refresh()


    def setStatusWindow(self):
        self.statusWindow.clear()
        self.statusWindow.border(0)
        self.statusWindow.addstr(1, 1, self.sock.getHostname())
        self.statusWindow.refresh()


    def startServer(self):
        try:
            self.server = Server()
            self.server.start(int(self.port))
        except _exceptions.NetworkError as ne:
            CursesDialog(screen, "Error starting server", str(ne), isError=True).show()


    def showOptionsMenuWindow(self, showStartOption=False):
        menuWindow = self.screen.subwin((9 if showStartOption else 8), 40, 3, self.width/2 - 20)
        menuWindow.border(0)

        # Enable arrow key detection for this window
        menuWindow.keypad(True)

        pos = 1

        while True:
            # Disable the cursor
            curses.curs_set(0)

            while True:
                menuItem = 1
                if showStartOption:
                    menuWindow.addstr(menuItem, 1, str(menuItem) + ".| Start chat", curses.color_pair(4) if pos == menuItem else curses.color_pair(1))
                    menuItem += 1
                menuWindow.addstr(menuItem, 1, str(menuItem) + ".| Show server fingerprint", curses.color_pair(4) if pos == menuItem else curses.color_pair(1))
                menuItem += 1
                menuWindow.addstr(menuItem, 1, str(menuItem) + ".| Save current keypair", curses.color_pair(4) if pos == menuItem else curses.color_pair(1))
                menuItem += 1
                menuWindow.addstr(menuItem, 1, str(menuItem) + ".| Clear saved keypair", curses.color_pair(4) if pos == menuItem else curses.color_pair(1))
                menuItem += 1
                menuWindow.addstr(menuItem, 1, str(menuItem) + ".| Show help", curses.color_pair(4) if pos == menuItem else curses.color_pair(1))
                menuItem += 1
                menuWindow.addstr(menuItem, 1, str(menuItem) + ".| Close menu", curses.color_pair(4) if pos == menuItem else curses.color_pair(1))
                menuItem += 1
                menuWindow.addstr(menuItem, 1, str(menuItem) + ".| Quit application", curses.color_pair(4) if pos == menuItem else curses.color_pair(1))

                menuWindow.refresh()
                key = menuWindow.getch()
                if key == curses.KEY_DOWN and pos < (7 if showStartOption else 6):
                    pos += 1
                elif key == curses.KEY_UP and pos > 1:
                    pos -= 1
                # Enter key
                elif key == ord('\n'):
                    break

            # Move the selected item by 1 to adjust for the lack of a start option
            if not showStartOption:
                pos += 1

            # Process the selected option
            if pos == 1:
                break
            if pos == 2:
                CursesDialog(self.screen, self.crypto.getLocalFingerprint(), "Server fingerprint", isBlocking=True).show()
            elif pos == 3:
                passphrase = self.getKeypairPassphrase(True)
                utils.saveKeypair(self.crypto, passphrase)
                CursesDialog(self.screen, "This keypair will be used for all subsequent chats", "Keypair Saved", isBlocking=True).show()
            elif pos == 4:
                utils.clearKeypair()
                CursesDialog(self.screen, "Keypair cleared", isBlocking=True).show()
            elif pos == 5:
                CursesDialog(self.screen, "Not implemented yet", isBlocking=True).show()
            elif pos == 6:
                break
            elif pos == 7:
                os.kill(os.getpid(), signal.SIGINT)

            # Shift the selected item position back
            if not showStartOption:
                pos -= 1

        # Re-enable the cursor
        curses.curs_set(2)

        # Get rid of the accept window
        menuWindow.clear()
        menuWindow.refresh()


    def getKeypairPassphrase(self, verify=False):
        passphraseWindow = self.screen.subwin(3, 36, self.height/2 - 1, self.width/2 - 18)

        # Turn on echo and wait for enter key to read buffer
        curses.echo()
        curses.nocbreak()

        while True:
            passphraseWindow.border(0)
            passphraseWindow.addstr(1, 1, "Passphrase: ")
            passphraseWindow.refresh()
            passphrase = getpass('')

            if not verify:
                break

            passphraseWindow.clear()
            passphraseWindow.border(0)
            passphraseWindow.addstr(1, 1, "Verify: ")
            passphraseWindow.refresh()
            verifyPassphrase = getpass('')

            if passphrase == verifyPassphrase:
                break
            else:
                curses.cbreak()
                CursesDialog(self.screen, "Passphrases do not match", '', isBlocking=True).show()
                curses.nocbreak()

        # Turn off echo and disable buffering
        curses.cbreak()
        curses.noecho()

        # Get rid of the passphrase window
        passphraseWindow.clear()
        passphraseWindow.refresh()

        return passphrase


    def loadOrGenerateKepair(self):
        self.crypto = Crypto()
        if utils.doesSavedKeypairExist():
            while(True):
                passphrase = self.getKeypairPassphrase()
                try:
                    utils.loadKeypair(self.crypto, passphrase)
                    break
                except _exceptions.CryptoError:
                    CursesDialog(self.screen, "Wrong passphrase", '', isBlocking=True).show()

            # We still need to generate an AES key
            self.crypto.generateAESKey()
        else:
            self.crypto.generateKeys()


    def stop(self):
        try:
            # If a client is connected, try to end the connection gracefully
            if self.sock.isConnected:
                self.sock.send("__END__")
                self.sock.disconnect()

            if self.server.isStarted:
                self.server.stop()
        except NameError:
            pass
