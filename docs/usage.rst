.. _using-|project|:

Using |project|
===============

-----------------
Getting |project|
-----------------

The first step is downloading |project|. To do that, head over to the :ref:`downloads` page. |project| is
available for Linux, Windows, and OS X. Just download the file and run it. No need to install anything
or create any accounts.

----------------------
Connecting to a friend
----------------------

|project| uses a central server to relay messages from one person to another.

Let's run through the process of connecting with a friend.

1. When you first open |project|, you'll see the following screen:

.. image:: images/login.png

2. Pick a nickname that will identify you to other people you'll chat with.

3. Once connected to the server, you may enter the nickname of someone you wish to chat with.

.. image:: images/new_chat.png

4. If the connection was succesful, the person being connected to will see a dialog asking to accept
   or reject the connection.

.. image:: images/accept_dialog.png

6. Upon accepting the connection, both people are chatting securely!

.. image:: images/chatting.png

**But**, after connecting, you should always verify encrytion key integrity of the person you're
chatting with to ensure no one is listening in on your conversation. See the
:ref:`verifying-encryption-key-integrity` section below.

.. _verifying-encryption-key-integrity:

----------------------------------
Verifying encryption key integrity
----------------------------------

A common attack against encryption is called the man-in-the-middle attack. To protect against
this, it is highly recommended to verify the integrity of the encryption keys of the person you're
chatting with. Fortunately, this is very simple.

First, let's understand what a fingerprint is. Encryption keys look very long to humans. In order to
make them more managable, we create a fingerprint of a key by doing some fancy math that takes a long
input and creates a short sequence of letters and numbers. Like a human's fingerprint, an encryption
key's fingerprint is unique and a good way of proving that you are chatting with who you think you're
chatting with.

1. Select the ``Verify key integrity`` option by clicking the key icon on the left hand side or from the options menu.

2. You and your friend need to exchange the sequence of numbers and letters under the
   "You read to them" heading. These are the key fingerprints. A good way of doing this is over the
   phone so you can verify the voice of your friend. Other options include text message or email
   (but telephone is preferred if possible) or even in person if you want to chat at some later time.

.. image:: images/fingerprint_dialog.png

3. If both fingerprints match, you're chatting securely! If not, someone is likely listening to your
   communcations and you should disconnect immediately.

**Note:** You should verify the identity of your friend every time you connect to him/her since
a new encryption key is generated each time the application is started, the fingerprints you
exchanged will change. You can avoid this by saving the encryption keys where it is then
only necessary to exchange this info once, but you should still make sure that the "they read to you"
section is the same for all subsequent connections. See the :ref:`saving-encryption-keys` section below.

.. _saving-encryption-keys:

----------------------
Saving encryption keys
----------------------

By default, |project| generates new encryption keys each time it is started. This means you should
exchange fingerprints in the verifying key integrity process described above. However, if you save
your encryption keys, your fingerprint won't change so you only need to exchange fingerprints once
and then you can check that the fingerprints you exchanged matches for all new connections.

To save your encryption keys:

1. You and your friend should go through the verification of encryption key integrity as described
   in the above section.
2. Save (or write down) the sequence from the "they read to you" part of the integriy verification
   process.
3. Both you and your friend save your keys by selecting the "Save keys" option in the options menu.
4. Your encryption keys are secret things. To protect them, |project| will encrypt the encryption
   keys (yes, it sounds weird, but it's safe!). Enter a passphrase to protect them. You'll need
   this the each time you start |project| now.
5. Each subsequent time you connect to your friend, you can now verify the fingerprint in the "they
   read to you section" with the one you originally exchanged with them.

If you ever want to generate new encryption keys, just select "Clear keys" from the options menu.

-------------------------------
Command Line Options (advanced)
-------------------------------

Advanced users may utilize command line options of |project|::

  usage: cryptully.py [-h] [-k [NICK]] [-r [TURN]] [-p [PORT]] [-s] [-n]
  
  optional arguments:
    -h, --help            show this help message and exit
    -k [NICK], --nick [NICK]
                          Nickname to use.
    -r [TURN], --relay [TURN]
                          The relay server to use.
    -p [PORT], --port [PORT]
                          Port to connect listen on (server) or connect to
                          (client).
    -s, --server          Run as TURN server for other clients.
    -n, --ncurses         Use the NCurses UI.


----------------------------------
Running Your Own Server (advanced)
----------------------------------

If you don't want to use the default relay server, you can host your own.

This is as easy as downloading a pre-built binary, or getting the source and running Cryptully with
the ``--server`` command line argument.
