from PyQt4.QtCore import Qt
from PyQt4.QtGui import QHBoxLayout
from PyQt4.QtGui import QLabel
from PyQt4.QtGui import QMovie
from PyQt4.QtGui import QWidget

from . import qtUtils


class QConnectingWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        # Create connecting image
        self.connectingGif = QMovie(qtUtils.getAbsoluteImagePath('waiting.gif'))
        self.connectingGif.start()
        self.connetingImageLabel = QLabel(self)
        self.connetingImageLabel.setMovie(self.connectingGif)
        self.connectingLabel = QLabel(self)

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(self.connetingImageLabel, alignment=Qt.AlignCenter)
        hbox.addSpacing(10)
        hbox.addWidget(self.connectingLabel, alignment=Qt.AlignCenter)
        hbox.addStretch(1)

        self.setLayout(hbox)


    def setConnectingToNick(self, nick):
        self.connectingLabel.setText("Connecting to " + nick + "...")
