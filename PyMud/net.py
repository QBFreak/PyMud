#!/usr/bin/python
"""
    PyMud/net.py - PyMud networking code
"""
import client, multiqueue, socket, threading, time

class Network(multiqueue.MultiQueue, threading.Thread):
    def __init__(self, port=32767):
        multiqueue.MultiQueue.__init__(self,('console', 'control'), 'console')
        threading.Thread.__init__(self)
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('localhost', int(port)))
        self.socket.setblocking(False)
        self.socket.listen(5)
        self.clients = []

    def console(self, msg, newline=True):
        "Enqueue a message for console output"
        self.enqueue('console', str(msg), newline=newline)

    def shutdown(self):
        "Enqueue the shutdown command in the command queue"
        self.enqueue('control', "shutdown", newline=False)

    def run(self):
        """
        Network main thread
        """
        self.console("Networking started on port " + str(self.port))
        while True:
            # Don't max out the processor with our main loop
            time.sleep(0.1)
            # Check the control queue for commands
            while self.hasqueued('control'):
                cmd = self.get_nowait('control')
                if cmd == 'shutdown':
                    # Shut down the network thread
                    self.console('Shutting down')
                    self.console("Networking stopped")
                    return
                else:
                    # Whaaat? I don't know how to do that
                    self.console("WARNING: Unknown command issued to Network: " + str(cmd))
            # Pass on console messages from clients
            for c in self.clients:
                while c.hasqueued('console'):
                    self.console(c.get_nowait('console'), newline=False)
            # Accept sockets
            try:
                (clientsocket, address) = self.socket.accept()
                clientthread = client.Client(clientsocket, address)
                clientthread.run()
                self.clients.append(clientthread)
            except socket.error, err:
                # [Errno 11] Resource temporarily unavailable
                #  That is to say, no error and no connection to accept
                if err.errno != 11:
                    self.console("NETWORK: " + str(err))
