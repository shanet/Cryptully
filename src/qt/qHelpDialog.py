from PyQt4.QtGui import QMessageBox
from PyQt4.QtGui import QIcon
from PyQt4.QtGui import QLabel
from PyQt4.QtGui import QVBoxLayout

from .qLinkLabel import QLinkLabel

class QHelpDialog(QMessageBox):
    def __init__(self, parent=None):
        QMessageBox.__init__(self, parent)

        self.setWindowTitle("Help")

        helpText = QLabel("Questions? There's a whole bunch of info on the documentation page.", self)
        helpLink = QLinkLabel("Read the docs.", "https://cryptully.readthedocs.org/en/latest/", self)

        self.setIcon(QMessageBox.Question)
        self.setStandardButtons(QMessageBox.Ok)

        vbox = QVBoxLayout()
        vbox.addStretch(1)
        vbox.addWidget(helpText)
        vbox.addWidget(helpLink)
        vbox.addStretch(1)

        # Replace the default label with our own custom layout
        layout = self.layout()
        layout.addLayout(vbox, 0, 1)
