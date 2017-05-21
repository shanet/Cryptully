from PyQt4.QtCore import Qt
from PyQt4.QtGui import QHBoxLayout
from PyQt4.QtGui import QLabel
from PyQt4.QtGui import QLineEdit
from PyQt4.QtGui import QMessageBox
from PyQt4.QtGui import QPixmap
from PyQt4.QtGui import QPushButton
from PyQt4.QtGui import QVBoxLayout
from PyQt4.QtGui import QWidget

from . import qtUtils

from utils import constants
from utils import errors
from utils import utils


class QNickInputWidget(QWidget):
    def __init__(self, image, imageWidth, connectClickedSlot, nick='', parent=None):
        QWidget.__init__(self, parent)

        self.connectClickedSlot = connectClickedSlot

        # Image
        self.image = QLabel(self)
        self.image.setPixmap(QPixmap(qtUtils.getAbsoluteImagePath(image)).scaledToWidth(imageWidth, Qt.SmoothTransformation))

        # Nick field
        self.nickLabel = QLabel("Nickname:", self)
        self.nickEdit = QLineEdit(nick, self)
        self.nickEdit.setMaxLength(constants.NICK_MAX_LEN)
        self.nickEdit.returnPressed.connect(self.__connectClicked)
        self.nickEdit.setFocus()

        # Connect button
        self.connectButton = QPushButton("Connect", self)
        self.connectButton.resize(self.connectButton.sizeHint())
        self.connectButton.setAutoDefault(False)
        self.connectButton.clicked.connect(self.__connectClicked)

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(self.nickLabel)
        hbox.addWidget(self.nickEdit)
        hbox.addStretch(1)

        vbox = QVBoxLayout()
        vbox.addStretch(1)
        vbox.addLayout(hbox)
        vbox.addWidget(self.connectButton)
        vbox.addStretch(1)

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(self.image)
        hbox.addSpacing(10)
        hbox.addLayout(vbox)
        hbox.addStretch(1)

        self.setLayout(hbox)


    def __connectClicked(self):
        nick = str(self.nickEdit.text()).lower()

        # Validate the given nick
        nickStatus = utils.isValidNick(nick)
        if nickStatus == errors.VALID_NICK:
            self.connectClickedSlot(nick)
        elif nickStatus == errors.INVALID_NICK_CONTENT:
            QMessageBox.warning(self, errors.TITLE_INVALID_NICK, errors.INVALID_NICK_CONTENT)
        elif nickStatus == errors.INVALID_NICK_LENGTH:
            QMessageBox.warning(self, errors.TITLE_INVALID_NICK, errors.INVALID_NICK_LENGTH)
        elif nickStatus == errors.INVALID_EMPTY_NICK:
            QMessageBox.warning(self, errors.TITLE_EMPTY_NICK, errors.EMPTY_NICK)
