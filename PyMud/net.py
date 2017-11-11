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
        self.enqueue('console', str(msg))

    def run(self):
        self.console("Networking started on port " + str(self.port))
        runto = time.mktime(time.localtime()) + 5
        while time.mktime(time.localtime()) <= runto:
            time.sleep(0.1)
            while self.hasqueued('control'):
                cmd = self.get_nowait('control')
                if cmd == 'shutdown':
                    self.console('Shutting down')
                    self.console("Networking stopped")
                    return
                else:
                    self.console("WARNING: Unknown command issued to Network: " + str(cmd))
        self.console("Networking stopped")

    def shutdown(self):
        self.enqueue('control', "shutdown", newline=False)
