import os
import sys

from . import constants
from . import errors

from time import localtime
from time import strftime


def isValidNick(nick):
    if nick == "":
        return errors.INVALID_EMPTY_NICK
    if not nick.isalnum():
        return errors.INVALID_NICK_CONTENT
    if len(nick) > constants.NICK_MAX_LEN:
        return errors.INVALID_NICK_LENGTH
    return errors.VALID_NICK


def getTimestamp():
    return strftime('%H:%M:%S', localtime())


def getAbsoluteResourcePath(relativePath):
    try:
        # PyInstaller stores data files in a tmp folder refered to as _MEIPASS
        basePath = sys._MEIPASS
    except Exception:
        # If not running as a PyInstaller created binary, try to find the data file as
        # an installed Python egg
        try:
            basePath = os.path.dirname(sys.modules['src'].__file__)
        except Exception:
            basePath = ''

        # If the egg path does not exist, assume we're running as non-packaged
        if not os.path.exists(os.path.join(basePath, relativePath)):
            basePath = 'src'

    path = os.path.join(basePath, relativePath)

    # If the path still doesn't exist, this function won't help you
    if not os.path.exists(path):
        return None

    return path


def secureStrcmp(left, right):
    equal = True

    if len(left) != len(right):
        equal = False

    for i in range(0, min(len(left), len(right))):
        if left[i] != right[i]:
            equal = False

    return equal
