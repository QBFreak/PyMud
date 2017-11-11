#!/usr/bin/python
"""
    PyMud/net.py - PyMud networking code
"""
import multiqueue, threading, time

class Network(multiqueue.MultiQueue, threading.Thread):
    def __init__(self, port=32767):
        multiqueue.MultiQueue.__init__(self,('console',), 'console')
        threading.Thread.__init__(self)
        self.port = port

    def console(self, msg):
        self.enqueue('console', str(msg))

    def run(self):
        self.console("Networking started on port " + str(self.port))
        time.sleep(5)
        self.console("Networking stopped")
