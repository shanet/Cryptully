import constants

# Nick validation statuses
VALID_NICK           = 0
INVALID_NICK_CONTENT = 1
INVALID_NICK_LENGTH  = 2
INVALID_EMPTY_NICK   = 3

# UI error messages
TITLE_CONNECTION_ENDED    = "Connection Ended"
TITLE_NETWORK_ERROR       = "Network Error"
TITLE_CRYPTO_ERROR        = "Crypto Error"
TITLE_END_CONNECTION      = "Connection Ended"
TITLE_INVALID_NICK        = "Invalid Nickname"
TITLE_NICK_NOT_FOUND      = "Nickname Not Found"
TITLE_CONNECTION_REJECTED = "Connection Rejected"
TITLE_PROTOCOL_ERROR      = "Invalid Response"
TITLE_CLIENT_EXISTS       = "Client Exists"
TITLE_SELF_CONNECT        = "Self Connection"
TITLE_SERVER_SHUTDOWN     = "Server Shutdown"
TITLE_INVALID_COMMAND     = "Invalid Command"
TITLE_ALREADY_CONNECTED   = "Already Chatting"
TITLE_UNKNOWN_ERROR       = "Unknown Error"
TITLE_EMPTY_NICK          = "No Nickname Provided"
TITLE_NETWORK_ERROR       = "Network Error"
TITLE_BAD_HMAC            = "Tampering Detected"

UNEXPECTED_CLOSE_CONNECTION = "Remote unexpectedly closed connection"
UNEXPECTED_DATA             = "Remote sent unexpected data"
UNEXPECTED_COMMAND          = "Receieved unexpected command"
NO_COMMAND_SEPARATOR        = "Command separator not found in message"
UNKNOWN_ENCRYPTION_TYPE     = "Unknown encryption type"
VERIFY_PASSPHRASE_FAILED    = "Passphrases do not match"
BAD_PASSPHRASE              = "Wrong passphrase"
BAD_PASSPHRASE_VERBOSE      = "An incorrect passphrase was entered"
FAILED_TO_START_SERVER      = "Error starting server"
FAILED_TO_ACCEPT_CLIENT     = "Error accepting client connection"
FAILED_TO_CONNECT           = "Error connecting to server"
CLIENT_ENDED_CONNECTION     = "The client requested to end the connection"
INVALID_NICK_CONTENT        = "Sorry, nicknames can only contain numbers and letters"
INVALID_NICK_LENGTH         = "Sorry, nicknames must be less than " + str(constants.NICK_MAX_LEN) + " characters"
NICK_NOT_FOUND              = "The requested nickname could not be found"
CONNECTION_REJECTED         = "%s rejected your connection"
PROTOCOL_ERROR              = "%s sent unexpected data"
CLIENT_EXISTS               = "%s is open in another tab already"
CONNECTION_ENDED            = "%s has disconnected"
SELF_CONNECT                = "You cannot connect to yourself"
SERVER_SHUTDOWN             = "The server is shutting down"
INVALID_COMMAND             = "An invalid command was recieved from %s"
ALREADY_CONNECTED           = "A chat with %s is already open"
UNKNOWN_ERROR               = "An unknown error occured with %s"
EMPTY_NICK                  = "Please enter a nickname"
NETWORK_ERROR               = "A network error occured while communicating with the server. Try connecting to the server again."
BAD_HMAC                    = "Warning: Automatic data integrity check failed. Someone may be tampering with your conversation."

# Error codes
ERR_CONNECTION_ENDED    = 0
ERR_NICK_NOT_FOUND      = 1
ERR_CONNECTION_REJECTED = 2
ERR_BAD_HANDSHAKE       = 3
ERR_CLIENT_EXISTS       = 4
ERR_SELF_CONNECT        = 5
ERR_SERVER_SHUTDOWN     = 6
ERR_INVALID_COMMAND     = 7
ERR_ALREADY_CONNECTED   = 8
ERR_NETWORK_ERROR       = 9
ERR_BAD_HMAC            = 10
