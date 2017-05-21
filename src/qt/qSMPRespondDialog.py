import os
import signal

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QDialog
from PyQt4.QtGui import QHBoxLayout
from PyQt4.QtGui import QIcon
from PyQt4.QtGui import QLabel
from PyQt4.QtGui import QLineEdit
from PyQt4.QtGui import QPixmap
from PyQt4.QtGui import QPushButton
from PyQt4.QtGui import QVBoxLayout

from .qLine import QLine
from . import qtUtils

from utils import constants

class QSMPRespondDialog(QDialog):
    def __init__(self, nick, question, parent=None):
        QDialog.__init__(self, parent)

        self.clickedButton = constants.BUTTON_CANCEL

        # Set the title and icon
        self.setWindowTitle("Authenticate %s" % nick)
        self.setWindowIcon(QIcon(qtUtils.getAbsoluteImagePath('icon.png')))

        smpQuestionLabel = QLabel("Question: <b>%s</b>" % question, self)

        smpAnswerLabel = QLabel("Answer (case sensitive):", self)
        self.smpAnswerInput = QLineEdit(self)

        okayButton = QPushButton(QIcon.fromTheme('dialog-ok'), "OK", self)
        cancelButton = QPushButton(QIcon.fromTheme('dialog-cancel'), "Cancel", self)

        keyIcon = QLabel(self)
        keyIcon.setPixmap(QPixmap(qtUtils.getAbsoluteImagePath('fingerprint.png')).scaledToWidth(60, Qt.SmoothTransformation))

        helpLabel = QLabel("%s has requested to authenticate your conversation by asking you a\n"
                           "question only you should know the answer to. Enter your answer below\n"
                           "to authenticate your conversation.\n\n"
                           "You may wish to ask your buddy a question as well." % nick)

        okayButton.clicked.connect(lambda: self.buttonClicked(constants.BUTTON_OKAY))
        cancelButton.clicked.connect(lambda: self.buttonClicked(constants.BUTTON_CANCEL))

        helpLayout = QHBoxLayout()
        helpLayout.addStretch(1)
        helpLayout.addWidget(keyIcon)
        helpLayout.addSpacing(15)
        helpLayout.addWidget(helpLabel)
        helpLayout.addStretch(1)

        # Float the buttons to the right
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(okayButton)
        buttons.addWidget(cancelButton)

        vbox = QVBoxLayout()
        vbox.addLayout(helpLayout)
        vbox.addWidget(QLine())
        vbox.addWidget(smpQuestionLabel)
        vbox.addWidget(smpAnswerLabel)
        vbox.addWidget(self.smpAnswerInput)
        vbox.addLayout(buttons)

        self.setLayout(vbox)


    def buttonClicked(self, button):
        self.smpAnswer = self.smpAnswerInput.text()
        self.clickedButton = button
        self.close()


    @staticmethod
    def getAnswer(nick, question):
        dialog = QSMPRespondDialog(nick, question)
        dialog.exec_()
        return dialog.smpAnswer, dialog.clickedButton
