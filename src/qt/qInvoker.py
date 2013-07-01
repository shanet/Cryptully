from PyQt4.QtCore import QEvent
from PyQt4.QtCore import QObject

class InvokeEvent(QEvent):
    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())

    def __init__(self, fn, *args, **kwargs):
        QEvent.__init__(self, InvokeEvent.EVENT_TYPE)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs


class Invoker(QObject):
    def event(self, event):
        event.fn(*event.args, **event.kwargs)
        return True
