import os
import signal
import sys

import qtUtils
from qFingerprintDialog import QFingerprintDialog

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QFontMetrics
from PyQt4.QtGui import QAction
from PyQt4.QtGui import QHBoxLayout
from PyQt4.QtGui import QIcon
from PyQt4.QtGui import QLabel
from PyQt4.QtGui import QLineEdit
from PyQt4.QtGui import QMainWindow
from PyQt4.QtGui import QMenu
from PyQt4.QtGui import QMessageBox
from PyQt4.QtGui import QPushButton
from PyQt4.QtGui import QSplitter
from PyQt4.QtGui import QTextEdit
from PyQt4.QtGui import QToolButton
from PyQt4.QtGui import QVBoxLayout
from PyQt4.QtGui import QWidget

from utils import constants
from utils import utils


class QChatWindow(QMainWindow):
    def __init__(self, sock, messageQueue, isLightTheme):
        QMainWindow.__init__(self)

        self.sock = sock
        self.messageQueue = messageQueue
        self.isLightTheme = isLightTheme

        self.__setMenubar()

        self.chatLog = QTextEdit()
        self.chatLog.setReadOnly(True)

        self.chatInput = QTextEdit()
        self.chatInput.textChanged.connect(self.chatInputTextChanged)

        self.sendButton = QPushButton("Send")
        self.sendButton.clicked.connect(self.sendMessage)

        # Set the min height for the chatlog and a matching fixed height for the send button
        chatInputFontMetrics = QFontMetrics(self.chatInput.font())
        self.chatInput.setMinimumHeight(chatInputFontMetrics.lineSpacing() * 3)
        self.sendButton.setFixedHeight(chatInputFontMetrics.lineSpacing() * 3)

        hboxLayout = QHBoxLayout()
        hboxLayout.addWidget(self.chatInput)
        hboxLayout.addWidget(self.sendButton)

        # Put the chatinput and send button in a wrapper widget so they may be added to the splitter
        chatInputWrapper = QWidget()
        chatInputWrapper.setLayout(hboxLayout)
        chatInputWrapper.setMinimumHeight(chatInputFontMetrics.lineSpacing() * 3.7)

        # Put the chat log and chat input into a splitter so the user can resize them at will
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.chatLog)
        splitter.addWidget(chatInputWrapper)
        splitter.setSizes([int(self.height()), 1])

        vboxLayout = QVBoxLayout()
        vboxLayout.addWidget(splitter)

        # Add the completeted layout to the window
        self.centralWidget = QWidget()
        self.centralWidget.setLayout(vboxLayout)
        self.setCentralWidget(self.centralWidget)

        qtUtils.centerWindow(self, 700, 400)

        # Title and icon
        self.setWindowTitle("Cryptully")
        self.setWindowIcon(QIcon(utils.getAbosluteResourcePath('images/' + ('light' if isLightTheme else 'dark') + '/icon.png')))
        self.statusBar().showMessage("Connected to 127.0.0.1")


    def showNowChattingMessage(self):
        self.appendMessage("You are now securely chatting with " + self.sock.getHostname() + " :)",
                           constants.SERVICE, showTimestamp=False)

        self.appendMessage("It's a good idea to verify the communcation is secure by selecting"
                           "\"verify identity\" in the options menu.", constants.SERVICE, showTimestamp=False)


    def chatInputTextChanged(self):
        if str(self.chatInput.toPlainText())[-1:] == '\n':
            self.sendMessage()


    def sendMessage(self):
        message = str(self.chatInput.toPlainText())[:-1]

        # Don't send empty messages
        if message == '':
            return

        # Add the message to the message queue to be sent
        self.messageQueue.put(message)

        # Clear the chat input
        self.chatInput.clear()

        self.appendMessage(message, constants.SENDER)


    def appendMessage(self, message, source, showTimestamp=True):
        if showTimestamp:
            timestamp = utils.getTimestamp()
        else:
            timestamp = ''

        color = self.__getColor(source)

        # Append the message to the end of the chat log
        self.chatLog.append(timestamp + '<font color="' + color + '">' + message + "</font>")

        # Move the vertical scrollbar to the bottom of the chat log
        scrollbar = self.chatLog.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum() + scrollbar.pageStep())


    def __getColor(self, source):
        if source == constants.SENDER:
            if self.isLightTheme:
                return '#0000CC'
            else:
                return '#6666FF'
        elif source == constants.RECEIVER:
            if self.isLightTheme:
                return '#CC0000'
            else:
                return '#CC3333'
        else:
            if self.isLightTheme:
                return '#000000'
            else:
                return '#FFFFFF'


    def __setMenubar(self):
        iconPath = 'images/'
        if self.isLightTheme:
            iconPath = iconPath + 'light/'
        else:
            iconPath = iconPath + 'dark/'

        fingerprintIcon = QIcon(utils.getAbosluteResourcePath(iconPath + 'fingerprint.png'))
        saveIcon        = QIcon(utils.getAbosluteResourcePath(iconPath + 'save.png'))
        clearIcon       = QIcon(utils.getAbosluteResourcePath(iconPath + 'delete.png'))
        helpIcon        = QIcon(utils.getAbosluteResourcePath(iconPath + 'help.png'))
        exitIcon        = QIcon(utils.getAbosluteResourcePath(iconPath + 'exit.png'))
        menuIcon        = QIcon(utils.getAbosluteResourcePath(iconPath + 'menu.png'))

        fingerprintAction  = QAction(fingerprintIcon, 'Verify &Identity', self)
        saveKeypairAction  = QAction(saveIcon, '&Save current encryption keys', self)
        clearKeypairAction = QAction(clearIcon, 'C&lear saved encryption keys', self)
        helpAction         = QAction(helpIcon, 'Show &help', self)
        exitAction         = QAction(exitIcon, '&Exit', self)

        fingerprintAction.triggered.connect(self.__showFingerprintDialog)
        saveKeypairAction.triggered.connect(self.__showSaveKeypairDialog)
        clearKeypairAction.triggered.connect(self.__clearKeypair)
        helpAction.triggered.connect(self.__showHelpDialog)
        exitAction.triggered.connect(self.__exit)

        fingerprintAction.setShortcut('Ctrl+I')
        saveKeypairAction.setShortcut('Ctrl+S')
        clearKeypairAction.setShortcut('Ctrl+L')
        helpAction.setShortcut('Ctrl+H')
        exitAction.setShortcut('Ctrl+Q')

        optionsMenu = QMenu()

        optionsMenu.addAction(fingerprintAction)
        optionsMenu.addAction(saveKeypairAction)
        optionsMenu.addAction(clearKeypairAction)
        optionsMenu.addAction(helpAction)
        optionsMenu.addAction(exitAction)

        toolButton = QToolButton()
        toolButton.setIcon(menuIcon)
        toolButton.setMenu(optionsMenu)
        toolButton.setPopupMode(QToolButton.InstantPopup)

        toolbar = self.addToolBar('toolbar')
        toolbar.addWidget(toolButton)


    def __showFingerprintDialog(self):
        QFingerprintDialog(self.sock.crypto).exec_()


    def __showSaveKeypairDialog(self):
        passphrase = qtUtils.getKeypairPassphrase(self, verify=True)
        utils.saveKeypair(self.sock.crypto, passphrase)
        QMessageBox.information(QWidget(), "Keypair saved", "Keypair saved. The current keypair will be used for all subsequent connections.")


    def __clearKeypair(self):
        utils.clearKeypair()
        QMessageBox.information(QWidget(), "Keypair cleared", "Keypair cleared. A new keypair will be generated the next time the app is started.")


    def __showHelpDialog(self):
        QMessageBox.information(QWidget(), "Help", "Help not implemented yet.")

    def __exit(self):
        os.kill(os.getpid(), signal.SIGINT)
