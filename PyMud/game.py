#!/usr/bin/python
"""
    PyMud/game.py - PyMud client thread
"""
import pickle, PyMud.multiqueue, threading, time

class Game(PyMud.multiqueue.MultiQueue, threading.Thread):
    def __init__(self, net, db):
        PyMud.multiqueue.MultiQueue.__init__(self,('console', 'control', 'client'), 'console')
        threading.Thread.__init__(self)
        self.db = db
        self.net = net

        self.clientLock = threading.Lock()
        self.clientNum = 0
        self.clientList = {}

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
        self.enqueueString('console', str(msg), newline=newline)

    def send(self, clientnum, msg, newline=True):
        self.clientList[clientnum].send(msg, newline=newline)

    def shutdown(self):
        """
            Notify Game that it needs to shutdown
              This is thread-safe
        """
        self.enqueue('control', "shutdown")

    def connect(self, client):
        """
            Notify Game that a new client has connected
              This is thread-safe
        """
        self.clientLock.acquire()
        self.clientList[self.clientNum] = client
        self.enqueue('client', pickle.dumps(('NEW', self.clientNum)))
        self.clientNum += 1
        self.clientLock.release()

    def disconnect(self, client):
        """
            Notify Game that a client has disconnected
              This is thread-safe
        """
        self.clientLock.acquire()
        cnum = list(self.clientList.keys())[list(self.clientList.values()).index(client)]
        del self.clientList[cnum]
        self.enqueue('client', pickle.dumps(('CLOSED', cnum)))
        self.clientLock.release()

    def receive(self, client, data):
        """
            Notify Game that a client has received a line from the player
              This is thread-safe
        """
        # Use the lock to make sure nothing shifts around on us
        self.clientLock.acquire()
        cnum = list(self.clientList.keys())[list(self.clientList.values()).index(client)]
        self.clientLock.release()
        self.enqueue('client', pickle.dumps(('RECV', (cnum, data))))

    def createPlayer(self, clientnum, userInput=None, firstUser=False):
        """
            Prompt the connected user to create a new player
             Also handles subsequent input required to complete process
        """
        client = self.clientList[clientnum]
        if userInput == None:
            # Called for the first time, set it up
            client.status = "NEWPLAYER"
            self.console("New player creation", client=clientnum)
            if firstUser:
                # Looks like this is the first user in the database
                self.send(clientnum, "No players in the database.")
                # You really have to be local to create the first player, sorry!
                if str(client.address) != "127.0.0.1":
                    self.send(clientnum, "Please connect from localhost to create the admin player.")
                    client.shutdown()
                    return
                self.send(clientnum, "Admin player creation")
            # Back to normal (any) player creation
            self.send(clientnum, "")
            self.send(clientnum, "Please enter a player name: ", newline=False)
            # We're prompting for the username
            client.currentPrompt = 'username'
        else:
            if self.checkInput(client.currentPrompt, userInput, self.newUserPrompts):
                if client.currentPrompt == 'username':
                    # Record the username
                    client.bucketLock.acquire()
                    client.bitBucket['username'] = userInput
                    client.bucketLock.release()
                    # Next we need to prompt for a password
                    client.currentPrompt = 'password'
                    self.send(clientnum, "Please select a password: ", newline=False)
                    # TODO: Fix escape sequences and Unicode (shoot me now)
                    # client.echoOff()
                elif client.currentPrompt == 'password':
                    # client.echoOn()
                    # Record the password
                    client.bucketLock.acquire()
                    client.bitBucket['password'] = userInput
                    client.bucketLock.release()
                    # No more prompts
                    client.currentPrompt = ''
                    self.send(clientnum, "User creation completed.")
                    client.status = "GAME"
                    self.send(clientnum, "DEBUG: Your username is " + str(client.bitBucket['username']) + ", and your password is " + str(client.bitBucket['password']))
                    self.db.create_player(str(client.bitBucket['username']), str(client.bitBucket['password']))
                    # Lets not keep the unhashed password around any longer than necessary
                    client.bucketLock.acquire()
                    del client.bitBucket['password']
                    client.bucketLock.release()
                else:
                    # Blork (they want us to do WHAT now?)
                    self.send(clientnum, "Error creating new player!")
                    client.currentPrompt = ""
            else:
                # User input didn't pass validation
                self.send(clientnum, "Invalid value, please try again.")

    def login(self, clientnum):
        "Prompt the connected user to log in as an existing player"
        self.console("login", client=clientnum)
        self.send(clientnum, "LOGIN")
        # TODO: HA! This is not a login prompt...

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
                ## the queue contains pickled ('STATUS', param[, optional params, ...])
                status, params = pickle.loads(self.get_nowait('client'))
                if status == "NEW":
                    self.console("Client " + str(params) + " connected to game", client=params)
                    pc = self.db.player_count()
                    if pc == 0:
                        # We need to create a player!
                        self.createPlayer(params, firstUser=True)
                    else:
                        # Log the player in
                        self.login(params)
                elif status == "CLOSED":
                    self.console("Client " + str(params) + " disconnected from game")
                elif status == "RECV":
                    cnum, data = params
                    self.console("RECV: " + str(data), client=cnum)
                    if self.clientList[cnum].status == "NEWPLAYER":
                        self.createPlayer(cnum, data)
                else:
                    self.console("Game: I don't know what to do with client status " + str(status))
