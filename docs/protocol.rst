.. _protocol:

Protocol
========

This is an overview of |project|'s protocol for easier understanding the code, or so someone
could implement another type of client.

**Note: This protocol is highly likely to change in the future.**

----------------
Basic Properties
----------------

* Commands are in the form of ``/[command] [argument]``

  * The space between the command and argument is required even if an argument is not present.

* All commands *are* case sensitive
* After the initial handshake is complete, the connection is kept alive indefinitely in a message loop until
  either the client or server sends the ``END`` command.
* The client or server may send the ``END`` command at any time.
* Currently, multiple connections to the server are not supported. If a client tries to connect to
  a server which already has a client, the ``ERR`` command is returned.

--------------------
List of All Commands
--------------------

``[arg]`` denotes that the command has a single argument.

* ``HELO``
* ``REDY``
* ``PUB_KEY [arg]``
* ``AES_KEY [arg]``
* ``AES_IV [arg]``
* ``AES_SALT [arg]``
* ``MSG [arg]``
* ``END``
* ``ERR``

-----------------
Handshake Details
-----------------

The commands in the handshake must be performed in the following order:

+--------+---------+-------+
|Server  |direction| Client|
+========+=========+=======+
|        |   <-    |HELO   |
+--------+---------+-------+
|REDY    |   ->    |       |
+--------+---------+-------+
|        |   <-    |PUB_KEY|
+--------+---------+-------+
|PUB_KEY |   ->    |       |
+--------+---------+-------+
|(switch to RSA encryption)|
+--------+---------+-------+
|AES_KEY |   ->    |       |
+--------+---------+-------+
|AES_IV  |   ->    |       |
+--------+---------+-------+
|AES_SALT|   ->    |       |
+--------+---------+-------+
|(switch to AES encryption)|
+--------+---------+-------+

--------------------
Message Loop Details
--------------------

The client/server may send message is any order including multiple messages in a row.

+--------+---------+-------+
|Server  |direction| Client|
+========+=========+=======+
|MSG     |   <->   |MSG    |
+--------+---------+-------+
|END     |   <->   |END    |
+--------+---------+-------+
