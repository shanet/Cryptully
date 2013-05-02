import os
import sys
import M2Crypto

from Exceptions import CryptoError


class Crypto:

    def __init__(self):
        self.localKeypair = None
        self.remoteKeypair = None


    def generateKeypair(self, bits):
        # Seed the random number generator with the number of bytes requested (bits/8)
        M2Crypto.Rand.rand_seed(os.urandom(bits/8))

        # Generate the keypair (65537 as the public exponent)
        self.localKeypair = M2Crypto.RSA.gen_key(bits, 65537)


    def setRemotePubKey(self, pubKey):
        if type(pubKey) is str:
            bio = M2Crypto.BIO.MemoryBuffer(pubKey)
            self.remoteKeypair = M2Crypto.RSA.load_pub_key_bio(bio)
        elif type(pubKey) is M2Crypto.RSA:
            self.remoteKeypair = pubKey
        else:
            raise CryptoError("Public key is not a string or RSA key object.")


    def encrypt(self, message):
        self.__checkRemoteKeypair()
        try:
            return self.remoteKeypair.public_encrypt(message, M2Crypto.RSA.pkcs1_oaep_padding)
        except M2Crypto.RSA.RSAError as rsae:
            raise CryptoError(str(rsae))


    def decrypt(self, message):
        self.__checkLocalKeypair()
        try:
            return self.localKeypair.private_decrypt(message, M2Crypto.RSA.pkcs1_oaep_padding)
        except M2Crypto.RSA.RSAError as rsae:
            raise CryptoError(str(rsae))


    def readLocalPubKeyFromFile(self, file):
        self.localKeypair = M2Crypto.load_pub_key(file)


    def readLocalPubKeyFromFile(self, file):
        self.localKeypair = M2Crypto.load_key(file)


    def readRemotePubKeyFromFile(self, file):
        self.remoteKeypair = M2Crypto.load_pub_key(file)


    def writeLocalPubKeyToFile(self, file):
        self.__checkLocalKeypair()
        self.localKeypair.save_pub_key(file)


    def writeLocalPriKeyToFile(self, file):
        self.__checkLocalKeypair()
        self.localKeypair.save_key(file)


    def writeRemotePubKeyToFile(self, file):
        self.__checkRemoteKeypair()
        self.remoteKeypair.save_pub_key(file)


    def getLocalPubKeyAsString(self):
        self.__checkLocalKeypair()
        bio = M2Crypto.BIO.MemoryBuffer()
        self.localKeypair.save_pub_key_bio(bio)
        return bio.read()


    def getRemotePubKeyAsString(self):
        self.__checkRemoteKeypair()
        bio = M2Crypto.BIO.MemoryBuffer()
        self.remoteKeypair.save_pub_key_bio(bio)
        return bio.read()


    def __checkLocalKeypair(self):
        if self.localKeypair is None:
            raise CryptoError("Local keypair not set.")


    def __checkRemoteKeypair(self):
        if self.remoteKeypair is None:
            raise CryptoError("Remote public key not set.")
