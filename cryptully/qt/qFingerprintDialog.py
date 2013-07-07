import qtUtils

from PyQt4.QtCore import Qt
from PyQt4.QtGui  import QDialog
from PyQt4.QtGui  import QHBoxLayout
from PyQt4.QtGui  import QIcon
from PyQt4.QtGui  import QLabel
from PyQt4.QtGui  import QVBoxLayout

from qLine import QLine


class QFingerprintDialog(QDialog):
    def __init__(self, crypto):
        QDialog.__init__(self)

        # Set the title and icon
        self.setWindowTitle("Verify Key Integrity")
        self.setWindowIcon(QIcon("images/placeholder.png"))

        helpLabel = QLabel("In order to ensure that no one is listening in on your conversation it's\n"
                           "best to verify the following information with your friend over a secure\n"
                           "line of communication, like a telephone. It's okay if someone sees or\n"
                           "hears this info; it just matters if what they see here matches what\n"
                           "you see. If not, someone could be listening to your communcations!")

        localLabel = QLabel("You read to them:")
        localFingerprintLabel = QLabel(crypto.getLocalFingerprint())
        remoteLabel = QLabel("They read to you:")
        remoteFingerprintLabel = QLabel(crypto.getRemoteFingerprint())

        vbox = QVBoxLayout()
        vbox.addStretch(1)
        vbox.addWidget(helpLabel)
        vbox.addSpacing(15)
        vbox.addWidget(QLine())
        vbox.addSpacing(15)
        vbox.addWidget(localLabel)
        vbox.addWidget(localFingerprintLabel, alignment=Qt.AlignHCenter)
        vbox.addSpacing(45)
        vbox.addWidget(remoteLabel)
        vbox.addWidget(remoteFingerprintLabel, alignment=Qt.AlignHCenter)
        vbox.addStretch(1)

        self.setLayout(vbox)
