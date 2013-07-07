from PyQt4.QtCore import Qt
from PyQt4.QtGui import QLabel

class QLinkLabel(QLabel):
    def __init__(self, text, link, parent=None):
        QLabel.__init__(self, parent)

        self.setText("<a href=\"" + link + "\">" + text + "</a>")
        self.setTextFormat(Qt.RichText)
        self.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.setOpenExternalLinks(True)
