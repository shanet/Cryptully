import os
import sys
import M2Crypto

from Exceptions import CryptoError


class Crypto:
    ENCRYPT = 1;
    DECRYPT = 0;


    def __init__(self):
        self.localKeypair  = None
        self.remoteKeypair = None
        self.aesKey        = None
        self.aesIv         = None
        self.aesSalt       = None


    def generateKeys(self, bits=2048):
        # Seed the random number generator with the number of bytes requested (bits/8)
        M2Crypto.Rand.rand_seed(os.urandom(bits/8))

        # Generate the keypair (65537 as the public exponent)
        self.localKeypair = M2Crypto.RSA.gen_key(bits, 65537, self.__callback)

        # Generate the AES key and IV
        self.aesKey  = os.urandom(32)
        self.aesIv   = os.urandom(32)
        self.aesSalt = os.urandom(8)


    def setRemotePubKey(self, pubKey):
        if type(pubKey) is str:
            bio = M2Crypto.BIO.MemoryBuffer(pubKey)
            self.remoteKeypair = M2Crypto.RSA.load_pub_key_bio(bio)
        elif type(pubKey) is M2Crypto.RSA:
            self.remoteKeypair = pubKey
        else:
            raise CryptoError("Public key is not a string or RSA key object.")


    def rsaEncrypt(self, message):
        self.__checkRemoteKeypair()
        try:
            return self.remoteKeypair.public_encrypt(message, M2Crypto.RSA.pkcs1_oaep_padding)
        except M2Crypto.RSA.RSAError as rsae:
            raise CryptoError(str(rsae))


    def rsaDecrypt(self, message):
        self.__checkLocalKeypair()
        try:
            return self.localKeypair.private_decrypt(message, M2Crypto.RSA.pkcs1_oaep_padding)
        except M2Crypto.RSA.RSAError as rsae:
            raise CryptoError(str(rsae))


    def aesEncrypt(self, message):
        try:
            cipher = self.__aesGetCipher(self.ENCRYPT)
            encMessage = cipher.update(message)
            return encMessage + cipher.final()
        except M2Crypto.EVP.EVPError as evpe:
            raise CryptoError(str(evpe))


    def aesDecrypt(self, message):
        try:
            cipher = self.__aesGetCipher(self.DECRYPT)
            decMessage = cipher.update(message)
            return decMessage + cipher.final()
        except M2Crypto.EVP.EVPError as evpe:
            raise CryptoError(str(evpe))


    def __aesGetCipher(self, op):
        return M2Crypto.EVP.Cipher(alg='aes_256_cbc', key=self.aesKey, iv=self.aesIv, salt=self.aesSalt, d='sha256', op=op)


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


    def __callback(self):
        return