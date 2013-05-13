import os
import sys
import signal
import curses

from encSocket import EncSocket


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


def showDialog(screen, title, message, isError):
    (height, width) = screen.getmaxyx()
    exitMessage = "Press Ctrl^c to exit" if isError else ""

    # Determine the max width of the dialog window
    dialogWidth = max(len(title), len(message), len(exitMessage)) + 2
    dialogHeight = 8 if message else 3

    dialogWindow = screen.subwin(dialogHeight, dialogWidth, height/2 - int(dialogHeight/2), width/2 - int(dialogWidth/2))
    dialogWindow.border(0)

    # Add the title
    dialogWindow.addstr(1, 1, title, curses.color_pair(2) if isError else curses.color_pair(1))

    if message:
        dialogWindow.hline(2, 1, 0, dialogWidth-2)

        # Add the message
        dialogWindow.addstr(3, 1, message)

        # Add the exit message if the dialog is an error dialog
        if isError:
            dialogWindow.addstr(6, 1, exitMessage)

    # Disable the cursor
    curses.curs_set(0)

    dialogWindow.refresh()

    # If an error dialog, block by waiting for a character
    if isError:
        dialogWindow.getch()
        os.kill(os.getpid(), signal.SIGINT)
    else:
        return dialogWindow
