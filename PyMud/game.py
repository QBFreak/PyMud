#!/usr/bin/python
"""
    PyMud/game.py - PyMud client thread
"""
import cPickle as Pickle, multiqueue, threading, time

class Game(multiqueue.MultiQueue, threading.Thread):
    def __init__(self, db, net):
        multiqueue.MultiQueue.__init__(self,('console', 'control', 'database', 'results'), 'console')
        threading.Thread.__init__(self)
        self.db = db
        self.net = net

    def console(self, msg, newline=True):
        "Enqueue a message for console output"
        self.enqueue('console', str(msg), newline=newline)

    def shutdown(self):
        "Enqueue the shutdown command in the command queue"
        self.enqueue('control', "shutdown", newline=False)

    def createPlayer(self):
        "Prompt the connected user to create a new player"
        self.console("New player creation")
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
                    # Shut down the network thread
                    self.console("Game stopped")
                    return
                else:
                    # Whaaat? I don't know how to do that
                    self.console("WARNING: Unknown control issued to Game: " + str(cmd))
