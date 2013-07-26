import os
import signal


from PyQt4.QtCore import QCoreApplication
from PyQt4.QtGui  import QDesktopWidget
from PyQt4.QtGui  import QIcon
from PyQt4.QtGui  import QInputDialog
from PyQt4.QtGui  import QMessageBox
from PyQt4.QtGui  import QPixmap
from PyQt4.QtGui  import QWidget

import qInvoker
from qPassphraseDialog import QPassphraseDialog

from utils import constants
from utils import utils


invoker = qInvoker.Invoker()


def centerWindow(window):
    centerPoint = QDesktopWidget().availableGeometry().center()
    geo = window.frameGeometry()
    geo.moveCenter(centerPoint)
    window.move(geo.topLeft())


def resizeWindow(window, width, height):
    window.setGeometry(0, 0, width, height)


def getKeypairPassphrase(parent=None, verify=False, showForgotButton=True):
    if parent is None:
        parent = QWidget()

    while True:
        passphrase, button = QPassphraseDialog.getPassphrase(False, showForgotButton)
        if button == constants.BUTTON_CANCEL:
            return
        if button == constants.BUTTON_FORGOT:
            clearKeypair(parent)
            return

        if not verify:
            return passphrase

        verifyPassphrase, button = QPassphraseDialog.getPassphrase(verify, showForgotButton)
        if button == constants.BUTTON_CANCEL:
            return

        if passphrase == verifyPassphrase:
            return passphrase
        else:
            QMessageBox.critical(parent, "Keypair Passphrase", "Passphrases do not match")


def clearKeypair(parent=None):
    if parent == None:
        parent = QWidget()

    if not utils.doesSavedKeypairExist():
        QMessageBox.warning(parent, "No Keys Saved", "No encryption keys have been saved yet.")
        return

    confirm = QMessageBox.question(parent, 'Clear Keys', "Are you sure you want to clear your saved encryption keys?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    if confirm == QMessageBox.Yes:
        utils.clearKeypair()
        QMessageBox.information(parent, "Keys Cleared", "Encryption keys cleared. New keys will be generated. You should verify key integrity for all new connections now.")


isLightTheme = False
def setIsLightTheme(color):
    global isLightTheme
    isLightTheme = (color.red() > 100 and color.blue() > 100 and color.green() > 100)


def getAbsoluteImagePath(imageName):
    global isLightTheme
    return utils.getAbsoluteResourcePath('images/' + ('light' if isLightTheme else 'dark') + '/' + imageName)


def runOnUIThread(function, *args, **kwargs):
    QCoreApplication.postEvent(invoker, qInvoker.InvokeEvent(function, *args, **kwargs))


def exitApp():
    os.kill(os.getpid(), signal.SIGINT)
