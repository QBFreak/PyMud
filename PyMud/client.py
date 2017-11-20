#!/usr/bin/python
"""
    PyMud/client.py - PyMud client thread
"""
import multiqueue, socket, threading, time

class Client(multiqueue.MultiQueue, threading.Thread):
    def __init__(self, socket, address, db):
        multiqueue.MultiQueue.__init__(self,('console', 'control', 'recv'), 'console')
        threading.Thread.__init__(self)
        self.status = "INIT"
        self.socket = socket
        self.address, self.port = address
        self.db = db

    def console(self, msg, newline=True, prefix=True):
        "Enqueue a message for console output"
        if prefix:
            msg = "[" + str(self.address) + ":" + str(self.port) + "]: " + str(msg)
        self.enqueue('console', str(msg), newline=newline)

    def shutdown(self):
        "Enqueue the shutdown command in the command queue"
        self.enqueue('control', "shutdown", newline=False)

    def send(self, msg, newline=True):
        "Send a message to the socket"
        try:
            self.socket.send(str(msg))
            if newline:
                self.socket.send("\n")
        except socket.error, e:
            if e.errno == 32:
                self.console("Broken pipe!")
            else:
                self.console("Error sending " + str(e))

    def createPlayer(self):
        "Prompt the connected user to create a new player"
        self.console(str(self.address) + ":" + str(self.port) + " new player creation")
        self.send("No players in the database.")
        if str(self.address) != "127.0.0.1":
            self.send("Please connect from localhost to create the admin player.")
            self.shutdown()
            return
        self.send("Admin player creation")
        self.send("")
        self.send("Please enter a player name: ", newline=False)


    def login(self):
        "Prompt the connected user to log in as an existing player"
        self.console(str(self.address) + ":" + str(self.port) + " login")
        self.send("LOGIN")

    def run(self):
        """
        Client main thread
        """
        self.status = "RUNNING"
        self.console("New client connected from " + str(self.address) + ":" + str(self.port))
        self.send("Welcome to PyMud")
        # self.send("Database version: " + str(self.db.read_config("DATABASE_VERSION")))
        # self.send("Player Count:     " + str(self.db.player_count()))
        # pc = self.db.player_count()
        # if pc == 0:
        #     # We need to create a player!
        #     self.createPlayer()
        # else:
        #     # Log the player in
        #     self.login()
        while True:
            # Don't max out the processor with our main loop
            time.sleep(0.1)
            # Check for user input
            # self.console("#", newline=False)
            # data = self.socket.recv(32)
            # self.console("-", newline=False)
            # if data:
            #     self.enqueue('recv', data)
            #     self.console("DEBUG: Recv: " + str(data))
            # Check the control queue for commands
            while self.hasqueued('control'):
                cmd = self.get_nowait('control')
                if cmd == 'shutdown':
                    # Shut down the network thread
                    self.socket.shutdown(socket.SHUT_RDWR)
                    self.socket.close()
                    self.console("Client stopped")
                    self.status = "SHUTDOWN"
                    return
                else:
                    # Whaaat? I don't know how to do that
                    self.console("WARNING: Unknown control issued to Client: " + str(cmd))
            # TESTING, Shut it down
            # self.shutdown()
