import os
import signal

from threading import Thread

class Console(Thread):
    def __init__(self, nickMap, ipMap):
        Thread.__init__(self)
        self.nickMap = nickMap
        self.ipMap = ipMap
        self.daemon = True

        self.commands = {
            'list': {
                'callback': self.list,
                'help': 'list\t\tlist active connections'
            },
            'zombies': {
                'callback': self.zombies,
                'help': 'zombies\t\tlist zombie connections'
            },
            'kick': {
                'callback': self.kick,
                'help': 'kick [nick]\tkick the given nick from the server'
            },
            'kill': {
                'callback': self.kill,
                'help': 'kill [ip]\tkill the zombie with the given IP'
            },
            'stop': {
                'callback': self.stop,
                'help': 'stop\t\tstop the server'
            },
            'help': {
                'callback': self.help,
                'help': 'help\t\tdisplay this message'
            },
        }


    def run(self):
        while True:
            try:
                input = input(">> ").split()

                if len(input) == 0:
                    continue

                command = input[0]
                arg = input[1] if len(input) == 2 else None

                self.commands[command]['callback'](arg)
            except EOFError:
                self.stop()
            except KeyError:
                print("Unrecognized command")


    def list(self, arg):
        print("Registered nicks")
        print("================")

        for nick, client in self.nickMap.items():
            print(nick + " - " + str(client.sock))


    def zombies(self, arg):
        print("Zombie Connections")
        print("==================")

        for addr, client in self.ipMap.items():
            print(addr)


    def kick(self, nick):
        if not nick:
            print("Kick command requires a nick")
            return

        try:
            client = self.nickMap[nick]
            client.kick()
            print("%s kicked from server" % nick)
        except KeyError:
            print("%s is not a registered nick" % nick)


    def kill(self, ip):
        if not ip:
            print("Kill command requires an IP")
            return

        try:
            client = self.ipMap[ip]
            client.kick()
            print("%s killed" % ip)
        except KeyError:
            print("%s is not a zombie" % ip)


    def stop(self, arg=None):
        os.kill(os.getpid(), signal.SIGINT)


    def help(self, arg):
        delimeter = '\n\t'
        helpMessages = [__command[1]['help'] for __command in iter(self.commands.items())]
        print("Available commands:%s%s" % (delimeter, delimeter.join(helpMessages)))
