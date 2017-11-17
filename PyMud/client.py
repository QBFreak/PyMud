#!/usr/bin/python
"""
    PyMud/client.py - PyMud client thread
"""
import multiqueue, socket, threading, time

class Client(multiqueue.MultiQueue, threading.Thread):
    def __init__(self, socket, address, db):
        multiqueue.MultiQueue.__init__(self,('console', 'control'), 'console')
        threading.Thread.__init__(self)
        self.socket = socket
        self.address, self.port = address
        self.db = db

    def console(self, msg):
        "Enqueue a message for console output"
        self.enqueue('console', str(msg))

    def shutdown(self):
        "Enqueue the shutdown command in the command queue"
        self.enqueue('control', "shutdown", newline=False)

    def send(self, msg, newline=True):
        "Send a message to the socket"
        self.socket.send(str(msg))
        if newline:
            self.socket.send("\n")

    def run(self):
        """
        Client main thread
        """
        self.console("New client connected from " + str(self.address) + ":" + str(self.port))
        self.send("TESTING")
        self.send("Database version: " + str(self.db.read_config("DATABASE_VERSION")))
        self.send("Player Count:     " + str(self.db.player_count()))
        while True:
            # Don't max out the processor with our main loop
            time.sleep(0.1)
            # Check the control queue for commands
            while self.hasqueued('control'):
                cmd = self.get_nowait('control')
                if cmd == 'shutdown':
                    # Shut down the network thread
                    self.console('Shutting down')
                    self.socket.shutdown(socket.SHUT_RDWR)
                    self.socket.close()
                    self.console("Client stopped")
                    return
                else:
                    # Whaaat? I don't know how to do that
                    self.console("WARNING: Unknown command issued to Client: " + str(cmd))
            # TESTING, Shut it down
            self.shutdown()
