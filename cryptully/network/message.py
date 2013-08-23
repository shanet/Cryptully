import base64
import json


class Message(object):
    def __init__(self, serverCommand=None, clientCommand=None, sourceNick=None, destNick=None,
                 payload=None, hmac=None, error=None):
        self.serverCommand = str(serverCommand)
        self.clientCommand = str(clientCommand)
        self.sourceNick    = str(sourceNick)
        self.destNick      = str(destNick)
        self.payload       = str(payload)
        self.hmac          = str(hmac)
        self.error         = str(error)


    def __str__(self):
        return json.dumps({'serverCommand': self.serverCommand, 'clientCommand': self.clientCommand,
                           'sourceNick': self.sourceNick, 'destNick': self.destNick,
                           'payload': self.payload, 'hmac': self.hmac, 'error': self.error})


    def getEncryptedPayloadAsBinaryString(self):
        return base64.b64decode(self.payload)


    def setEncryptedPayload(self, payload):
        self.payload = str(base64.b64encode(payload))


    def getHmacAsBinaryString(self):
        return base64.b64decode(self.hmac)


    def setBinaryHmac(self, hmac):
        self.hmac = str(base64.b64encode(hmac))


    @staticmethod
    def createFromJSON(jsonStr):
        jsonStr = json.loads(jsonStr)
        return Message(jsonStr['serverCommand'], jsonStr['clientCommand'], jsonStr['sourceNick'], jsonStr['destNick'],
                       jsonStr['payload'], jsonStr['hmac'], jsonStr['error'])
