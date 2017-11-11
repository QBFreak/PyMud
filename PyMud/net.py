#!/usr/bin/python
"""
    PyMud/net.py - PyMud networking code
"""
import multiqueue

class Network(multiqueue.MultiQueue):
    def __init__(self, port=32767):
        multiqueue.MultiQueue.__init__(self,('console',), 'console')
        # print("Networking started on port " + str(port))
        self.console("Networking started on port " + str(port))

    def console(self, msg):
        self.enqueue('console', str(msg))
