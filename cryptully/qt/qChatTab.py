import os
import signal
import sys

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QAction
from PyQt4.QtGui import QHBoxLayout
from PyQt4.QtGui import QStackedWidget
from PyQt4.QtGui import QWidget

import qtUtils
from qChatWidget import QChatWidget
from qConnectingWidget import QConnectingWidget
from qFingerprintDialog import QFingerprintDialog
from qHelpDialog import QHelpDialog
from qNickInputWidget import QNickInputWidget


class QChatTab(QWidget):
    def __init__(self, connectionManager, nick):
        QWidget.__init__(self)

        self.connectionManager = connectionManager
        self.nick = nick

        self.widgetStack = QStackedWidget(self)
        self.widgetStack.addWidget(QNickInputWidget('new_chat.png', 150, self.connectClicked, parent=self))
        self.widgetStack.addWidget(QConnectingWidget(self))
        self.widgetStack.addWidget(QChatWidget(self.connectionManager, self))

        # Skip the chat layout if the nick was given denoting an incoming connection
        if self.nick is None or self.nick == '':
            self.widgetStack.setCurrentIndex(0)
        else:
            self.widgetStack.setCurrentIndex(2)

        layout = QHBoxLayout()
        layout.addWidget(self.widgetStack)
        self.setLayout(layout)


    def connectClicked(self, nick):
        self.nick = nick
        self.widgetStack.widget(1).setConnectingToNick(self.nick)
        self.widgetStack.setCurrentIndex(1)
        self.connectionManager.openChat(self.nick)


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
