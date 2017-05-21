from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui  import QDialog
from PyQt4.QtGui  import QFrame
from PyQt4.QtGui  import QHBoxLayout
from PyQt4.QtGui  import QLabel
from PyQt4.QtGui  import QMovie
from PyQt4.QtGui  import QVBoxLayout

from . import qtUtils
from .qLine import QLine

from utils import constants


class QWaitingDialog(QDialog):
    def __init__(self, parent, text=""):
        QDialog.__init__(self, parent)

        # Create waiting image
        waitingImage = QMovie(qtUtils.getAbsoluteImagePath('waiting.gif'))
        waitingImage.start()
        waitingImageLabel = QLabel(self)
        waitingImageLabel.setMovie(waitingImage)

        waitingLabel = QLabel(text, self)

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(waitingImageLabel)
        hbox.addSpacing(10)
        hbox.addWidget(waitingLabel)
        hbox.addStretch(1)

        self.setLayout(hbox)
