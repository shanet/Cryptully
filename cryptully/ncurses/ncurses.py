import curses
import curses.ascii
import curses.textpad
import os
import Queue
import signal
import sys
import threading
import time

from getpass import getpass

from cursesAcceptDialog import CursesAcceptDialog
from cursesDialog import CursesDialog
from cursesFingerprintDialog import CursesFingerprintDialog
from cursesInputDialog import CursesInputDialog
from cursesModeDialog import CursesModeDialog

from network.client import Client
from network.connectionManager import ConnectionManager
from network import ncursesThreads

from utils import constants
from utils import errors
from utils import exceptions
from utils import utils
from utils.crypto import Crypto

mutex = threading.Lock()
dialogDismissed = threading.Condition()

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
        if hasattr(self, 'connectionManager'):
            self.connectionManager.disconnectFromServer()

        # Give the send thread time to get the disconnect messages out before exiting
        # and killing the thread
        time.sleep(.25)

        curses.endwin()


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
            self.nick = CursesInputDialog(self.screen, "Nickname: ").show()

        self.__connectToServer()
        self.postConnectToServer()


    def postConnectToServer(self):
        # Ask if to wait for a connection or connect to someone
        mode = CursesModeDialog(self.screen).show()

        # If waiting for a connection, enter the recv loop and start the send thread
        if mode == constants.WAIT:
            self.waitingDialog = CursesDialog(self.screen, "Waiting for connection...", '')
            self.waitingDialog.show()
            self.__receiveMessageLoop()
        else:
            # Get the nickname of who to connect to
            nick = CursesInputDialog(self.screen, "Nickname: ").show()
            self.__connectToNick(nick)


    def __connectToServer(self):
        # Create the connection manager to manage all communication to the server
        self.connectionManager = ConnectionManager(self.nick, (self.turn, self.port), self.crypto, self.postMessage, self.newClient, self.clientReady, self.handleError)

        dialogWindow = CursesDialog(self.screen, "Connecting to server...", "", False)
        dialogWindow.show()
        try:
            # TODO: push this to it's own thread
            self.connectionManager.connectToServer()
        except exceptions.GenericError as ge:
            dialogWindow.hide()
            CursesDialog(self.screen, str(ge), "Error connecting to server", isError=True, isBlocking=True).show()
            self.__quitApp()
        
        dialogWindow.hide()


    def __connectToNick(self, nick):
        # TODO: handle connecting to a nick
        pass


    def postMessage(self, command, sourceNick, payload):
        self.messageQueue.put((command, sourceNick, payload))


    def __receiveMessageLoop(self):
        while True:
            message = self.messageQueue.get()
            mutex.acquire()

            prefix = "(%s) %s: " % (utils.getTimestamp(), message[1])
            self.__appendMessage(prefix, message[2])

            mutex.release()
            self.messageQueue.task_done()


    def __appendMessage(self, prefix, message):
        (height, width) = self.chatWindow.getmaxyx()

        # Put the received data in the chat window
        self.chatWindow.scroll(1)
        self.chatWindow.addstr(height-1, 0, prefix, curses.color_pair(2))
        self.chatWindow.addstr(height-1, len(prefix), message)

        # Move the cursor back to the chat input window
        self.textboxWindow.move(0, 0)

        self.chatWindow.refresh()
        self.textboxWindow.refresh()


    def newClient(self, nick):
        # Only allow one client (TODO: support multiple clients)
        if self.connectedNick is not None:
            self.connectionManager.newClientRejected(nick)
        
        self.waitingDialog.hide()

        # Show the accept dialog
        accept = CursesAcceptDialog(self.screen, nick).show()

        if accept == constants.REJECT:
            self.waitingDialog.show()
            self.connectionManager.newClientRejected(nick)
            return

        # Set who we're connected to in the status window
        self.setStatusWindow(nick)
        self.connectedNick = nick

        # Add a hint on how to display the options menu
        self.screen.addstr(0, 5, "Ctrl+U for options")
        self.screen.refresh()

        self.sendThread = CursesSendThread(self)
        self.sendThread.start()
        self.connectionManager.newClientAccepted(nick)


    def clientReady(self, nick):
        self.__appendMessage('', "Now chatting with " + nick)


    def handleError(self, nick, errorCode):
        # Stop the send thread after the user presses enter if it is running
        waiting = False
        if hasattr(self, 'sendThread'):
            waiting = True
            self.sendThread.stop.set()

        if errorCode == errors.ERR_CONNECTION_ENDED:
            dialog = CursesDialog(self.screen, errors.CONNECTION_ENDED % (nick), errors.TITLE_CONNECTION_ENDED, isError=True)
        elif errorCode == errors.ERR_NICK_NOT_FOUND:
            dialog = CursesDialog(self.screen, errors.NICK_NOT_FOUND % (nick), errors.TITLE_NICK_NOT_FOUND, isError=True)
        elif errorCode == errors.ERR_CONNECTION_REJECTED:
            dialog = CursesDialog(self.screen, errors.CONNECTION_REJECTED % (nick), errors.TITLE_CONNECTION_REJECTED, isError=True)
        elif errorCode == errors.ERR_BAD_HANDSHAKE:
            dialog = CursesDialog(self.screen, errors.PROTOCOL_ERROR % (nick), errors.TITLE_PROTOCOL_ERROR, isError=True)
        elif errorCode == errors.ERR_CLIENT_EXISTS:
            dialog = CursesDialog(self.screen, errors.CLIENT_EXISTS % (nick), errors.TITLE_CLIENT_EXISTS, isError=True)
        elif errorCode == errors.ERR_SELF_CONNECT:
            dialog = CursesDialog(self.screen, errors.SELF_CONNECT, errors.TITLE_SELF_CONNECT, isError=True)
        elif errorCode == errors.ERR_SERVER_SHUTDOWN:
            dialog = CursesDialog(self.screen, errors.SERVER_SHUTDOWN, errors.TITLE_SERVER_SHUTDOWN, isError=True, isFatal=True)
        elif errorCode == errors.ERR_ALREADY_CONNECTED:
            dialog = CursesDialog(self.screen, errors.ALREADY_CONNECTED % (nick), errors.TITLE_ALREADY_CONNECTED, isError=True)
        elif errorCode == errors.ERR_INVALID_COMMAND:
            dialog = CursesDialog(self.screen, errors.INVALID_COMMAND % (nick), errors.TITLE_INVALID_COMMAND, isError=True)
        elif errorCode == errors.ERR_NETWORK_ERROR:
            dialog = CursesDialog(self.screen, errors.NETWORK_ERROR, errors.TITLE_NETWORK_ERROR, isError=True, isFatal=True)
        elif errorCode == errors.ERR_BAD_HMAC:
            dialog = CursesDialog(self.screen, errors.BAD_HMAC, errors.TITLE_BAD_HMAC, isError=True)
        elif errorCode == errors.ERR_BAD_DECRYPT:
            dialog = CursesDialog(self.screen, errors.BAD_DECRYPT, errors.TITLE_BAD_DECRYPT, isError=True)
        elif errorCode == errors.ERR_KICKED:
            dialog = CursesDialog(self.screen, errors.KICKED, errors.TITLE_KICKED, isError=True)
        elif errorCode == errors.ERR_NICK_IN_USE:
            dialog = CursesDialog(self.screen, errors.NICK_IN_USE, errors.TITLE_NICK_IN_USE, isError=True, isFatal=True)
        else:
            dialog = CursesDialog(self.screen, errors.UNKNOWN_ERROR % (nick), errors.TITLE_UNKNOWN_ERROR, isError=True)

        dialog.show()

        # Wait for the send thread to report that the dialog has been dismissed (enter was pressed)
        # or, if the send thread was not started yet, wait for a key press here
        if waiting:
            dialogDismissed.acquire()
            dialogDismissed.wait()
            dialogDismissed.release()
        else:
            self.screen.getch()

        dialog.hide()

        if dialog.isFatal:
            self.__quitApp()
        else:
            self.connectedNick = None
            self.postConnectToServer()


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


    def setStatusWindow(self, nick):
        self.statusWindow.clear()
        self.statusWindow.border(0)
        self.statusWindow.addstr(1, 1, nick)
        self.statusWindow.refresh()


    def showOptionsMenuWindow(self, showStartOption=False):
        menuWindow = self.screen.subwin((9 if showStartOption else 8), 40, 3, self.width/2 - 20)

        # Enable arrow key detection for this window
        menuWindow.keypad(True)

        pos = 1

        while True:
            # Redraw the border on each loop in case something is shown on top of this window
            menuWindow.border(0)

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


    def __quitApp(self):
        os.kill(os.getpid(), signal.SIGINT)


class CursesSendThread(threading.Thread):
    def __init__(self, ncurses):
        self.ncurses = ncurses
        self.stop = threading.Event()

        threading.Thread.__init__(self)
        self.daemon = True


    def run(self):
        (height, width) = self.ncurses.chatWindow.getmaxyx()

        while True:
            chatInput = self.ncurses.textbox.edit(self.inputValidator)

            if self.stop.is_set():
                dialogDismissed.acquire()
                dialogDismissed.notify()
                dialogDismissed.release()
                return

            self.ncurses.screen.refresh()

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
