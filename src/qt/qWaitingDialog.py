import qtUtils

from network import threads

from qLine import QLine

from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui  import QDialog
from PyQt4.QtGui  import QFrame
from PyQt4.QtGui  import QHBoxLayout
from PyQt4.QtGui  import QLabel
from PyQt4.QtGui  import QMovie
from PyQt4.QtGui  import QVBoxLayout

from utils import constants
from utils import utils

class QWaitingDialog(QDialog):
    ipLabelPrefix = "IP address: "
    onCloseSignal = pyqtSignal()

    def __init__(self, parent, text="", isLightTheme=True, onCloseSlot=None, showIP=False):
        QDialog.__init__(self, parent)
        self.onCloseSignal.connect(onCloseSlot)

        # Create connecting image
        connMov = QMovie(utils.getAbsoluteResourcePath('images/' + ('light' if isLightTheme else 'dark') + '/waiting.gif'))
        connMov.start()
        self.connImg = QLabel(self)
        self.connImg.setMovie(connMov)

        # Create connecting and IP address labels
        self.connLabel = QLabel(text, self)
        if showIP:
            self.ipLabel = QLabel(self.ipLabelPrefix + "Getting IP address...", self)
            self.ipHelpLabel = QLabel("Your friend should enter the IP address above as the host to connect to.\n"
                                      "Make sure that port " + str(constants.DEFAULT_PORT) + " is forwarded to "
                                      "this computer. See the help\nfor more info.", self)


        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(self.connImg)
        hbox.addSpacing(10)
        hbox.addWidget(self.connLabel)
        hbox.addStretch(1)

        vbox = QVBoxLayout()
        vbox.addStretch(1)
        vbox.addLayout(hbox)

        if showIP:
            vbox.addSpacing(10)
            vbox.addWidget(QLine())
            vbox.addSpacing(10)
            vbox.addWidget(self.ipLabel)
            vbox.addSpacing(10)
            vbox.addWidget(self.ipHelpLabel)

        vbox.addStretch(1)

        self.setLayout(vbox)

        qtUtils.centerWindow(self, 500 if showIP else 250, 150 if showIP else 100)

        if showIP:
            # Start the thread to get the IP address and update the IP label when finished
            self.ipThread = threads.GetIPAddressThread(self.__setIPAddress, self.__getIPAddressFailure)
            self.ipThread.start()


    def closeEvent(self, event):
        self.onCloseSignal.emit()


    def __setIPAddress(self, ip):
        self.ipLabel.setText(self.ipLabelPrefix + ip)


    def __getIPAddressFailure(self, error):
        self.ipLabel.setText(self.ipLabelPrefix + "Error getting IP address")
