import curses
import curses.ascii
import curses.textpad
import os
import Queue
import signal
import sys
import time

from getpass import getpass

from cursesAcceptDialog import CursesAcceptDialog
from cursesFingerprintDialog import CursesFingerprintDialog
from cursesDialog import CursesDialog

from network.client import Client
from network import ncursesThreads
from network.connectionManager import ConnectionManager

from threading import Lock
from threading import Thread

from utils import constants
from utils import errors
from utils import exceptions
from utils import utils
from utils.crypto import Crypto

mutex = Lock()

class NcursesUI(object):
    def __init__(self, nick, turn, port):
        self.nick = nick
        self.turn = turn
        self.port = port

        self.connectedNick = None
        self.messageQueue = Queue.Queue()


    def start(self):
        curses.wrapper(self.run)


    def stop(self):
        # If a client is connected, try to end the connection gracefully
        if hasattr(self, 'client'):
            self.client.disconnect()

        if hasattr(self, 'server'):
            self.server.stop()


    def run(self, screen):
        self.screen = screen
        (self.height, self.width) = self.screen.getmaxyx()

        # Change the colors, clear the screen and set the overall border
        self.__setColors()
        self.screen.clear()
        self.screen.border(0)

        # Create the status and chat input windows
        self.makeChatWindow()
        self.makeStatusWindow()
        self.makeChatInputWindow()
        self.screen.refresh()

        # Try to load a keypair if one was saved or generate a new keypair
        self.__loadOrGenerateKepair()

        # Get the nick if not given
        if self.nick == None:
            self.showNickInputDialog()

        self.connectToServer()

        self.__receiveMessageLoop()


    def connectToServer(self):
        # Create the connection manager to manage all communcation to the server
        self.connectionManager = ConnectionManager(self.nick, (self.turn, self.port), self.crypto, self.postMessage, self.newClient, self.clientReady, self.handleError)

        dialogWindow = CursesDialog(self.screen, "Connecting to server...", "", False)
        dialogWindow.show()
        try:
            # TODO: push this to it's own thread
            self.connectionManager.connectToServer()
        except exceptions.GenericError as ge:
            CursesDialog(self.screen, str(ge), "Error connecting to server", isError=True).show()
        finally:
            dialogWindow.hide()


    def postMessage(self, command, sourceNick, payload):
        self.messageQueue.put((command, sourceNick, payload))


    def __receiveMessageLoop(self):
        (height, width) = self.chatWindow.getmaxyx()

        while True:
            message = self.messageQueue.get()
            mutex.acquire()

            # Put the received data in the chat window
            prefix = "(%s) %s: " % (utils.getTimestamp(), message[1])
            self.chatWindow.scroll(1)
            self.chatWindow.addstr(height-1, 0, prefix, curses.color_pair(2))
            self.chatWindow.addstr(height-1, len(prefix), message[2])

            # Move the cursor back to the chat input window
            self.textboxWindow.move(0, 0)

            self.chatWindow.refresh()
            self.textboxWindow.refresh()

            mutex.release()
            self.messageQueue.task_done()


    def newClient(self, nick):
        # Only allow one client (TODO: support multiple clients)
        if self.connectedNick is not None:
            self.connectionManager.newClientRejected(nick)
        

        # Show the accept dialog
        accept = CursesAcceptDialog(self, nick).show()

        if accept == constants.REJECT:
            self.connectionManager.newClientRejected(nick)
            return

        # Set who we're connected to in the status window
        self.setStatusWindow(nick)
        self.connectedNick = nick

        # Add a hint on how to display the options menu
        self.screen.addstr(0, 5, "Ctrl+U for options")
        self.screen.refresh()

        self.connectionManager.newClientAccepted(nick)

        CursesSendThread(self).start()


    def clientReady(self, nick):
        pass


    def handleError(self, nick, errorCode):
        if errorCode == errors.ERR_CONNECTION_ENDED:
            CursesDialog(self.screen, errors.CONNECTION_ENDED % (nick), errors.TITLE_CONNECTION_ENDED, isError=True).show()
        elif errorCode == errors.ERR_NICK_NOT_FOUND:
            CursesDialog(self.screen, errors.NICK_NOT_FOUND % (nick), errors.TITLE_NICK_NOT_FOUND, isError=True).show()
        elif errorCode == errors.ERR_CONNECTION_REJECTED:
            CursesDialog(self.screen, errors.CONNECTION_REJECTED % (nick), errors.TITLE_CONNECTION_REJECTED, isError=True).show()
        elif errorCode == errors.ERR_BAD_HANDSHAKE:
            CursesDialog(self.screen, errors.PROTOCOL_ERROR % (nick), errors.TITLE_PROTOCOL_ERROR, isError=True).show()
        elif errorCode == errors.ERR_CLIENT_EXISTS:
            CursesDialog(self.screen, errors.CLIENT_EXISTS % (nick), errors.TITLE_CLIENT_EXISTS, isError=True).show()
        elif errorCode == errors.ERR_SELF_CONNECT:
            CursesDialog(self.screen, errors.SELF_CONNECT, errors.TITLE_SELF_CONNECT, isError=True).show()
        elif errorCode == errors.ERR_SERVER_SHUTDOWN:
            CursesDialog(self.screen, errors.SERVER_SHUTDOWN, errors.TITLE_SERVER_SHUTDOWN, isError=True).show()
        elif errorCode == errors.ERR_ALREADY_CONNECTED:
            CursesDialog(self.screen, errors.ALREADY_CONNECTED % (nick), errors.TITLE_ALREADY_CONNECTED, isError=True).show()
        elif errorCode == errors.ERR_INVALID_COMMAND:
            CursesDialog(self.screen, errors.INVALID_COMMAND % (nick), errors.TITLE_INVALID_COMMAND, isError=True).show()
        elif errorCode == errors.ERR_NETWORK_ERROR:
            CursesDialog(self.screen, errors.NETWORK_ERROR, errors.TITLE_NETWORK_ERROR, isError=True).show()
        elif errorCode == errors.ERR_BAD_HMAC:
            CursesDialog(self.screen, errors.BAD_HMAC, errors.TITLE_BAD_HMAC, isError=True).show()
        elif errorCode == errors.ERR_BAD_DECRYPT:
            CursesDialog(self.screen, errors.BAD_DECRYPT, errors.TITLE_BAD_DECRYPT, isError=True).show()
        elif errorCode == errors.ERR_KICKED:
            CursesDialog(self.screen, errors.KICKED, errors.TITLE_KICKED, isError=True).show()
        elif errorCode == errors.ERR_NICK_IN_USE:
            CursesDialog(self.screen, errors.NICK_IN_USE, errors.TITLE_NICK_IN_USE, isError=True).show()
        else:
            CursesDialog(self.screen, errors.UNKNOWN_ERROR % (nick), errors.TITLE_UNKNOWN_ERROR, isError=True).show()


    def __setColors(self):
        if curses.has_colors():
            curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_RED,   curses.COLOR_BLACK)
            curses.init_pair(3, curses.COLOR_CYAN,  curses.COLOR_BLACK)
            curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_GREEN)
            self.screen.bkgd(curses.color_pair(1))


    def makeChatWindow(self):
        self.chatWindow = self.screen.subwin(self.height-4, self.width-2, 1, 1)
        self.chatWindow.scrollok(True)


    def makeStatusWindow(self):
        self.statusWindow = self.screen.subwin(self.height-3, self.width-34)
        self.statusWindow.border(0)
        self.statusWindow.addstr(1, 1, "Disconnected")


    def makeChatInputWindow(self):
        self.textboxWindow = self.screen.subwin(1, self.width-35, self.height-2, 1)

        self.textbox = curses.textpad.Textbox(self.textboxWindow, insert_mode=True)
        curses.textpad.rectangle(self.screen, self.height-3, 0, self.height-1, self.width-35)
        self.textboxWindow.move(0, 0)


    def showNickInputDialog(self):
        self.nickInputWindow = self.screen.subwin(3, 42, self.height/2 - 1, self.width/2 - 22)
        self.nickInputWindow.border(0)
        self.nickInputWindow.addstr(1, 1, "Nickname: ")
        self.nickInputWindow.refresh()

        # Turn on echo and wait for enter key to read buffer
        curses.echo()
        curses.nocbreak()

        self.nick = self.nickInputWindow.getstr(1, 11)

        # Turn off echo and disable buffering
        curses.cbreak()
        curses.noecho()

        # Clear the window
        self.nickInputWindow.clear()
        self.nickInputWindow.refresh()


    def setStatusWindow(self, nick):
        self.statusWindow.clear()
        self.statusWindow.border(0)
        self.statusWindow.addstr(1, 1, nick)
        self.statusWindow.refresh()


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
                menuWindow.addstr(menuItem, 1, str(menuItem) + ".| Show public key fingerprints", curses.color_pair(4) if pos == menuItem else curses.color_pair(1))
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
                # Wrap around from top of menu
                elif key == curses.KEY_UP and pos == 1:
                    pos = (7 if showStartOption else 6)
                # Wrap around from bottom of menu
                elif key == curses.KEY_DOWN and pos == (7 if showStartOption else 6):
                    pos = 1
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
                try:
                    CursesFingerprintDialog(self.screen, self.crypto.getLocalFingerprint(), self.crypto.getRemoteFingerprint()).show()
                except exceptions.CryptoError:
                    CursesDialog(self.screen, "Public key(s) not generated/received yet.", isBlocking=True).show()
            elif pos == 3:
                passphrase = self.getKeypairPassphrase(True)
                utils.saveKeypair(self.crypto, passphrase)
                CursesDialog(self.screen, "This keypair will be used for all subsequent chats", "Keypair Saved", isBlocking=True).show()
            elif pos == 4:
                utils.clearKeypair()
                CursesDialog(self.screen, "Keypair cleared", isBlocking=True).show()
            elif pos == 5:
                CursesDialog(self.screen, "Read the docs at https://cryptully.readthedocs.org/en/latest/", isBlocking=True).show()
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
                CursesDialog(self.screen, errors.VERIFY_PASSPHRASE_FAILED, '', isBlocking=True).show()
                curses.nocbreak()

        # Turn off echo and disable buffering
        curses.cbreak()
        curses.noecho()

        # Get rid of the passphrase window
        passphraseWindow.clear()
        passphraseWindow.refresh()

        return passphrase


    def __loadOrGenerateKepair(self):
        self.crypto = Crypto()

        if utils.doesSavedKeypairExist():
            while(True):
                try:
                    utils.loadKeypair(self.crypto, passphrase)
                    break
                except exceptions.CryptoError:
                    CursesDialog(self.screen, errors.BAD_PASSPHRASE, '', isBlocking=True).show()
        else:
            # Only generate an RSA keypair; a unique AES key will be generated later for each client
            self.crypto.generateRSAKeypair()


class CursesSendThread(Thread):
    def __init__(self, ncurses):
        self.ncurses = ncurses

        Thread.__init__(self)
        self.daemon = True


    def run(self):
        (height, width) = self.ncurses.chatWindow.getmaxyx()

        while True:
            chatInput = self.ncurses.textbox.edit(self.inputValidator)

            mutex.acquire()

            # Clear the chat input
            self.ncurses.textboxWindow.deleteln()
            self.ncurses.textboxWindow.move(0, 0)
            self.ncurses.textboxWindow.deleteln()

            # Add the new input to the chat window
            prefix = "(%s) %s: " % (utils.getTimestamp(), self.ncurses.nick)
            self.ncurses.chatWindow.scroll(1)
            self.ncurses.chatWindow.addstr(height-1, 0, prefix, curses.color_pair(3))
            self.ncurses.chatWindow.addstr(height-1, len(prefix), chatInput[:-1])

            # Send the input to the client
            self.ncurses.connectionManager.getClient(self.ncurses.connectedNick).sendChatMessage(chatInput[:-1])

            # Move the cursor back to the chat input window
            self.ncurses.textboxWindow.move(0, 0)

            self.ncurses.chatWindow.refresh()
            self.ncurses.textboxWindow.refresh()

            mutex.release()


    def inputValidator(self, char):
        if char == 21: # Ctrl+U
            self.ncurses.showOptionsMenuWindow()
            return 0
        elif char == curses.KEY_HOME:
            return curses.ascii.SOH
        elif char == curses.KEY_END:
            return curses.ascii.ENQ
        elif char == curses.KEY_ENTER or char == ord('\n'):
             return curses.ascii.BEL
        return char