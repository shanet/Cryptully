.. _protocol:

Protocol
========

This is an overview of |project|'s protocol for easier understanding the code, or so someone
could implement another type of client.

**Note: This protocol is highly likely to change in the future.**

----------------
Basic Properties
----------------

* All traffic over the network is formatted as JSON messages with the following properties:

  * ``serverCommand``: The command given to the server
  * ``clientCommand``: The command given to the destination client
  * ``sourceNick``: The nickname of the sender
  * ``destNick``: The nickname of the receiver
  * ``payload``: The content of the message. If an encrypted message, it is base64 encoded
  * ``hmac``: The HMAC as calculated by the sender to be verified against by the receiver
  * ``iv``: If the payload is encrypted, the AES IV used for this message (base64 encoded and encrypted with RSA)
  * ``error``: The error code, if applicable

* All commands *are* case sensitive
* After the initial handshake is complete, the connection is kept alive indefinitely in a message loop until
  either the client or server sends the ``END`` command.
* The client or server may send the ``END`` command at any time.

--------------------
List of All Commands
--------------------

^^^^^^^^^^^^^^^
Server Commands
^^^^^^^^^^^^^^^

* ``REG``: Register a nickname with the server
* ``REL``: Relay a message to the client as specified in the ``destClient`` field

^^^^^^^^^^^^^^^
Client Commands
^^^^^^^^^^^^^^^

* ``HELO``: The first command denotes the initation of a new connection with a client
* ``REDY``: The client is ready to initiate a handshake
* ``REJ``: If the client rejected a connection from another client
* ``PUB_KEY [arg]``
* ``AES_KEY [arg]``
* ``AES_IV [arg]``
* ``AES_SALT [arg]``
* ``MSG [arg]``
* ``END``
* ``ERR``

------------------
Encryption Details
------------------

* AES is 256 bits in CBC mode with randomly generated key, IV and 8 byte salt.
* RSA is 2048 bits with a public exponent of 65537.
* RSA fingerprints are the MD5 digest of a client's public key.
* HMAC's are the SHA256 digest of the AES key and the encrypted message payload. The receiver calculates
  and verfies the HMAC before attempting to decrypt the message payload.
* Each client generates a unique RSA keypair and AES key for each connection. The exception being if the user
  saved an RSA keypair. Then each connection uses the same keypair, but an AES key is randomly generated for
  each connection.
* The AES IV is randomly generated for each message and sent along with the message encrypted with the RSA keys
  that are exchanged in the handshake.

-----------------
Handshake Details
-----------------

The commands in the handshake must be performed in the following order:

+--------+---------+--------+
|Client A|direction|Client B|
+========+=========+========+
|        |   <-    |HELO    |
+--------+---------+--------+
|REDY    |   ->    |        |
+--------+---------+--------+
|        |   <-    |PUB_KEY |
+--------+---------+--------+
|PUB_KEY |   ->    |        |
+--------+---------+--------+
|(switch to RSA encryption) |
+--------+---------+--------+
|AES_KEY |   ->    |        |
+--------+---------+--------+
|AES_SALT|   ->    |        |
+--------+---------+--------+
|(switch to AES encryption) |
+--------+---------+--------+

--------------------
Message Loop Details
--------------------

Clients may send messages any order including multiple messages in a row.

+--------+---------+-------+
|Server  |direction| Client|
+========+=========+=======+
|MSG     |   <->   |MSG    |
+--------+---------+-------+
|END     |   <->   |END    |
+--------+---------+-------+
