import qtUtils

from PySide.QtCore import Signal
from PySide.QtGui  import QDialog
from PySide.QtGui  import QHBoxLayout
from PySide.QtGui  import QLabel
from PySide.QtGui  import QMovie

class QWaitingDialog(QDialog):
    onCloseSignal = Signal()

    def __init__(self, parent, text="", isLightTheme=True, onCloseSlot=None):
        QDialog.__init__(self, parent)
        self.onCloseSignal.connect(onCloseSlot)

        # Create connecting image
        connMov = QMovie('images/' + ('light' if isLightTheme else 'dark') + '/waiting.gif')
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
