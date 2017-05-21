import os
import M2Crypto

from utils import constants
from utils import exceptions

class Crypto(object):
    ENCRYPT = 1;
    DECRYPT = 0;

    dhPrime = 0x00a53d56c30fe79d43e3c9a0b678e87c0fcd2e78b15c676838d2a2bd6c299b1e7fdb286d991f62e8f366b0067ae71d3d91dac4738fd744ee180b16c97a54215236d4d393a4c85d8b390783566c1b0d55421a89fca20b85e0faecded7983d038821778b6504105f455d8655953d0b62841e9cc1248fa21834bc9f3e3cc1c080cfcb0b230fd9a2059f5f637395dfa701981fad0dbeb545e2e29cd20f7b6baee9314039e16ef19f604746fe596d50bb3967da51b948184d8d4511f2c0b8e4b4e3abc44144ce1f5968aadd053600a40430ba97ad9e0ad26fe4c444be3f48434a68aa132b1677d8442454fe4c6ae9d3b7164e6603f1c8a8f5b5235ba0b9f5b5f86278e4f69eb4d5388838ef15678535589516a1d85d127da8f46f150613c8a49258be2ed53c3e161d0049cabb40d15f9042a00c494746753b9794a9f66a93b67498c7c59b8253a910457c10353fa8e2edcafdf6c9354a3dc58b5a825c353302d686596c11e4855e86f3c6810f9a4abf917f69a6083330492aedb5621ebc3fd59778a40e0a7fa8450c8b2c6fe3923775419b2ea35cd19abe62c50020df991d9fc772d16dd5208468dc7a9b51c6723495fe0e72e818ee2b2a8581fab2caf6bd914e4876573b023862286ec88a698be2dd34c03925ab5ca0f50f0b2a246ab852e3779f0cf9d3e36f9ab9a50602d5e9216c3a29994e81e151accd88ea346d1be6588068e873
    dhGenerator = 2

    def __init__(self):
        self.localKeypair   = None
        self.remoteKeypair  = None
        self.aesKey         = None
        self.aesIv          = None
        self.aesSalt        = None
        self.dh             = None
        self.aesMode        = constants.DEFAULT_AES_MODE


    def generateKeys(self, rsaBits=2048, aesMode=constants.DEFAULT_AES_MODE):
        self.generateRSAKeypair(rsaBits)
        self.generateAESKey(aesMode)


    def generateRSAKeypair(self, bits=2048):
        # Generate the keypair (65537 as the public exponent)
        self.localKeypair = M2Crypto.RSA.gen_key(bits, 65537, self.__generateKeypairCallback)


    def generateAESKey(self, aesMode=constants.DEFAULT_AES_MODE):
        self.aesMode = aesMode

        # Generate the AES key and IV
        bitsString = aesMode[4:7]
        if bitsString == '128':
            self.aesBytes = 16
        elif bitsString == '192':
            self.aesBytes = 24
        elif bitsString == '256':
            self.aesBytes = 32
        else:
            raise exceptions.CryptoError("Invalid AES mode")

        self.aesKey  = M2Crypto.Rand.rand_bytes(self.aesBytes)
        self.aesIv   = M2Crypto.Rand.rand_bytes(self.aesBytes)
        self.aesSalt = M2Crypto.Rand.rand_bytes(8)


    def generateDHKey(self):
        self.dh = M2Crypto.DH.set_params(decToMpi(self.dhPrime), decToMpi(self.dhGenerator))
        self.dh.gen_key()


    def computeDHSecret(self, publicKey):
        self.dhSecret = binToDec(self.dh.compute_key(decToMpi(publicKey)))
        hash = self.hash(str(self.dhSecret), 'sha512')
        self.aesKey = hash[0:32]
        self.aesIv = hash[32:64]
        self.aesSalt = hash[56:64]


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
        return M2Crypto.EVP.Cipher(alg=self.aesMode, key=self.aesKey, iv=self.aesIv, salt=self.aesSalt, d='sha256', op=op)


    def generateHmac(self, message):
        hmac = M2Crypto.EVP.HMAC(self.aesKey, 'sha256')
        hmac.update(message)
        return hmac.digest()


    def hash(self, message, type='sha256'):
        hash = M2Crypto.EVP.MessageDigest(type)
        hash.update(message)
        return hash.final()


    def stringHash(self, message):
        digest = self.hash(message)
        return hex(self.__octx_to_num(digest))[2:-1].upper()


    def mapStringToInt(self, string):
        num = 0
        shift = 0

        for char in reversed(string):
          num |= ord(char) << shift
          shift += 8

        return num


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
        self.localKeypair.save_key(file, self.aesMode, self.__passphraseCallback)


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
        return self.localKeypair.as_pem(self.aesMode, self.__passphraseCallback)


    def getLocalFingerprint(self):
        return self.__generateFingerprint(self.getLocalPubKeyAsString())


    def getRemoteFingerprint(self):
        return self.__generateFingerprint(self.getRemotePubKeyAsString())


    def __generateFingerprint(self, key):
        digest = self.stringHash(key)

        # Add colons between every 2 characters of the fingerprint
        fingerprint = ''
        digestLength = len(digest)
        for i in range(0, digestLength):
            fingerprint += digest[i]
            if i&1 and i != 0 and i != digestLength-1:
                fingerprint += ':'
        return fingerprint


    def __octx_to_num(self, data):
        converted = 0
        length = len(data)
        for i in range(length):
            converted = converted + ord(data[i]) * (256 ** (length - i - 1))
        return converted


    def getDHPubKey(self):
        return mpiToDec(self.dh.pub)


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


def mpiToDec(mpi):
    bn = M2Crypto.m2.mpi_to_bn(mpi)
    hex = M2Crypto.m2.bn_to_hex(bn)
    return int(hex, 16)


def binToDec(binval):
    bn = M2Crypto.m2.bin_to_bn(binval)
    hex = M2Crypto.m2.bn_to_hex(bn)
    return int(hex, 16)


def decToMpi(dec):
    bn = M2Crypto.m2.dec_to_bn('%s' % dec)
    return M2Crypto.m2.bn_to_mpi(bn)
