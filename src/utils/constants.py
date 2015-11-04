DEFAULT_TURN_SERVER = 'cryptully.com'
DEFAULT_PORT        = 9000

PROTOCOL_VERSION = '1'
NICK_MAX_LEN = 32
DEFAULT_AES_MODE = 'aes_256_cbc'
TYPING_TIMEOUT = 1500

# Protocol commands

# Server commands
COMMAND_REGISTER = "REG"
COMMAND_RELAY    = "REL"
COMMAND_VERSION  = "VERSION"

# Client commands

# Handshake commands
COMMAND_HELO       = "HELO"
COMMAND_REDY       = "REDY"
COMMAND_REJECT     = "REJ"
COMMAND_PUBLIC_KEY = "PUB_KEY"

# Loop commands
COMMAND_MSG    = "MSG"
COMMAND_TYPING = "TYPING"
COMMAND_END    = "END"
COMMAND_ERR    = "ERR"
COMMAND_SMP_0  = "SMP0"
COMMAND_SMP_1  = "SMP1"
COMMAND_SMP_2  = "SMP2"
COMMAND_SMP_3  = "SMP3"
COMMAND_SMP_4  = "SMP4"

SMP_COMMANDS = [
  COMMAND_SMP_0,
  COMMAND_SMP_1,
  COMMAND_SMP_2,
  COMMAND_SMP_3,
  COMMAND_SMP_4,
]

LOOP_COMMANDS = [
  COMMAND_MSG,
  COMMAND_TYPING,
  COMMAND_END,
  COMMAND_ERR,
  COMMAND_SMP_0,
  COMMAND_SMP_1,
  COMMAND_SMP_2,
  COMMAND_SMP_3,
  COMMAND_SMP_4,
]

# Message sources
SENDER   = 0
RECEIVER = 1
SERVICE  = 2

# Typing statuses
TYPING_START             = 0
TYPING_STOP_WITHOUT_TEXT = 1
TYPING_STOP_WITH_TEXT    = 2

# QT UI custom button codes
BUTTON_OKAY   = 0
BUTTON_CANCEL = 1
BUTTON_FORGOT = 2

# Ncurses accept/mode dialog codes
ACCEPT = 0
REJECT = 1

CONNECT = 0
WAIT    = 1

SMP_CALLBACK_REQUEST  = 0
SMP_CALLBACK_COMPLETE = 1
SMP_CALLBACK_ERROR    = 2

URL_REGEX = r"(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?]))"
