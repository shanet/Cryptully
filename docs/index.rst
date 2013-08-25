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

.. image:: images/chatting.png

--------
Features
--------

* Provides basic, encrypted chat with no prerequisite knowledge of cryptography
* Runs on Linux, Windows, and Mac OS X
* No registration or software installation required
* Chat with multiple people simultaneously
* Ability to host your own server (for the technically inclined)
* Graphical UI and command line (Curses) UI
* Open source (LGPL license)

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
How does it work and how is it secure?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

|project| works by relaying messages from one person to another through a relay server. It generates
per-session encryption keys (256bit AES) that all communications are encrypted with before leaving
your computer and then decrypted on the destination computer.

-----------
Quick Start
-----------

1. Download the executable for your platform on the :ref:`downloads` page.
2. Launch the executable (no need to install anything).
3. Select a nickname and connect to the server.
4. Enter the nickname of the person you want to chat with.
5. You should now be chatting!

Need more info? See the :ref:`using-|project|` page for much more detailed instructions.

-------------------------------------
Doesn't encrypted chat already exist?
-------------------------------------

Yup, it does. There are plenty of other encrypted chat programs so what's the point of |project|?
The problem is just that, there's plenty of other chat programs. There's too many options
for chating with another person. Other solutions require downloading and installing software, creating
accounts, etc. With |project|, you just download and run the software. No need to install anything or
create an account. Just enter the nickname of the person you want to chat with and you're off.

Another advantage is that |project| is a relatively simple program and is open source. For the paranoid,
you can inspect the source code to ensure that |project| is not doing anything nefarious or host your
own relay server.

--------
Contents
--------

.. toctree::
   :maxdepth: 2

   downloads
   usage
   building
   protocol

------------
Contributing
------------

For non-programmers:

Even if you're not writing code, you can still help! Submitting any issues or problems you run into
at https://github.com/shanet/Cryptully/issues or by emailing shane@shanetully.com. Even reporting something like
a section in the documentation not being as clear as it could be or just a typo is helpful.

For programmers:

If you would like contribute to |project|, see the :ref:`downloads` page on how to set up a build environment
and get the source code. Please any issues encountered at https://github.com/shanet/Cryptully/issues.
