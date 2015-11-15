from mock import Mock
from threading import Event

class WaitingMock(Mock):
    TIMEOUT = 3

    def __init__(self, *args, **kwargs):
        super(WaitingMock, self).__init__(*args, **kwargs)
        self.calledEvent = Event()


    def _mock_call(self, *args, **kwargs):
        retval = super(WaitingMock, self)._mock_call(*args, **kwargs)

        if self.call_count >= 1:
            self.calledEvent.set()

        return retval

    def assert_called_with_wait(self, *args, **kargs):
        self.calledEvent.clear()

        if self.call_count >= 1:
            return True

        self.calledEvent.wait(timeout=self.TIMEOUT)
        self.assert_called_with(*args, **kargs)
