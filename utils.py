import curses
import curses.ascii
import Exceptions

from EncSocket import EncSocket


def send(client, data):
    try:
        client.send(data)
    except Exceptions.NetworkError as ne:
        print ne
        client.disconnect()


def recv(client):
    try:
        return client.recv()
    except Exceptions.NetworkError as ne:
        print ne
        client.disconnect()
        

def doServerHandshake(client):
    # Send the server's public key
    localPubKey = client.crypto.getLocalPubKeyAsString()
    send(client, localPubKey)

    # Receive the client's public key
    remotePubKey = recv(client)
    client.crypto.setRemotePubKey(remotePubKey)

    # Switch to RSA encryption to exchange the AES key, IV, and salt
    client.setEncryptionType(EncSocket.RSA)

    # Send the AES key, IV, and salt
    send(client, client.crypto.aesKey)
    send(client, client.crypto.aesIv)
    send(client, client.crypto.aesSalt)

    # Switch to AES encryption for the remainder of the connection
    client.setEncryptionType(EncSocket.AES)


def doClientHandshake(sock):
    # Receive the server's public key
    remotePubKey = recv(sock)
    sock.crypto.setRemotePubKey(remotePubKey)

    # Send the client's public key
    localPubKey = sock.crypto.getLocalPubKeyAsString()
    send(sock, localPubKey)

    # Switch to RSA encryption to receive the AES key, IV, and salt
    sock.setEncryptionType(EncSocket.RSA)

    # Receive the AES key, IV, and salt
    sock.crypto.aesKey  = recv(sock)
    sock.crypto.aesIv   = recv(sock)
    sock.crypto.aesSalt = recv(sock)

    # Switch to AES encryption for the remainder of the connection
    sock.setEncryptionType(EncSocket.AES)


def inputValidator(char):
    if char == curses.KEY_HOME:
        return curses.ascii.SOH
    elif char == curses.KEY_END:
        return curses.ascii.ENQ
    elif char == curses.KEY_ENTER or char == ord('\n'):
         return curses.ascii.BEL
    return char
