from PySide.QtCore import Qt
from PySide.QtGui import QGroupBox
from PySide.QtGui import QHBoxLayout
from PySide.QtGui import QLabel
from PySide.QtGui import QPixmap
from PySide.QtGui import QPushButton
from PySide.QtGui import QVBoxLayout
from PySide.QtGui import QWidget

class QModeButton(QWidget):
    def __init__(self, buttonText, imagePath, buttonCallback, imageSize, parent=None):
        QWidget.__init__(self, parent)

        icon = QLabel(self)
        icon.setPixmap(QPixmap(imagePath).scaled(imageSize, imageSize))

        button = QPushButton(buttonText)
        button.clicked.connect(buttonCallback)

        vbox = QVBoxLayout()
        vbox.addStretch(1)
        vbox.addWidget(icon, alignment=Qt.AlignHCenter)
        vbox.addSpacing(20)
        vbox.addWidget(button)
        vbox.addStretch(1)

        # Add some horizontal padding
        hbox = QHBoxLayout()
        hbox.addSpacing(10)
        hbox.addLayout(vbox)
        hbox.addSpacing(10)

        groupBox = QGroupBox()
        groupBox.setLayout(hbox)

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(groupBox)
        hbox.addStretch(1)

        self.setLayout(hbox)