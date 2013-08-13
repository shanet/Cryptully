import base64
import json


class Message(object):
    def __init__(self, serverCommand=None, clientCommand=None, sourceNick=None, destNick=None,
                 payload=None, hmac=None, error=None, key=None, iv=None, salt=None):
        self.serverCommand = str(serverCommand)
        self.clientCommand = str(clientCommand)
        self.sourceNick    = str(sourceNick)
        self.destNick      = str(destNick)
        self.payload       = str(payload)
        self.hmac          = str(hmac)
        self.error         = str(error)
        self.key           = str(key)
        self.iv            = str(iv)
        self.salt          = str(salt)


    def __str__(self):
        return json.dumps({'serverCommand': self.serverCommand, 'clientCommand': self.clientCommand,
                           'sourceNick': self.sourceNick, 'destNick': self.destNick,
                           'payload': self.payload, 'hmac': self.hmac, 'error': self.error,
                           'key': self.key, 'iv': self.iv, 'salt': self.salt})


    def getEncryptedPayloadAsBinaryString(self):
        return base64.b64decode(self.payload)


    def setEncryptedPayload(self, payload):
        self.payload = str(base64.b64encode(payload))


    def getHmacAsBinaryString(self):
        return base64.b64decode(self.hmac)


    def setBinaryHmac(self, hmac):
        self.hmac = str(base64.b64encode(hmac))


    def getKeyAsBinaryString(self):
        return base64.b64decode(self.key)


    def setBinaryKey(self, key):
        self.key = str(base64.b64encode(key))


    def getIvAsBinaryString(self):
        return base64.b64decode(self.iv)


    def setBinaryIv(self, iv):
        self.iv = str(base64.b64encode(iv))


    def getSaltAsBinaryString(self):
        return base64.b64decode(self.salt)


    def setBinarySalt(self, salt):
        self.salt = str(base64.b64encode(salt))


    @staticmethod
    def createFromJSON(jsonStr):
        jsonStr = json.loads(jsonStr)
        return Message(jsonStr['serverCommand'], jsonStr['clientCommand'], jsonStr['sourceNick'], jsonStr['destNick'],
                       jsonStr['payload'], jsonStr['hmac'], jsonStr['error'],
                       jsonStr['key'], jsonStr['iv'], jsonStr['salt'])
