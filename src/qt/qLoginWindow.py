import os
import signal

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QDialog
from PyQt4.QtGui import QHBoxLayout
from PyQt4.QtGui import QIcon
from PyQt4.QtGui import QLabel
from PyQt4.QtGui import QLineEdit
from PyQt4.QtGui import QPushButton
from PyQt4.QtGui import QVBoxLayout

from .qNickInputWidget import QNickInputWidget
from .qLinkLabel import QLinkLabel
from . import qtUtils

from utils import constants
from utils import utils

class QLoginWindow(QDialog):
    def __init__(self, parent, nick=""):
        QDialog.__init__(self, parent)
        self.nick = None

        # Set the title and icon
        self.setWindowTitle("Cryptully")
        self.setWindowIcon(QIcon(qtUtils.getAbsoluteImagePath('icon.png')))

        helpLink = QLinkLabel("Confused? Read the docs.", "https://cryptully.readthedocs.org/en/latest/", self)

        vbox = QVBoxLayout()
        vbox.addStretch(1)
        vbox.addWidget(QNickInputWidget('splash_icon.png', 200, self.connectClicked, nick, self))
        vbox.addStretch(1)
        vbox.addWidget(helpLink, alignment=Qt.AlignRight)

        self.setLayout(vbox)

        qtUtils.resizeWindow(self, 500, 200)
        qtUtils.centerWindow(self)


    def connectClicked(self, nick):
        self.nick = nick
        self.close()


    @staticmethod
    def getNick(parent, nick=""):
        if nick is None:
            nick = ""

        loginWindow = QLoginWindow(parent, nick)
        loginWindow.exec_()
        return loginWindow.nick
