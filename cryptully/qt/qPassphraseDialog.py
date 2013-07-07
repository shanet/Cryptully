import os
import signal

from PyQt4.QtGui import QDialog
from PyQt4.QtGui import QHBoxLayout
from PyQt4.QtGui import QIcon
from PyQt4.QtGui import QLabel
from PyQt4.QtGui import QLineEdit
from PyQt4.QtGui import QPushButton
from PyQt4.QtGui import QVBoxLayout

import qtUtils

from utils import constants
from utils import utils

class QPassphraseDialog(QDialog):
    def __init__(self, isLightTheme, verify=False, showForgotButton=True):
        QDialog.__init__(self)

        self.passphrase = None
        self.clickedButton = constants.BUTTON_CANCEL

        # Set the title and icon
        self.setWindowTitle("Save Keys Passphrase")
        self.setWindowIcon(QIcon(utils.getAbsoluteResourcePath('images/' + ('light' if isLightTheme else 'dark') + '/icon.png')))

        label = QLabel("Encryption keys passphrase:" if not verify else "Verify:", self)
        self.passphraseInput = QLineEdit(self)
        self.passphraseInput.setEchoMode(QLineEdit.Password)
        okayButton = QPushButton(QIcon.fromTheme('dialog-ok'), "OK", self)
        cancelButton = QPushButton(QIcon.fromTheme('dialog-cancel'), "Cancel", self)

        if showForgotButton:
            forgotButton = QPushButton(QIcon.fromTheme('edit-undo'), "Forgot Passphrase", self)

        okayButton.clicked.connect(lambda: self.buttonClicked(constants.BUTTON_OKAY))
        cancelButton.clicked.connect(lambda: self.buttonClicked(constants.BUTTON_CANCEL))

        if showForgotButton:
            forgotButton.clicked.connect(lambda: self.buttonClicked(constants.BUTTON_FORGOT))

        # Float the buttons to the right
        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(okayButton)
        hbox.addWidget(cancelButton)

        if showForgotButton:
            hbox.addWidget(forgotButton)

        vbox = QVBoxLayout()
        vbox.addStretch(1)
        vbox.addWidget(label)
        vbox.addWidget(self.passphraseInput)
        vbox.addLayout(hbox)
        vbox.addStretch(1)

        self.setLayout(vbox)


    def buttonClicked(self, button):
        self.passphrase = self.passphraseInput.text()
        self.clickedButton = button
        self.close()


    @staticmethod
    def getPassphrase(isLightTheme, verify=False, showForgotButton=True):
        passphraseDialog = QPassphraseDialog(isLightTheme, verify, showForgotButton)
        passphraseDialog.exec_()
        return passphraseDialog.passphrase, passphraseDialog.clickedButton
