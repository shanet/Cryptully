from threading import Thread

class Console(Thread):
    def __init__(self):
        Thread.__init__(self)
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
            input = raw_input(">> ").split()

            if len(input) == 0:
                continue

            command = input[0]
            arg = input[1] if len(input) == 2 else None

            try:
                self.commands[command]['callback'](arg)
            except KeyError:
                print "Unrecognized command"


    def list(self, arg):
        print "Registered nicks"
        print "================"
        for nick, client in nickMap.iteritems():
            print nick + " - " + str(client.sock)


    def zombies(self, arg):
        print "Zombie Connections"
        print "=================="
        for addr, client in ipMap.iteritems():
            print addr


    def kick(self, nick):
        if not nick:
            print "Kick command requires a nick"
            return

        try:
            client = nickMap[nick]
            client.kick()
            print "%s kicked from server" % nick
        except KeyError:
            print "%s is not a registered nick" % nick


    def kill(self, ip):
        if not ip:
            print "Kill command requires an IP"
            return

        try:
            client = ipMap[ip]
            client.kick()
            print "%s killed" % ip
        except KeyError:
            print "%s is not a zombie" % ip


    def stop(self, arg):
        os.kill(os.getpid(), signal.SIGINT)


    def help(self, arg):
        delimeter = '\n\t'
        helpMessages = map(lambda (_, command): command['help'], self.commands.iteritems())
        print "Available commands:%s%s" % (delimeter, delimeter.join(helpMessages))
