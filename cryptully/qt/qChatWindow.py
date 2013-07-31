import os
import signal
import sys

from PyQt4.QtCore import pyqtSignal
from PyQt4.QtCore import pyqtSlot
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QFontMetrics
from PyQt4.QtGui import QAction
from PyQt4.QtGui import QIcon
from PyQt4.QtGui import QInputDialog
from PyQt4.QtGui import QLabel
from PyQt4.QtGui import QMainWindow
from PyQt4.QtGui import QMenu
from PyQt4.QtGui import QMessageBox
from PyQt4.QtGui import QPushButton
from PyQt4.QtGui import QSplitter
from PyQt4.QtGui import QSystemTrayIcon
from PyQt4.QtGui import QTabWidget
from PyQt4.QtGui import QTextEdit
from PyQt4.QtGui import QToolBar
from PyQt4.QtGui import QToolButton
from PyQt4.QtGui import QVBoxLayout
from PyQt4.QtGui import QWidget

from qChatTab import QChatTab
from qAcceptDialog import QAcceptDialog
from qFingerprintDialog import QFingerprintDialog
from qHelpDialog import QHelpDialog
import qtUtils

from utils import constants
from utils import errors
from utils import utils


class QChatWindow(QMainWindow):
    newClientSignal = pyqtSignal(str)
    clientReadySignal = pyqtSignal(str)
    handleErrorSignal = pyqtSignal(str, int)
    sendMessageToTabSignal = pyqtSignal(str, str, str)

    def __init__(self, connectionManager=None, messageQueue=None):
        QMainWindow.__init__(self)

        self.connectionManager = connectionManager
        self.messageQueue = messageQueue
        self.newClientSignal.connect(self.newClientSlot)
        self.clientReadySignal.connect(self.clientReadySlot)
        self.handleErrorSignal.connect(self.handleErrorSlot)
        self.sendMessageToTabSignal.connect(self.sendMessageToTab)

        self.chatTabs = QTabWidget(self)
        self.chatTabs.setTabsClosable(True)
        self.chatTabs.setMovable(True)
        self.chatTabs.tabCloseRequested.connect(self.closeTab)
        self.chatTabs.currentChanged.connect(self.tabChanged)

        self.systemTrayIcon = QSystemTrayIcon(self)

        self.__setMenubar()

        vbox = QVBoxLayout()
        vbox.addWidget(self.chatTabs)

        # Add the completeted layout to the window
        self.centralWidget = QWidget()
        self.centralWidget.setLayout(vbox)
        self.setCentralWidget(self.centralWidget)

        qtUtils.resizeWindow(self, 700, 400)
        qtUtils.centerWindow(self)

        # Title and icon
        self.setWindowTitle("Cryptully")
        self.setWindowIcon(QIcon(qtUtils.getAbsoluteImagePath('icon.png')))


    def connectedToServer(self):
        # Add an initial tab once connected to the server
        self.addNewTab()


    def newClient(self, message):
        # This function is called from a bg thread. Send a signal to get on the UI thread
        self.newClientSignal.emit(message)


    @pyqtSlot(str)
    def newClientSlot(self, nick):
        nick = str(nick)

        # Show the accept dialog
        accept = QAcceptDialog.getAnswer(self, nick)

        if not accept:
            self.connectionManager.newClientRejected(nick)
            return

        # If nick already has a tab, reuse it
        if self.isNickInTabs(nick):
            self.getTabByNick(nick)[0].enable()
        else:
            self.addNewTab(nick)

        self.connectionManager.newClientAccepted(nick)


    def addNewTab(self, nick=None):
        newTab = QChatTab(self, nick)
        self.chatTabs.addTab(newTab, nick if nick is not None else "New Chat")
        self.chatTabs.setCurrentWidget(newTab)


    def clientReady(self, nick):
        # Use a signal to call the client ready slot on the UI thread since
        # this function is called from a background thread
        self.clientReadySignal.emit(nick)


    @pyqtSlot(str)
    def clientReadySlot(self, nick):
        nick = str(nick)
        tab, tabIndex = self.getTabByNick(nick)
        self.chatTabs.setTabText(tabIndex, nick)
        tab.showNowChattingMessage()


    def handleError(self, nick, errorCode):
        self.handleErrorSignal.emit(nick, errorCode)


    @pyqtSlot(str, int)
    def handleErrorSlot(self, nick, errorCode):
        nick = str(nick)
        tab = self.getTabByNick(nick)[0]
        tab.resetOrDisable()

        if errorCode == errors.ERR_CONNECTION_ENDED:
            QMessageBox.warning(self, errors.TITLE_CONNECTION_ENDED, errors.CONNECTION_ENDED % (nick))
        elif errorCode == errors.ERR_NICK_NOT_FOUND:
            QMessageBox.warning(self, errors.TITLE_NICK_NOT_FOUND, errors.NICK_NOT_FOUND)
        elif errorCode == errors.ERR_CONNECTION_REJECTED:
            QMessageBox.warning(self, errors.TITLE_CONNECTION_REJECTED, errors.CONNECTION_REJECTED % (nick))
            tab.nick = None
        elif errorCode == errors.ERR_BAD_HANDSHAKE:
            QMessageBox.warning(self, errors.TITLE_PROTOCOL_ERROR, errors.PROTOCOL_ERROR)
        elif errorCode == errors.ERR_CLIENT_EXISTS:
            QMessageBox.warning(self, errors.TITLE_CLIENT_EXISTS, errors.CLIENT_EXISTS % (nick))
        elif errorCode == errors.ERR_SELF_CONNECT:
            QMessageBox.warning(self, errors.TITLE_SELF_CONNECT, errors.SELF_CONNECT)
        elif errorCode == errors.ERR_SERVER_SHUTDOWN:
            QMessageBox.critical(self, errors.TITLE_SERVER_SHUTDOWN, errors.SELF_SERVER_SHUTDOWN)
        elif errorCode == errors.ERR_ALREADY_CONNECTED:
            QMessageBox.warning(self, errors.TITLE_ALREADY_CONNECTED, errors.ALREADY_CONNECTED % (nick))
        elif errorCode == errors.ERR_INVALID_COMMAND:
            QMessageBox.warning(self, errors.TITLE_INVALID_COMMAND, errors.INVALID_COMMAND % (nick))
        else:
            QMessageBox.warning(self, errors.TITLE_UNKNOWN_ERROR, errors.UNKNOWN_ERROR % (nick))


    def postMessage(self, command, sourceNick, payload):
        self.sendMessageToTabSignal.emit(command, sourceNick, payload)


    @pyqtSlot(str, str, str)
    def sendMessageToTab(self, command, sourceNick, payload):
        self.getTabByNick(sourceNick)[0].appendMessage(payload, constants.RECEIVER)

        # Update the unread message count if the message is not intended for the currently selected tab
        tab, tabIndex = self.getTabByNick(sourceNick)
        if tabIndex != self.chatTabs.currentIndex():
            tab.unreadCount += 1
            self.chatTabs.setTabText(tabIndex, tab.nick + (" (%d)" % tab.unreadCount))

            # Show a system notifcation of the new message
            self.systemTrayIcon.setVisible(True)
            self.systemTrayIcon.showMessage(sourceNick, payload)


    @pyqtSlot(int)
    def tabChanged(self, index):
        # Reset the unread count for the tab when it's switched to
        tab = self.chatTabs.widget(index)
        if tab.unreadCount != 0:
            tab.unreadCount = 0
            self.chatTabs.setTabText(index, tab.nick)


    @pyqtSlot(int)
    def closeTab(self, index):
        tab = self.chatTabs.widget(index)
        self.connectionManager.closeChat(tab.nick)

        self.chatTabs.removeTab(index)

        # Show a new tab if there are now no tabs left
        if self.chatTabs.count() == 0:
            self.addNewTab()


    def getTabByNick(self, nick):
        for i in range(0, self.chatTabs.count()):
            curTab = self.chatTabs.widget(i)
            if curTab.nick == nick:
                return (curTab, i)
        return None


    def isNickInTabs(self, nick):
        for i in range(0, self.chatTabs.count()):
            curTab = self.chatTabs.widget(i)
            if curTab.nick == nick:
                return True
        return False


    def __setMenubar(self):
        newChatIcon     = QIcon(qtUtils.getAbsoluteImagePath('new_chat.png'))
        fingerprintIcon = QIcon(qtUtils.getAbsoluteImagePath('fingerprint.png'))
        saveIcon        = QIcon(qtUtils.getAbsoluteImagePath('save.png'))
        clearIcon       = QIcon(qtUtils.getAbsoluteImagePath('delete.png'))
        helpIcon        = QIcon(qtUtils.getAbsoluteImagePath('help.png'))
        exitIcon        = QIcon(qtUtils.getAbsoluteImagePath('exit.png'))
        menuIcon        = QIcon(qtUtils.getAbsoluteImagePath('menu.png'))

        newChatAction      = QAction(newChatIcon, '&New chat', self)
        fingerprintAction  = QAction(fingerprintIcon, '&Verify key integrity', self)
        saveKeypairAction  = QAction(saveIcon, '&Save current encryption keys', self)
        clearKeypairAction = QAction(clearIcon, 'C&lear saved encryption keys', self)
        helpAction         = QAction(helpIcon, 'Show &help', self)
        exitAction         = QAction(exitIcon, '&Exit', self)

        newChatAction.triggered.connect(lambda: self.addNewTab())
        fingerprintAction.triggered.connect(self.__showFingerprintDialog)
        saveKeypairAction.triggered.connect(self.__showSaveKeypairDialog)
        clearKeypairAction.triggered.connect(self.__clearKeypair)
        helpAction.triggered.connect(self.__showHelpDialog)
        exitAction.triggered.connect(self.__exit)

        newChatAction.setShortcut('Ctrl+N')
        fingerprintAction.setShortcut('Ctrl+I')
        saveKeypairAction.setShortcut('Ctrl+S')
        clearKeypairAction.setShortcut('Ctrl+L')
        helpAction.setShortcut('Ctrl+H')
        exitAction.setShortcut('Ctrl+Q')

        optionsMenu = QMenu()

        optionsMenu.addAction(newChatAction)
        optionsMenu.addAction(fingerprintAction)
        optionsMenu.addAction(saveKeypairAction)
        optionsMenu.addAction(clearKeypairAction)
        optionsMenu.addAction(helpAction)
        optionsMenu.addAction(exitAction)

        optionsMenuButton = QToolButton()
        newChatButton     = QToolButton()
        fingerprintButton = QToolButton()
        exitButton        = QToolButton()

        newChatButton.clicked.connect(lambda: self.addNewTab())
        fingerprintButton.clicked.connect(self.__showFingerprintDialog)
        exitButton.clicked.connect(self.__exit)

        optionsMenuButton.setIcon(menuIcon)
        newChatButton.setIcon(newChatIcon)
        fingerprintButton.setIcon(fingerprintIcon)
        exitButton.setIcon(exitIcon)

        optionsMenuButton.setMenu(optionsMenu)
        optionsMenuButton.setPopupMode(QToolButton.InstantPopup)

        toolbar = QToolBar(self)
        toolbar.addWidget(optionsMenuButton)
        toolbar.addWidget(newChatButton)
        toolbar.addWidget(fingerprintButton)
        toolbar.addWidget(exitButton)
        self.addToolBar(Qt.LeftToolBarArea, toolbar)


    def __showFingerprintDialog(self):
        try:
            crypto = self.connectionManager.getClient(self.chatTabs.currentWidget().nick).crypto
            QFingerprintDialog(crypto).exec_()
        except AttributeError:
            QMessageBox.information(self, "Not Available", "Encryption keys are not available until you are chatting with someone")


    def __showSaveKeypairDialog(self):
        if utils.doesSavedKeypairExist():
            QMessageBox.warning(self, "Keys Already Saved", "The current encryption keys have already been saved")
            return

        QMessageBox.information(self, "Save Keys", "For extra security, your encryption keys will be protected with a passphrase. You'll need to enter this each time you start the app")
        passphrase = qtUtils.getKeypairPassphrase(self, verify=True, showForgotButton=False)

        # Return if the user did not provide a passphrase
        if passphrase is None:
            return

        utils.saveKeypair(self.connectionManager.getClient(self.nick).sock.crypto, passphrase)
        QMessageBox.information(self, "Keys Saved", "Encryption keys saved. The current keys will be used for all subsequent connections")


    def __clearKeypair(self):
        qtUtils.clearKeypair(self)


    def __showHelpDialog(self):
        QHelpDialog(self).show()


    def __exit(self):
        if QMessageBox.question(self, "Confirm Exit", "Are you sure you want to exit?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No):
            qtUtils.exitApp()
