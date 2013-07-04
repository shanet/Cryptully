.. Cryptully documentation master file, created by
   sphinx-quickstart on Mon Jul  1 00:15:49 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to |project|'s documentation!
=====================================

------------
Introduction
------------

|project| is an encrypted chat program meant for secure conversations between two people
with no knowledge of cryptography needed.

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
How does it work and how is it secure?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

|project| is a client/server program. That is, one person connects to another person's computer and
data is relayed between those two computer directly (no intermediate servers). When the program
starts it generates encryption keys (2048bit RSA and 256bit AES) that all communications are encrypted
with before leaving your computer and then decrypted on your friend's computer. Further, to ensure that
no one is listening in on your conversation, the fingerprints of the encryption keys are provided.
You can use this to verify with your friend that no one is listening. More on this in the usage
section though.

--------
Features
--------

* Provides basic encrypted chat with no requisite knowledge of cryptography
* Runs on Linux, Windows, and Mac OS X
* Ability to set own RSA keys
* Graphical UI and command line (Curses) UI
* Open source (LGPL license)

-----------
Quick Start
-----------

1. Download the executable for your platform on the downloads page.
2. Launch the executable (no need to install anything).
3. One person selects "Wait for connection" (make sure port 9000 is forwarded if necessary).
4. The other person selects "Connect to friend" and enters the IP address to connect to.
5. You should now be chatting! (but you should verify the key integrity in the options menu)

Need more info? See the :ref:`using-|project|` page for much more detailed instructions.

-------------------------------------
Doesn't encrypted chat already exist?
-------------------------------------

Yup, it does. There are plenty of other encrypted chat programs so what's the point of |project|?
The problem is just that, there's plenty of other chat programs. There's too many options
for chating with another person. Other solutions require downloading and installing software, creating
accounts, etc. With |project|, you just download and run the software. No need to install anything or
create an account. Just enter the IP address of the person you want to chat with and you're off.

Another advantage is that |project| is a relatively simple program and is open source. For the paranoid,
you can inspect the source code to ensure that |project| is not doing anything nefarious.

--------
Contents
--------

.. toctree::
   :maxdepth: 2

   downloads
   usage
   building

----------
Contribute
----------

If you would like contribute to |project|, see the building page on how to set up a build environment
and get the source code.

Any issues encountered may be reported at https://github.com/shanet/Cryptully/issues.
