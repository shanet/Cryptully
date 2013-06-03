import os
import sys
import signal
import curses
import _exceptions

from getpass      import getpass
from crypto       import Crypto
from encSocket    import EncSocket
from cursesDialog import CursesDialog


def doServerHandshake(sock):
    # Send the server's public key
    localPubKey = sock.crypto.getLocalPubKeyAsString()
    sock.send(localPubKey)

    # Receive the client's public key
    remotePubKey = sock.recv()
    sock.crypto.setRemotePubKey(remotePubKey)

    # Switch to RSA encryption to exchange the AES key, IV, and salt
    sock.setEncryptionType(EncSocket.RSA)

    # Send the AES key, IV, and salt
    sock.send(sock.crypto.aesKey)
    sock.send(sock.crypto.aesIv)
    sock.send(sock.crypto.aesSalt)

    # Switch to AES encryption for the remainder of the connection
    sock.setEncryptionType(EncSocket.AES)


def doClientHandshake(sock):
    # Receive the server's public key
    remotePubKey = sock.recv()
    sock.crypto.setRemotePubKey(remotePubKey)

    # Send the client's public key
    localPubKey = sock.crypto.getLocalPubKeyAsString()
    sock.send(localPubKey)

    # Switch to RSA encryption to receive the AES key, IV, and salt
    sock.setEncryptionType(EncSocket.RSA)

    # Receive the AES key, IV, and salt
    sock.crypto.aesKey  = sock.recv()
    sock.crypto.aesIv   = sock.recv()
    sock.crypto.aesSalt = sock.recv()

    # Switch to AES encryption for the remainder of the connection
    sock.setEncryptionType(EncSocket.AES)


def showOptionsMenuWindow(screen, crypto, showStartOption=False):
    (height, width) = screen.getmaxyx()

    menuWindow = screen.subwin((9 if showStartOption else 8), 40, 3, width/2 - 20)
    menuWindow.border(0)

    # Enable arrow key detection for this window
    menuWindow.keypad(True)

    pos = 1

    while True:
        # Disable the cursor
        curses.curs_set(0)

        while True:
            menuItem = 1
            if showStartOption:
                menuWindow.addstr(menuItem, 1, str(menuItem) + ".| Start chat", curses.color_pair(4) if pos == menuItem else curses.color_pair(1))
                menuItem += 1
            menuWindow.addstr(menuItem, 1, str(menuItem) + ".| Show server fingerprint", curses.color_pair(4) if pos == menuItem else curses.color_pair(1))
            menuItem += 1
            menuWindow.addstr(menuItem, 1, str(menuItem) + ".| Save current keypair", curses.color_pair(4) if pos == menuItem else curses.color_pair(1))
            menuItem += 1
            menuWindow.addstr(menuItem, 1, str(menuItem) + ".| Clear saved keypair", curses.color_pair(4) if pos == menuItem else curses.color_pair(1))
            menuItem += 1
            menuWindow.addstr(menuItem, 1, str(menuItem) + ".| Show help", curses.color_pair(4) if pos == menuItem else curses.color_pair(1))
            menuItem += 1
            menuWindow.addstr(menuItem, 1, str(menuItem) + ".| Close menu", curses.color_pair(4) if pos == menuItem else curses.color_pair(1))
            menuItem += 1
            menuWindow.addstr(menuItem, 1, str(menuItem) + ".| Quit application", curses.color_pair(4) if pos == menuItem else curses.color_pair(1))


            menuWindow.refresh()
            key = menuWindow.getch()
            if key == curses.KEY_DOWN and pos < (7 if showStartOption else 6):
                pos += 1
            elif key == curses.KEY_UP and pos > 1:
                pos -= 1
            # Enter key
            elif key == ord('\n'):
                break

        # Move the selected item by 1 to adjust for the lack of a start option
        if not showStartOption:
            pos += 1

        # Process the selected option
        if pos == 1:
            break
        if pos == 2:
            CursesDialog(screen, crypto.getLocalFingerprint(), "Server fingerprint", isBlocking=True).show()
        elif pos == 3:
            passphrase = getKeypairPassphrase(screen, True)
            saveKeypair(crypto, passphrase)
            CursesDialog(screen, "This keypair will be used for all subsequent chats", "Keypair Saved", isBlocking=True).show()
        elif pos == 4:
            clearKeypair()
            CursesDialog(screen, "Keypair cleared", isBlocking=True).show()
        elif pos == 5:
            CursesDialog(screen, "Not implemented yet", isBlocking=True).show()
        elif pos == 6:
            break
        elif pos == 7:
            os.kill(os.getpid(), signal.SIGINT)

        # Shift the selected item position back
        if not showStartOption:
            pos -= 1

    # Re-enable the cursor
    curses.curs_set(2)

    # Get rid of the accept window
    menuWindow.clear()
    menuWindow.refresh()


def saveKeypair(crypto, passphrase):
    storeDir = os.path.join(os.path.expanduser('~'), '.cryptully')

    # Create the path if it doesn't already exist
    if not os.path.exists(storeDir):
        os.makedirs(storeDir)

    keypairFile = os.path.join(storeDir, 'keypair.pem')

    crypto.writeLocalKeypairToFile(keypairFile, passphrase)

    # Set the directory & keypair permissions to read/write/execute for the current user only
    # and no permissions for everyone else
    os.chmod(storeDir, 0700)
    os.chmod(keypairFile, 0700)


def clearKeypair():
    storeDir = os.path.join(os.path.expanduser('~'), '.cryptully')

    # Check that the path exists
    if not os.path.exists(storeDir):
        return

    keypairFile = os.path.join(storeDir, 'keypair.pem')
    os.unlink(keypairFile)

    # Try to remove the directory if empty
    os.rmdir(storeDir)


def loadKeypair(crypto, passphrase):
    storeDir = os.path.join(os.path.expanduser('~'), '.cryptully')
    keypairFile = os.path.join(storeDir, 'keypair.pem')

    # Check that the path and keypair file both exist
    if not (os.path.exists(storeDir) and os.path.exists(keypairFile)):
        return

    crypto.readLocalKeypairFromFile(keypairFile, passphrase)


def loadOrGenerateKepair(screen):
    crypto = Crypto()
    if doesSavedKeypairExist():
        while(True):
            passphrase = getKeypairPassphrase(screen)
            try:
                loadKeypair(crypto, passphrase)
                break
            except _exceptions.CryptoError:
                CursesDialog(screen, "Wrong passphrase", '', isBlocking=True).show()

        # We still need to generate an AES key
        crypto.generateAESKey()
    else:
        crypto.generateKeys()

    return crypto


def doesSavedKeypairExist():
    storeDir = os.path.join(os.path.expanduser('~'), '.cryptully')
    keypairFile = os.path.join(storeDir, 'keypair.pem')

    # Check that the path and keypair file both exist
    return (os.path.exists(storeDir) and os.path.exists(keypairFile))


def getKeypairPassphrase(screen, verify=False):
    (height, width) = screen.getmaxyx()
    passphraseWindow = screen.subwin(3, 36, height/2 - 1, width/2 - 18)

    # Turn on echo and wait for enter key to read buffer
    curses.echo()
    curses.nocbreak()

    while True:
        passphraseWindow.border(0)
        passphraseWindow.addstr(1, 1, "Passphrase: ")
        passphraseWindow.refresh()
        passphrase = getpass('')

        if not verify:
            break

        passphraseWindow.clear()
        passphraseWindow.border(0)
        passphraseWindow.addstr(1, 1, "Verify: ")
        passphraseWindow.refresh()
        verifyPassphrase = getpass('')

        if passphrase == verifyPassphrase:
            break
        else:
            curses.cbreak()
            CursesDialog(screen, "Passphrases do not match", '', isBlocking=True).show()
            curses.nocbreak()

    # Turn off echo and disable buffering
    curses.cbreak()
    curses.noecho()

    # Get rid of the passphrase window
    passphraseWindow.clear()
    passphraseWindow.refresh()

    return passphrase
