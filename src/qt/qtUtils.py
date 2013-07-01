import os
import signal

import qInvoker

from PyQt4.QtCore import QCoreApplication
from PyQt4.QtGui  import QDesktopWidget
from PyQt4.QtGui  import QIcon
from PyQt4.QtGui  import QInputDialog
from PyQt4.QtGui  import QPixmap
from PyQt4.QtGui  import QWidget


invoker = qInvoker.Invoker()

def centerWindow(window, width, height):
    window.setGeometry(0, 0, width, height)
    centerPoint = QDesktopWidget().availableGeometry().center()
    geo = window.frameGeometry()
    geo.moveCenter(centerPoint)
    window.move(geo.topLeft())


def getKeypairPassphrase(parent=None, verify=False):
    if parent is None:
        parent = QWidget()

    while True:
        passphrase, ok = QInputDialog.getText(QWidget(), "Keypair Passphrase", "Passphrase:")
        if not ok:
            exitApp()

        if not verify:
            return passphrase

        verifyPassphrase, ok = QInputDialog.getText(QWidget(), "Keypair Passphrase", "Verify:")
        if not ok:
            exitApp()

        if passphrase == verifyPassphrase:
            return passphrase
        else:
            QMessageBox.critical(self, "Keypair Passphrase", "Passphrases do not match")


def isLightTheme(color):
    return (color.red() > 100 and color.blue() > 100 and color.green() > 100)


def runOnUIThread(function, *args, **kwargs):
    QCoreApplication.postEvent(invoker, qInvoker.InvokeEvent(function, *args, **kwargs))


def exitApp():
    os.kill(os.getpid(), signal.SIGINT)
