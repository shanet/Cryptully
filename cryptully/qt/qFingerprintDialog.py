from PyQt4.QtCore import Qt
from PyQt4.QtGui  import QDialog
from PyQt4.QtGui  import QHBoxLayout
from PyQt4.QtGui  import QIcon
from PyQt4.QtGui  import QLabel
from PyQt4.QtGui  import QPixmap
from PyQt4.QtGui  import QVBoxLayout

from qLine import QLine
import qtUtils


class QFingerprintDialog(QDialog):
    def __init__(self, crypto):
        QDialog.__init__(self)

        # Set the title and icon
        self.setWindowTitle("Verify Key Integrity")
        self.setWindowIcon(QIcon(qtUtils.getAbsoluteImagePath('icon.png')))

        keyIcon = QLabel(self)
        keyIcon.setPixmap(QPixmap(qtUtils.getAbsoluteImagePath('fingerprint.png')).scaledToWidth(80, Qt.SmoothTransformation))


        helpLabel = QLabel("In order to ensure that no one is listening in on your conversation it's\n"
                           "best to verify the following information with your friend over a secure\n"
                           "line of communication, like a telephone. It's okay if someone sees or\n"
                           "hears this info; it just matters if what they see here matches what\n"
                           "you see. If not, someone could be listening to your conversation!")

        # Replace the semicolons with spaces to make it look less intimidating
        localFingerprintLabel = QLabel('You read to them: <b>' + crypto.getLocalFingerprint().replace(':', ' ') + '</b>')
        remoteFingerprintLabel = QLabel('They read to you: <b>' + crypto.getRemoteFingerprint().replace(':', ' ') + '</b>')

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(keyIcon)
        hbox.addSpacing(15)
        hbox.addWidget(helpLabel)
        hbox.addStretch(1)

        vbox = QVBoxLayout()
        vbox.addStretch(1)
        vbox.addLayout(hbox)
        vbox.addSpacing(15)
        vbox.addWidget(QLine())
        vbox.addSpacing(15)
        vbox.addWidget(localFingerprintLabel, alignment=Qt.AlignHCenter)
        vbox.addSpacing(10)
        vbox.addWidget(remoteFingerprintLabel, alignment=Qt.AlignHCenter)
        vbox.addStretch(1)

        self.setLayout(vbox)
