Using Cryptully
===============

-----------------
Getting Cryptully
-----------------

The first step is downloading Cryptully. To do that, head over to the downloads page. Cryptully is
available for Linux, Windows, and OS X. Just download the file and run it. No need to install anything
or create any accounts.

----------------------
Connecting to a friend
----------------------

Cryptully uses what's called a client-server model where one person (the client) connects directly
to the other person's computer (the server). This is different from most other chat server where
both people (clients) connect to a central server.

Let's run through the process of connecting with a friend.

1. When you first open Cryptully, you'll see the following screen:

TODO: Insert image of mode dialog

2. Person A should select "Wait for connection". The following waiting dialog shows up:

TODO: Insert image of waiting dialog

3. Person B should select "Connect to friend". The following prompt is shown:

4. Person A then tells Person B the IP address that is shown in the waiting dialog. Person B enters
   that in the prompt.

5. If the connection was succesful, person A will see a dialog asking to accept or reject the connection.

TODO: Insert image of accept dialog

6. Upon accepting the connection, person A and person B are chatting securely!

**But**, after connecting, you should always verify encrytion key integrity of the person you're
chatting with to ensure no one is listening in on your conversation. Keep reading to learn how to do that.

----------------------------------
Verifying encryption key integrity
----------------------------------

A common attack against encryption is called the man-in-the-middle attack. To protect against
this, it is highly recommended to verify the integrity of the encryption key of the person you're
chatting with. Fortunately, this is very simple.

1. Select the ``Verify key integrity`` option from the options menu.

TODO: Insert image of the options menu

2. You and your friend need to exchange the sequence of numbers and letters under the
   "You read to them" heading. A good way of doing this is over the phone so you can verify
   the voice of your friend. Other options include text message or email (but telephone is preferred
   if possible).

TODO: Insert image of fingerprint dialog

3. If both sequences match, you're chatting securely! If not, someone is likely listening to your
   communcations and you should disconnect immediately.

**Note:** You should verify the identity of your friend every time you connect to him/her since
a new encryption key is generated each time the application is started, the sequence of letters and
numbers you exchanged will change. You can avoid this by saving the encryption keys and then it's
only necessary to exchange this info once, but you should still make sure that the "they read to you"
section is the same for all subsequent connections. See the saving encryption keys section below.

----------------------
Saving encryption keys
----------------------

Cryptully generates new encryption keys each time it is started. This means that you would need to
verify the key integrity each time you make a connection with someone. However, you can save the
generated encryption keys so they are used to subsequent connections. Then you only need to verify
key integrity during the first connection.

To save your encryption keys:

1. You and your friend should go through the verification of encryption key integrity as described
   in the above section.
2. Save (or write down) the sequence from the "they read to you" part of the integriy verification
   process.
3. Both you and your friend save your keys by selecting the "Save keys" option in the option menu.
4. Your encryption keys are secret things. To protect them, Cryptully will encrypt the encryption
   keys (yes, it sounds weird, but it's safe!). Enter a passphrase to protect them. You'll need
   this the each time you start Cryptully now.
5. Each subsequent time you connect to you friend, you can now verify the sequence in the "they
   read to you section" with the one you wrote down.

If you ever want to generate new encryption keys, just select "Clear keys" from the options menu.
