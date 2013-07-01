import qtUtils

from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui  import QDialog
from PyQt4.QtGui  import QHBoxLayout
from PyQt4.QtGui  import QLabel
from PyQt4.QtGui  import QMovie

from utils import utils

class QWaitingDialog(QDialog):
    onCloseSignal = pyqtSignal()

    def __init__(self, parent, text="", isLightTheme=True, onCloseSlot=None):
        QDialog.__init__(self, parent)
        self.onCloseSignal.connect(onCloseSlot)

        # Create connecting image
        connMov = QMovie(utils.getAbosluteResourcePath('images/' + ('light' if isLightTheme else 'dark') + '/waiting.gif'))
        connMov.start()
        self.connImg = QLabel(self)
        self.connImg.setMovie(connMov)

        # Create host label and text edit
        self.connLabel = QLabel(text, self)

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(self.connImg)
        hbox.addSpacing(10)
        hbox.addWidget(self.connLabel)
        hbox.addStretch(1)

        self.setLayout(hbox)

        qtUtils.centerWindow(self, 250, 100)


    def closeEvent(self, event):
        self.onCloseSignal.emit()
