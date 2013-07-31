from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui  import QDialog
from PyQt4.QtGui  import QFrame
from PyQt4.QtGui  import QHBoxLayout
from PyQt4.QtGui  import QLabel
from PyQt4.QtGui  import QMovie
from PyQt4.QtGui  import QVBoxLayout

import qtUtils
from qLine import QLine

from utils import constants


class QWaitingDialog(QDialog):
    def __init__(self, parent, text=""):
        QDialog.__init__(self, parent)

        # Create connecting image
        connMov = QMovie(qtUtils.getAbsoluteImagePath('waiting.gif'))
        connMov.start()
        self.connImg = QLabel(self)
        self.connImg.setMovie(connMov)

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(self.connImg)
        hbox.addSpacing(10)
        hbox.addWidget(self.connLabel)
        hbox.addStretch(1)

        self.setLayout(hbox)
