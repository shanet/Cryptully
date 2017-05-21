import re

from PyQt4.QtCore import Qt
from PyQt4.QtCore import QTimer
from PyQt4.QtGui import QFontMetrics
from PyQt4.QtGui import QHBoxLayout
from PyQt4.QtGui import QLabel
from PyQt4.QtGui import QPushButton
from PyQt4.QtGui import QSplitter
from PyQt4.QtGui import QTextBrowser
from PyQt4.QtGui import QTextEdit
from PyQt4.QtGui import QWidget

from . import qtUtils

from utils import constants
from utils import utils


class QChatWidget(QWidget):
    def __init__(self, connectionManager, parent=None):
        QWidget.__init__(self, parent)

        self.connectionManager = connectionManager
        self.isDisabled = False
        self.wasCleared = False

        self.urlRegex = re.compile(constants.URL_REGEX)

        self.chatLog = QTextBrowser()
        self.chatLog.setOpenExternalLinks(True)

        self.chatInput = QTextEdit()
        self.chatInput.textChanged.connect(self.chatInputTextChanged)

        self.sendButton = QPushButton("Send")
        self.sendButton.clicked.connect(self.sendMessage)

        # Set the min height for the chatlog and a matching fixed height for the send button
        chatInputFontMetrics = QFontMetrics(self.chatInput.font())
        self.chatInput.setMinimumHeight(chatInputFontMetrics.lineSpacing() * 3)
        self.sendButton.setFixedHeight(chatInputFontMetrics.lineSpacing() * 3)

        hbox = QHBoxLayout()
        hbox.addWidget(self.chatInput)
        hbox.addWidget(self.sendButton)

        # Put the chatinput and send button in a wrapper widget so they may be added to the splitter
        chatInputWrapper = QWidget()
        chatInputWrapper.setLayout(hbox)
        chatInputWrapper.setMinimumHeight(chatInputFontMetrics.lineSpacing() * 3.7)

        # Put the chat log and chat input into a splitter so the user can resize them at will
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.chatLog)
        splitter.addWidget(chatInputWrapper)
        splitter.setSizes([int(parent.height()), 1])

        hbox = QHBoxLayout()
        hbox.addWidget(splitter)
        self.setLayout(hbox)

        self.typingTimer = QTimer()
        self.typingTimer.setSingleShot(True)
        self.typingTimer.timeout.connect(self.stoppedTyping)


    def chatInputTextChanged(self):
        # Check if the text changed was the text box being cleared to avoid sending an invalid typing status
        if self.wasCleared:
            self.wasCleared = False
            return

        if str(self.chatInput.toPlainText())[-1:] == '\n':
            self.sendMessage()
        else:
            # Start a timer to check for the user stopping typing
            self.typingTimer.start(constants.TYPING_TIMEOUT)
            self.sendTypingStatus(constants.TYPING_START)


    def stoppedTyping(self):
        self.typingTimer.stop()
        if str(self.chatInput.toPlainText()) == '':
            self.sendTypingStatus(constants.TYPING_STOP_WITHOUT_TEXT)
        else:
            self.sendTypingStatus(constants.TYPING_STOP_WITH_TEXT)


    def sendMessage(self):
        if self.isDisabled:
            return

        self.typingTimer.stop()

        text = str(self.chatInput.toPlainText())[:-1]

        # Don't send empty messages
        if text == '':
            return

        # Convert URLs into clickable links
        text = self.__linkify(text)

        # Add the message to the message queue to be sent
        self.connectionManager.getClient(self.nick).sendChatMessage(text)

        # Clear the chat input
        self.wasCleared = True
        self.chatInput.clear()

        self.appendMessage(text, constants.SENDER)


    def sendTypingStatus(self, status):
        self.connectionManager.getClient(self.nick).sendTypingMessage(status)


    def showNowChattingMessage(self, nick):
        self.nick = nick
        self.appendMessage("You are now securely chatting with " + self.nick + " :)",
                           constants.SERVICE, showTimestampAndNick=False)

        self.appendMessage("It's a good idea to verify the communcation is secure by selecting "
                           "\"authenticate buddy\" in the options menu.", constants.SERVICE, showTimestampAndNick=False)


    def appendMessage(self, message, source, showTimestampAndNick=True):
        color = self.__getColor(source)

        if showTimestampAndNick:
            timestamp = '<font color="' + color + '">(' + utils.getTimestamp() + ') <strong>' + \
                        (self.connectionManager.nick if source == constants.SENDER else self.nick) + \
                        ':</strong></font> '
        else:
            timestamp = ''

        # If the user has scrolled up (current value != maximum), do not move the scrollbar
        # to the bottom after appending the message
        shouldScroll = True
        scrollbar = self.chatLog.verticalScrollBar()
        if scrollbar.value() != scrollbar.maximum() and source != constants.SENDER:
            shouldScroll = False

        self.chatLog.append(timestamp + message)

        # Move the vertical scrollbar to the bottom of the chat log
        if shouldScroll:
            scrollbar.setValue(scrollbar.maximum())


    def __linkify(self, text):
        matches = self.urlRegex.findall(text)

        for match in matches:
            text = text.replace(match[0], '<a href="%s">%s</a>' % (match[0], match[0]))

        return text


    def __getColor(self, source):
        if source == constants.SENDER:
            if qtUtils.isLightTheme:
                return '#0000CC'
            else:
                return '#6666FF'
        elif source == constants.RECEIVER:
            if qtUtils.isLightTheme:
                return '#CC0000'
            else:
                return '#CC3333'
        else:
            if qtUtils.isLightTheme:
                return '#000000'
            else:
                return '#FFFFFF'


    def disable(self):
        self.isDisabled = True
        self.chatInput.setReadOnly(True)


    def enable(self):
        self.isDisabled = False
        self.chatInput.setReadOnly(False)
