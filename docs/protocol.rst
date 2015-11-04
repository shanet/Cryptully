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
  * ``error``: The error code, if applicable
  * ``num``: The message number, starting from 0 and monotonically increasing with sequential numbers.

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

* ``VERSION``: Tell the server what protocol version the client is using
* ``REG``: Register a nickname with the server
* ``REL``: Relay a message to the client as specified in the ``destClient`` field

^^^^^^^^^^^^^^^
Client Commands
^^^^^^^^^^^^^^^

* ``HELO``: The first command denotes the initation of a new connection with a client
* ``REDY``: The client is ready to initiate a handshake
* ``REJ``: If the client rejected a connection from another client
* ``PUB_KEY [arg]``
* ``SMP0 [arg]``: The question the SMP initiator is asking
* ``SMP1 [arg]``
* ``SMP2 [arg]``
* ``SMP3 [arg]``
* ``SMP4 [arg]``
* ``MSG [arg]``: The user has sent a chat message
* ``TYPING [arg]``: The user is currently typing or has stopped typing
* ``END``
* ``ERR``

^^^^^^^^^^^^^
Typing Status
^^^^^^^^^^^^^

A client may optional give the typing status of the user to the remote client by issuing the ``TYPING``
command. The ``TYPING`` command takes one of three possible arguments:

* ``0``: The user is currently typing
* ``1``: The user has stopped typing and deleted all text from the buffer
* ``2``: The user has stopped typing, but left some text in the buffer

------------------
Encryption Details
------------------

* 4096-bit prime is used to generate and exchange a shared secret via Diffie-Hellman.
* An AES key is the first 32 bytes of the SHA512 digest of the Diffie-Hellman secret. The IV last 32 bytes of this hash.
* All AES operations are with a 256-bit key in CBC mode.
* HMAC's are the SHA256 digest of the AES key and the encrypted message payload. The receiver calculates
  and verifies the HMAC before attempting to decrypt the message payload.


^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Socialist Millionaire Protocol
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The Socialist Millionaire Protocol (SMP) is a method for determining whether two clients share the same secret,
but without exchanging the secret itself. In |project|'s case, it is used to determine whether a MITM
attack has occurred or is occurring and compromised the Diffie-Hellman key exchange protocol.

The innards of the SMP is relatively complex so it is best to defer to the documentation of it's implementation
as defined in the Off-The-Record (OTR) protocol version 3.

|project|'s implementation uses the following commands:

+--------+---------+--------+
|Client A|direction|Client B|
+========+=========+========+
|        |   <-    |SMP0    |
+--------+---------+--------+
|        |   <-    |SMP1    |
+--------+---------+--------+
|SMP2    |   ->    |        |
+--------+---------+--------+
|        |   <-    |SMP3    |
+--------+---------+--------+
|SMP4    |   ->    |        |
+--------+---------+--------+

``SMP0`` contains the question the initiator is asking. The remaining commands may be sent at any time, as long as they are
completed in order and another SMP request is not started before the previous one is completed.

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
|(switch to AES encryption) |
+--------+---------+--------+


The client may reject a connection with the ``REJ`` command instead of sending the ``REDY`` command.

--------------------
Message Loop Details
--------------------

Clients may send messages any order including multiple messages in a row.

+--------+---------+--------+
|Client A|direction|Client B|
+========+=========+========+
|MSG     |   <->   |MSG     |
+--------+---------+--------+
|TYPING  |   <->   |TYPING  |
+--------+---------+--------+
|END     |   <->   |END     |
+--------+---------+--------+
