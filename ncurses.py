#! /usr/bin/env python

import curses
import curses.ascii
import curses.textpad

import utils
import threads
import Crypto
import Exceptions

from Server    import Server
from EncSocket import EncSocket


def main(screen):
    (height, width) = screen.getmaxyx()

    # Change the colors, clear the screen and set the overall border
    setColors(screen)
    screen.clear()
    screen.border(0)

    # Create the status and chat input windows
    chatWindow               = makeChatWindow(screen, 1, 1, height-4, width-2)
    statusWindow             = makeStatusWindow(screen, height-3, width-23)
    (textboxWindow, textbox) = makeChatInputWindow(screen, height-2, 1, 1, width-25)

    screen.refresh()

    server = startServer()
    client = server.accept()

    utils.doServerHandshake(client)

    threads.CursesSendThread(client, chatWindow, textboxWindow, textbox).start()
    threads.CursesRecvThread(client, chatWindow, textboxWindow).start()


def setColors(screen):
    if curses.has_colors():
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED,   curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLUE,  curses.COLOR_BLACK)
        screen.bkgd(curses.color_pair(1))


def makeChatWindow(screen, y, x, height, width):
    chatWindow = screen.subwin(height, width, y, x)
    chatWindow.scrollok(True)
    return chatWindow


def makeStatusWindow(screen, y, x):
    statusWindow = screen.subwin(y, x)
    statusWindow.border(0)
    statusWindow.addstr(1, 1, "Disconnected")
    return statusWindow


def makeChatInputWindow(screen, y, x, height, width):
    textboxWindow = screen.subwin(height, width, y, x)
    textbox = curses.textpad.Textbox(textboxWindow, insert_mode=True)
    curses.textpad.rectangle(screen, y-1, x-1, y+height, x+width)
    textboxWindow.move(0, 0)
    return (textboxWindow, textbox)


def startServer():
    try:
        server = Server()
        server.startServer(9000)
    except Exceptions.GenericError as ge:
        print "Error starting server: " + str(ge)
        sys.exit(1)

    return server

curses.wrapper(main)
