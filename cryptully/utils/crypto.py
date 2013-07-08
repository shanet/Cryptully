import os
import M2Crypto

import exceptions

class Crypto(object):
    ENCRYPT = 1;
    DECRYPT = 0;


    def __init__(self, generateKeys=False):
        self.localKeypair  = None
        self.remoteKeypair = None
        self.aesKey        = None
        self.aesIv         = None
        self.aesSalt       = None

        if generateKeys:
            self.generateKeys()


    def generateKeys(self, rsaBits=2048, aesMode='aes_256_cbc'):
        self.generateRSAKeypair(rsaBits)
        self.generateAESKey(aesMode)


    def generateRSAKeypair(self, bits=2048):
        # Seed the random number generator with the number of bytes requested (bits/8)
        M2Crypto.Rand.rand_seed(os.urandom(bits/8))

        # Generate the keypair (65537 as the public exponent)
        self.localKeypair = M2Crypto.RSA.gen_key(bits, 65537, self.__generateKeypairCallback)


    def generateAESKey(self, aesMode='aes_256_cbc'):
        self.aesMode = aesMode

        # Generate the AES key and IV
        bitsString = aesMode[4:7]
        if bitsString == '128':
            bits = 16
        elif bitsString == '192':
            bits = 24
        elif bitsString == '256':
            bits = 32
        else:
            raise exceptions.CryptoError("Invalid AES mode")

        self.aesKey  = os.urandom(bits)
        self.aesIv   = os.urandom(bits)
        self.aesSalt = os.urandom(8)


    def setRemotePubKey(self, pubKey):
        if type(pubKey) is str:
            bio = M2Crypto.BIO.MemoryBuffer(pubKey)
            self.remoteKeypair = M2Crypto.RSA.load_pub_key_bio(bio)
        elif type(pubKey) is M2Crypto.RSA:
            self.remoteKeypair = pubKey
        else:
            raise exceptions.CryptoError("Public key is not a string or RSA key object.")


    def rsaEncrypt(self, message):
        self.__checkRemoteKeypair()
        try:
            return self.remoteKeypair.public_encrypt(message, M2Crypto.RSA.pkcs1_oaep_padding)
        except M2Crypto.RSA.RSAError as rsae:
            raise exceptions.CryptoError(str(rsae))


    def rsaDecrypt(self, message):
        self.__checkLocalKeypair()
        try:
            return self.localKeypair.private_decrypt(message, M2Crypto.RSA.pkcs1_oaep_padding)
        except M2Crypto.RSA.RSAError as rsae:
            raise exceptions.CryptoError(str(rsae))


    def aesEncrypt(self, message):
        try:
            cipher = self.__aesGetCipher(self.ENCRYPT)
            encMessage = cipher.update(message)
            return encMessage + cipher.final()
        except M2Crypto.EVP.EVPError as evpe:
            raise exceptions.CryptoError(str(evpe))


    def aesDecrypt(self, message):
        try:
            cipher = self.__aesGetCipher(self.DECRYPT)
            decMessage = cipher.update(message)
            return decMessage + cipher.final()
        except M2Crypto.EVP.EVPError as evpe:
            raise exceptions.CryptoError(str(evpe))


    def __aesGetCipher(self, op):
        return M2Crypto.EVP.Cipher(alg='aes_256_cbc', key=self.aesKey, iv=self.aesIv, salt=self.aesSalt, d='sha256', op=op)


    def readLocalKeypairFromFile(self, file, passphrase):
        self._keypairPassphrase = passphrase
        try:
            self.localKeypair = M2Crypto.RSA.load_key(file, self.__passphraseCallback)
        except M2Crypto.RSA.RSAError as rsae:
            raise exceptions.CryptoError(str(rsae))


    def readRemotePubKeyFromFile(self, file):
        self.remoteKeypair = M2Crypto.RSA.load_pub_key(file)


    def writeLocalKeypairToFile(self, file, passphrase):
        self.__checkLocalKeypair()
        self._keypairPassphrase = passphrase
        self.localKeypair.save_key(file, 'aes_256_cbc', self.__passphraseCallback)


    def writeLocalPubKeyToFile(self, file):
        self.__checkLocalKeypair()
        self.localKeypair.save_pub_key(file)


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


    def getKeypairAsString(self, passphrase):
        self._keypairPassphrase = passphrase
        return self.localKeypair.as_pem('aes_256_cbc', self.__passphraseCallback)


    def getLocalFingerprint(self):
        self.__checkLocalKeypair()
        return self.__generateFingerprint(self.getLocalPubKeyAsString())


    def getRemoteFingerprint(self):
        self.__checkRemoteKeypair()
        return self.__generateFingerprint(self.getRemotePubKeyAsString())


    def __generateFingerprint(self, key):
        # Create the fingerprint by running the key through md5
        md = M2Crypto.EVP.MessageDigest('md5')
        md.update(key)
        digest = md.final()
        digest = hex(self.__octx_to_num(digest))[2:-1].upper()

        # Add colons between every 2 characters of the fingerprint
        fingerprint = ''
        digestLength = len(digest)
        for i in range(0, digestLength):
            fingerprint += digest[i]
            if i&1 and i != 0 and i != digestLength-1:
                fingerprint += ':'
        return fingerprint


    def __octx_to_num(self, data):
        converted = 0L
        length = len(data)
        for i in range(length):
            converted = converted + ord(data[i]) * (256L ** (length - i - 1))
        return converted


    def __checkLocalKeypair(self):
        if self.localKeypair is None:
            raise exceptions.CryptoError("Local keypair not set.")


    def __checkRemoteKeypair(self):
        if self.remoteKeypair is None:
            raise exceptions.CryptoError("Remote public key not set.")


    def __generateKeypairCallback(self):
        pass


    def __passphraseCallback(self, ignore, prompt1=None, prompt2=None):
        return self._keypairPassphrase
