import os
import signal
import sys

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QAction
from PyQt4.QtGui import QHBoxLayout
from PyQt4.QtGui import QMessageBox
from PyQt4.QtGui import QStackedWidget
from PyQt4.QtGui import QWidget

from . import qtUtils
from .qChatWidget import QChatWidget
from .qConnectingWidget import QConnectingWidget
from .qHelpDialog import QHelpDialog
from .qNickInputWidget import QNickInputWidget

from utils import errors


class QChatTab(QWidget):
    def __init__(self, chatWindow, nick):
        QWidget.__init__(self)

        self.chatWindow = chatWindow
        self.nick = nick
        self.unreadCount = 0

        self.widgetStack = QStackedWidget(self)
        self.widgetStack.addWidget(QNickInputWidget('new_chat.png', 150, self.connectClicked, parent=self))
        self.widgetStack.addWidget(QConnectingWidget(self))
        self.widgetStack.addWidget(QChatWidget(self.chatWindow.connectionManager, self))

        # Skip the chat layout if the nick was given denoting an incoming connection
        if self.nick is None or self.nick == '':
            self.widgetStack.setCurrentIndex(0)
        else:
            self.widgetStack.setCurrentIndex(2)

        layout = QHBoxLayout()
        layout.addWidget(self.widgetStack)
        self.setLayout(layout)


    def connectClicked(self, nick):
        # Check that the nick isn't already connected
        if self.chatWindow.isNickInTabs(nick):
            QMessageBox.warning(self, errors.TITLE_ALREADY_CONNECTED, errors.ALREADY_CONNECTED % (nick))
            return

        self.nick = nick
        self.widgetStack.widget(1).setConnectingToNick(self.nick)
        self.widgetStack.setCurrentIndex(1)
        self.chatWindow.connectionManager.openChat(self.nick)


    def showNowChattingMessage(self):
        self.widgetStack.setCurrentIndex(2)
        self.widgetStack.widget(2).showNowChattingMessage(self.nick)


    def appendMessage(self, message, source):
        self.widgetStack.widget(2).appendMessage(message, source)


    def resetOrDisable(self):
        # If the connecting widget is showing, reset to the nick input widget
        # If the chat widget is showing, disable it to prevent sending of more messages
        curWidgetIndex = self.widgetStack.currentIndex()
        if curWidgetIndex == 1:
            self.widgetStack.setCurrentIndex(0)
        elif curWidgetIndex == 2:
            self.widgetStack.widget(2).disable()


    def enable(self):
        self.widgetStack.setCurrentIndex(2)
        self.widgetStack.widget(2).enable()
