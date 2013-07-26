import base64
import json


class Message(object):
    def __init__(self, serverCommand=None, clientCommand=None, sourceNick=None, destNick=None, payload=None, error=None):
        self.serverCommand = str(serverCommand)
        self.clientCommand = str(clientCommand)
        self.sourceNick    = str(sourceNick)
        self.destNick      = str(destNick)
        self.payload       = str(payload)
        self.error         = str(error)


    def __str__(self):
        return json.dumps({'serverCommand': self.serverCommand, 'clientCommand': self.clientCommand,
                           'sourceNick': self.sourceNick, 'destNick': self.destNick,
                           'payload': self.payload, 'error': self.error})


    def getEncryptedPayloadAsString(self):
        return base64.b64decode(self.payload)


    def setEncryptedPayload(self, payload):
        self.payload = str(base64.b64encode(payload))


    @staticmethod
    def createFromJSON(jsonStr):
        jsonStr = json.loads(jsonStr)
        return Message(jsonStr['serverCommand'], jsonStr['clientCommand'], jsonStr['sourceNick'], jsonStr['destNick'], jsonStr['payload'], jsonStr['error'])
