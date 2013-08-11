DEFAULT_TURN_SERVER = 'cryptully.com'
DEFAULT_PORT        = 9000

NICK_MAX_LEN = 32

# Protocol commands

# Server commands
COMMAND_REGISTER   = "REG"
COMMAND_RELAY      = "REL"

# Client commands

# Handshake commands
COMMAND_HELO       = "HELO"
COMMAND_REDY       = "REDY"
COMMAND_REJECT     = "REJ"
COMMAND_PUBLIC_KEY = "PUB_KEY"
COMMAND_AES_KEY    = "AES_KEY"
COMMAND_AES_IV     = "AES_IV"
COMMAND_AES_SALT   = "AES_SALT"

# Loop commands
COMMAND_MSG        = "MSG"
COMMAND_END        = "END"
COMMAND_ERR        = "ERR"
LOOP_COMMANDS = [COMMAND_MSG, COMMAND_END, COMMAND_ERR]

# Message sources
SENDER   = 0
RECEIVER = 1
SERVICE  = 2

# QT UI custom button codes
BUTTON_OKAY   = 0
BUTTON_CANCEL = 1
BUTTON_FORGOT = 2

# Ncurses accept/mode dialog codes
ACCEPT = 0
REJECT = 1

CONNECT = 0
WAIT    = 1

URL_REGEX = r"(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?]))"
