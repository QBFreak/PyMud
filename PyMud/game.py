#!/usr/bin/python
"""
    PyMud/game.py - PyMud client thread
"""
import cPickle as Pickle, multiqueue, threading, time

class Game(multiqueue.MultiQueue, threading.Thread):
    def __init__(self, db, net):
        multiqueue.MultiQueue.__init__(self,('console', 'control', 'client'), 'console')
        threading.Thread.__init__(self)
        self.db = db
        self.net = net

        self.clientLock = threading.Lock()
        self.clientNum = 0
        self.clientList = {}

        # Errrr. This needs to be multi-socket, not single...
        self.currentPrompt = None
        self.newUserPrompts = {
            'promptorder':('username', 'password'),
            'username':str(),
            'password':str()
        }

    def checkInput(self, name, value, prompts):
        if not name in prompts:
            raise NameError("No prompt named " + str(name))
        fmt = prompts[name]
        if fmt == str():
            if type(value) == type(fmt):
                return True
            else:
                return False
        else:
            raise ValueError("Unknown format " + str(fmt))

    def console(self, msg, newline=True, client=None):
        """
            Notify the main thread to display a message on the console
              This is thread-safe
        """
        if not client == None:
            msg = "[" + str(self.clientList[client].address) + ":" + str(self.clientList[client].port) + "]: " + str(msg)
        self.enqueue('console', str(msg), newline=newline)

    def shutdown(self):
        """
            Notify Game that it needs to shutdown
              This is thread-safe
        """
        self.enqueue('control', "shutdown", newline=False)

    def connect(self, client):
        """
            Notify Game that a new client has connected
              This is thread-safe
        """
        self.clientLock.acquire()
        self.clientList[self.clientNum] = client
        self.enqueue('client', Pickle.dumps(('NEW', self.clientNum)), newline=False)
        self.clientNum += 1
        self.clientLock.release()

    def disconnect(self, client):
        """
            Notify Game that a client has disconnected
              This is thread-safe
        """
        self.clientLock.acquire()
        # if client in self.clientList:
        cnum = self.clientList.keys()[self.clientList.values().index(client)]
        del self.clientList[cnum]
        self.enqueue('client', Pickle.dumps(('CLOSED', cnum)), newline=False)
        self.clientLock.release()

    def createPlayer(self, userInput=None):
        """
            Prompt the connected user to create a new player
             Also handles subsequent input required to complete process
        """
        if userInput == None:
            self.console("New player creation")
            self.send("No players in the database.")
            if str(self.address) != "127.0.0.1":
                self.send("Please connect from localhost to create the admin player.")
                self.shutdown()
                return
            self.send("Admin player creation")
            self.send("")
            self.send("Please enter a player name: ", newline=False)
            self.currentPrompt = 'username'
        else:
            if checkInput(self.currentPrompt, userInput, self.newUserPrompts):
                if self.currentPrompt == 'username':
                    self.currentPrompt = 'password'
                    self.send("Please select a password: ", newline=False)
                else:
                    self.send("Error creating new player!")
                    self.currentPrompt = ""
            else:
                self.send("Invalid value, please try again.")

    def login(self):
        "Prompt the connected user to log in as an existing player"
        ### TODO: DO NOT USE!
        foo = foo
        # self.console(str(self.address) + ":" + str(self.port) + " login")
        # self.send("LOGIN")

    def run(self):
        """
            Game main thread
        """
        self.console("Game started")
        while True:
            # Don't max out the processor with our main loop
            time.sleep(0.1)
            # Check the control queue for commands
            while self.hasqueued('control'):
                cmd = self.get_nowait('control')
                if cmd == 'shutdown':
                    # Shut down the game thread
                    self.console("Game stopped")
                    return
                else:
                    # Whaaat? I don't know how to do that
                    self.console("WARNING: Unknown control issued to Game: " + str(cmd))
            # Check the client queue for new clients
            while self.hasqueued('client'):
                ## the queue contains Pickled ('STATUS', param[, optional params, ...])
                status, params = Pickle.loads(self.get_nowait('client'))
                if status == "NEW":
                    self.console("Client " + str(params) + " connected to game", client=params)
                elif status == "CLOSED":
                    self.console("Client " + str(params) + " disconnected from game")
                else:
                    self.console("Game: I don't know what to do with client status " + str(status))
