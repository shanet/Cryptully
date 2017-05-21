import curses
import curses.ascii
import curses.textpad
import os
import queue
import signal
import sys
import threading
import time

from .cursesAcceptDialog import CursesAcceptDialog
from .cursesDialog import CursesDialog
from .cursesInputDialog import CursesInputDialog
from .cursesModeDialog import CursesModeDialog
from .cursesPassphraseDialog import CursesPassphraseDialog
from .cursesSendThread import CursesSendThread
from .cursesStatusWindow import CursesStatusWindow

from network.client import Client
from network.connectionManager import ConnectionManager

from utils import constants
from utils import errors
from utils import exceptions
from utils import utils


class NcursesUI(object):
    def __init__(self, nick, turn, port):
        self.nick = nick
        self.turn = turn
        self.port = port

        self.connectedNick      = None
        self.inRecveiveLoop     = False
        self.clientConnectError = False
        self.messageQueue       = queue.Queue()
        self.connectionManager  = None
        self.sendThread         = None

        self.errorRaised     = threading.Event()
        self.dialogDismissed = threading.Condition()
        self.clientConnected = threading.Condition()


    def start(self):
        curses.wrapper(self.run)


    def stop(self):
        if self.connectionManager is not None:
            self.connectionManager.disconnectFromServer()

        # Give the send thread time to get the disconnect messages out before exiting
        # and killing the thread
        time.sleep(.25)

        curses.endwin()


    def __restart(self):
        self.__drawUI()

        self.connectedNick      = None
        self.inRecveiveLoop     = False
        self.clientConnectError = False

        self.errorRaised.clear()
        self.postConnectToServer()


    def run(self, screen):
        self.screen = screen
        (self.height, self.width) = self.screen.getmaxyx()

        self.__drawUI()

        # Get the nick if not given
        if self.nick == None:
            self.nick = CursesInputDialog(self.screen, "Nickname: ").show()

        self.__connectToServer()
        self.postConnectToServer()


    def __drawUI(self):
        # Change the colors, clear the screen and set the overall border
        self.__setColors()
        self.screen.clear()
        self.screen.border(0)

        # Create the chat log and chat input windows
        self.makeChatWindow()
        self.makeChatInputWindow()

        self.statusWindow = CursesStatusWindow(self.screen, "Disconnected")
        self.statusWindow.show()
        self.screen.refresh()


    def postConnectToServer(self):
        # Ask if to wait for a connection or connect to someone
        self.mode = CursesModeDialog(self.screen).show()

        # If waiting for a connection, enter the recv loop and start the send thread
        if self.mode == constants.WAIT:
            self.waitingDialog = CursesDialog(self.screen, "Waiting for connection...", '')
            self.waitingDialog.show()
        else:
            # Get the nickname of who to connect to
            while True:
                nick = CursesInputDialog(self.screen, "Nickname: ").show()

                # Don't allow connections to self
                if nick == self.nick:
                    CursesDialog(self.screen, errors.SELF_CONNECT, errors.TITLE_SELF_CONNECT, isError=True, isBlocking=True).show()
                    continue
                if nick == '':
                    CursesDialog(self.screen, errors.EMPTY_NICK, errors.TITLE_EMPTY_NICK, isError=True, isBlocking=True).show()
                    continue

                self.__connectToNick(nick)
                break

        self.__receiveMessageLoop()


    def __connectToServer(self):
        # Create the connection manager to manage all communication to the server
        self.connectionManager = ConnectionManager(self.nick, (self.turn, self.port), self.postMessage, self.newClient, self.clientReady, self.smpRequest, self.handleError)

        dialogWindow = CursesDialog(self.screen, "Connecting to server...", "", False)
        dialogWindow.show()
        try:
            # TODO: push this to it's own thread
            self.connectionManager.connectToServer()
        except exceptions.GenericError as ge:
            dialogWindow.hide()
            CursesDialog(self.screen, str(ge), "Error connecting to server", isError=True, isFatal=True, isBlocking=True).show()
            self.__quitApp()

        dialogWindow.hide()


    def __connectToNick(self, nick):
        connectingDialog = CursesDialog(self.screen, "Connecting to %s..." % nick, "", False)
        connectingDialog.show()
        self.connectionManager.openChat(nick)

        self.clientConnected.acquire()
        self.clientConnected.wait()
        self.clientConnected.release()

        connectingDialog.hide()

        # If there was an error while connecting to the client, restart
        if self.clientConnectError:
            self.__restart()
            return

        self.__startSendThread()


    def postMessage(self, command, sourceNick, payload):
        self.messageQueue.put((command, sourceNick, payload))


    def __receiveMessageLoop(self):
        self.inRecveiveLoop = True

        while True:
            # Keyboard interrupts are ignored unless a timeout is specified
            # See http://bugs.python.org/issue1360
            message = self.messageQueue.get(True, 31536000)

            if self.errorRaised.is_set():
                self.__restart()
                return

            prefix = "(%s) %s: " % (utils.getTimestamp(), message[1])
            self.appendMessage(prefix, message[2], curses.color_pair(2))

            self.messageQueue.task_done()


    def appendMessage(self, prefix, message, color):
        (height, width) = self.chatWindow.getmaxyx()

        # Put the received data in the chat window
        self.chatWindow.scroll(1)
        self.chatWindow.addstr(height-1, 0, prefix, color)
        self.chatWindow.addstr(height-1, len(prefix), message)

        # Move the cursor back to the chat input window
        self.textboxWindow.move(0, 0)

        self.chatWindow.refresh()
        self.textboxWindow.refresh()


    def newClient(self, nick):
        # Only allow one client (TODO: support multiple clients)
        if self.connectedNick is not None or self.mode != constants.WAIT:
            self.connectionManager.newClientRejected(nick)
            return

        self.waitingDialog.hide()

        # Show the accept dialog
        accept = CursesAcceptDialog(self.screen, nick).show()

        if accept == constants.REJECT:
            self.waitingDialog.show()
            self.connectionManager.newClientRejected(nick)
            return

        # Set who we're connected to in the status window
        self.statusWindow.setText(nick)
        self.connectedNick = nick

        self.__startSendThread()

        self.connectionManager.newClientAccepted(nick)


    def __startSendThread(self):
        # Add a hint on how to display the options menu
        self.screen.addstr(0, 5, "Ctrl+U for options")
        self.screen.refresh()

        # Show the now chatting message
        self.appendMessage('', "Now chatting with %s" % self.connectedNick, curses.color_pair(0))

        self.sendThread = CursesSendThread(self)
        self.sendThread.start()


    def clientReady(self, nick):
        self.connectedNick = nick
        self.statusWindow.setText(nick)

        self.clientConnected.acquire()
        self.clientConnected.notify()
        self.clientConnected.release()


    def smpRequest(self, type, nick, question='', errno=0):
        if type == constants.SMP_CALLBACK_REQUEST:
            # Set the SMP request event and pump the message queue to fire it in the UI thread
            self.appendMessage("Chat authentication request (case senstitive):", ' ' + question, curses.color_pair(4))
            self.sendThread.smpRequested.set()
        elif type == constants.SMP_CALLBACK_COMPLETE:
            CursesDialog(self.screen, "Chat with %s authenticated successfully." % nick, isBlocking=True).show()
        elif type == constants.SMP_CALLBACK_ERROR:
            self.handleError(nick, errno)


    def setSmpAnswer(self, answer):
        self.connectionManager.respondSMP(self.connectedNick, answer)


    def handleError(self, nick, errorCode):
        # Stop the send thread after the user presses enter if it is running
        clientConnectError = False
        waiting = False
        if self.sendThread is not None:
            waiting = True
            self.sendThread.stop.set()

        if errorCode == errors.ERR_CONNECTION_ENDED:
            dialog = CursesDialog(self.screen, errors.CONNECTION_ENDED % (nick), errors.TITLE_CONNECTION_ENDED, isError=True)
        elif errorCode == errors.ERR_NICK_NOT_FOUND:
            dialog = CursesDialog(self.screen, errors.NICK_NOT_FOUND % (nick), errors.TITLE_NICK_NOT_FOUND, isError=True)
            clientConnectError = True
        elif errorCode == errors.ERR_CONNECTION_REJECTED:
            dialog = CursesDialog(self.screen, errors.CONNECTION_REJECTED % (nick), errors.TITLE_CONNECTION_REJECTED, isError=True)
            clientConnectError = True
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
        elif errorCode == errors.ERR_SMP_CHECK_FAILED:
            dialog = CursesDialog(self.screen, errors.PROTOCOL_ERROR, errors.TITLE_PROTOCOL_ERROR, isError=True)
        elif errorCode == errors.ERR_SMP_MATCH_FAILED:
            dialog = CursesDialog(self.screen, errors.SMP_MATCH_FAILED_SHORT, errors.TITLE_SMP_MATCH_FAILED, isError=True)
        elif errorCode == errors.ERR_MESSAGE_REPLAY:
            dialog = CursesDialog(self.screen, errors.MESSAGE_REPLAY, errors.TITLE_MESSAGE_REPLAY, isError=True)
        elif errorCode == errors.ERR_MESSAGE_DELETION:
            dialog = CursesDialog(self.screen, errors.MESSAGE_DELETION, errors.TITLE_MESSAGE_DELETION, isError=True)
        elif errorCode == errors.ERR_PROTOCOL_VERSION_MISMATCH:
            dialog = CursesDialog(self.screen, errors.PROTOCOL_VERSION_MISMATCH, errors.TITLE_PROTOCOL_VERSION_MISMATCH, isError=True, isFatal=True)
        else:
            dialog = CursesDialog(self.screen, errors.UNKNOWN_ERROR % (nick), errors.TITLE_UNKNOWN_ERROR, isError=True)

        dialog.show()

        # Wait for the send thread to report that the dialog has been dismissed (enter was pressed)
        # or, if the send thread was not started yet, wait for a key press here
        if waiting:
            self.dialogDismissed.acquire()
            self.dialogDismissed.wait()
            self.dialogDismissed.release()
        else:
            self.screen.getch()

        dialog.hide()

        if dialog.isFatal:
            self.__quitApp()
        elif self.inRecveiveLoop:
            # If not fatal, the UI thread needs to restart, but it's blocked the message queue
            # Set a flag and send an empty message to pump the message queue
            self.errorRaised.set()
            self.postMessage('', '', '')
        elif clientConnectError:
            self.__handleClientConnectingError()
        else:
            self.__restart()


    def __handleClientConnectingError(self):
        self.clientConnectError = True
        self.clientConnected.acquire()
        self.clientConnected.notify()
        self.clientConnected.release()


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


    def makeChatInputWindow(self):
        self.textboxWindow = self.screen.subwin(1, self.width-36, self.height-2, 1)

        self.textbox = curses.textpad.Textbox(self.textboxWindow, insert_mode=True)
        curses.textpad.rectangle(self.screen, self.height-3, 0, self.height-1, self.width-35)
        self.textboxWindow.move(0, 0)


    def showOptionsMenuWindow(self):
        numMenuEntires = 5
        menuWindow = self.screen.subwin(numMenuEntires+2, 34, 3, self.width/2 - 14)

        # Enable arrow key detection for this window
        menuWindow.keypad(True)

        pos = 1

        while True:
            # Redraw the border on each loop in case something is shown on top of this window
            menuWindow.border(0)

            # Disable the cursor
            curses.curs_set(0)

            while True:
                item = 1
                menuWindow.addstr(item, 1, str(item) + ".| End current chat ", curses.color_pair(4) if pos == item else curses.color_pair(1))
                item += 1
                menuWindow.addstr(item, 1, str(item) + ".| Authenticate chat", curses.color_pair(4) if pos == item else curses.color_pair(1))
                item += 1
                menuWindow.addstr(item, 1, str(item) + ".| Show help        ", curses.color_pair(4) if pos == item else curses.color_pair(1))
                item += 1
                menuWindow.addstr(item, 1, str(item) + ".| Close menu       ", curses.color_pair(4) if pos == item else curses.color_pair(1))
                item += 1
                menuWindow.addstr(item, 1, str(item) + ".| Quit application ", curses.color_pair(4) if pos == item else curses.color_pair(1))

                menuWindow.refresh()
                key = menuWindow.getch()
                if key == curses.KEY_DOWN and pos < numMenuEntires:
                    pos += 1
                elif key == curses.KEY_UP and pos > 1:
                    pos -= 1
                # Wrap around from top of menu
                elif key == curses.KEY_UP and pos == 1:
                    pos = numMenuEntires
                # Wrap around from bottom of menu
                elif key == curses.KEY_DOWN and pos == numMenuEntires:
                    pos = 1
                # Enter key
                elif key == ord('\n'):
                    break

            # Process the selected option
            if pos == 1:
                self.connectionManager.closeChat(self.connectedNick)
                menuWindow.clear()
                menuWindow.refresh()
                self.__restart()
            elif pos == 2:
                if self.connectionManager is None:
                    CursesDialog(self.screen, "Chat authentication is not available until you are chatting with someone.", isBlocking=True).show()
                    return

                question = CursesInputDialog(self.screen, "Question: ").show()
                answer = CursesInputDialog(self.screen, "Answer (case senstitive): ").show()

                self.connectionManager.getClient(self.connectedNick).initiateSMP(question, answer)
            elif pos == 3:
                CursesDialog(self.screen, "Read the docs at https://cryptully.readthedocs.org/en/latest/", isBlocking=True).show()
            elif pos == 4:
                # Move the cursor back to the chat input textbox
                self.textboxWindow.move(0, 0)
                break
            elif pos == 5:
                os.kill(os.getpid(), signal.SIGINT)

        # Re-enable the cursor
        curses.curs_set(2)

        # Get rid of the accept window
        menuWindow.clear()
        menuWindow.refresh()


    def __quitApp(self):
        os.kill(os.getpid(), signal.SIGINT)
