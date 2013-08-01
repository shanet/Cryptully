class GenericError(Exception):
    pass


class NetworkError(Exception):
    def __init__(self, message, errno=0):
        Exception.__init__(self, message)
        self.errno = errno


class ProtocolError(Exception):
    def __init__(self, errno=0):
        Exception.__init__(self)
        self.errno = errno


class ProtocolEnd(Exception):
    pass


class CryptoError(Exception):
    pass
