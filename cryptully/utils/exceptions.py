class GenericError(Exception):
    pass


class NetworkError(Exception):
    pass


class ProtocolError(Exception):
    def __init__(self, errno=0):
        Exception.__init__(self)
        self.errno = errno


class ProtocolEnd(Exception):
    pass


class CryptoError(Exception):
    pass
