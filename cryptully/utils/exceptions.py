class GenericError(Exception):
    def __init__(self, message=None, errno=0):
        Exception.__init__(self)
        self.message = message
        self.errno   = errno


class NetworkError(GenericError):
    def __init__(self, message=None, errno=0):
        GenericError.__init__(self, message, errno)


class ProtocolError(GenericError):
    def __init__(self, message=None, errno=0):
        GenericError.__init__(self, message, errno)


class ProtocolEnd(GenericError):
    def __init__(self, message=None, errno=0):
        GenericError.__init__(self, message, errno)


class CryptoError(GenericError):
    def __init__(self, message=None, errno=0):
        GenericError.__init__(self, message, errno)
