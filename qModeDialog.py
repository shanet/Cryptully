import os
import signal

import constants
import qtUtils

from PySide.QtGui import QDialog
from PySide.QtGui import QHBoxLayout
from PySide.QtGui import QIcon

from qModeButton import QModeButton

class QModeDialog(QDialog):
    def __init__(self, isLightTheme):
        QDialog.__init__(self)

        self.mode = None

        # Set the title and icon
        self.setWindowTitle("Cryptully")
        self.setWindowIcon(QIcon('images/' + ('light' if isLightTheme else 'dark') + '/icon.png'))

        clientButton = QModeButton("Connect to friend", 'images/client.png', lambda: self.modeSelected(constants.CLIENT), 150, self)
        serverButton = QModeButton("Wait for connection", 'images/server.png', lambda: self.modeSelected(constants.SERVER), 150, self)

        # Center the buttons horizontally
        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(clientButton)
        hbox.addSpacing(45)
        hbox.addWidget(serverButton)
        hbox.addStretch(1)

        self.setLayout(hbox)

        qtUtils.centerWindow(self, 500, 200)


    def modeSelected(self, mode):
        self.mode = mode
        self.close()


    @staticmethod
    def getMode(isLightTheme):
        modeDialog = QModeDialog(isLightTheme)
        modeDialog.exec_()
        return modeDialog.mode
