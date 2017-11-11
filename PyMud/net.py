#!/usr/bin/python
"""
    PyMud/net.py - PyMud networking code
"""
import multiqueue, threading, time

class Network(multiqueue.MultiQueue, threading.Thread):
    def __init__(self, port=32767):
        multiqueue.MultiQueue.__init__(self,('console', 'control'), 'console')
        threading.Thread.__init__(self)
        self.port = port

    def console(self, msg):
        "Enqueue a message for console output"
        self.enqueue('console', str(msg))

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
