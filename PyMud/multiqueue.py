"""
    PyMud/multiqueue.py - PyMud MultiQueue class

    Subclasses have multiple named Queue.Queue-s
    Gotcha warning: If you want only a single queue, make sure you place a comma
        after it in the list passed in queues= to the constructor. For example:
            queues=('console',)
        Otherwise you'll get a bunch of queues, one for each letter in the
        string: queues=('console') results in seven queues; c, o, n, s, o, l, e
"""

import Queue

class MultiQueue:
    def __init__(self, queues=(), defqueue=''):
        self.queues = {}
        for q in queues:
            self.queues[q] = Queue.Queue()
        if len(queues) and defqueue == '':
            defqueue = queues[0]
        self.defqueue = defqueue

    def enqueue(self, queue, data, newline=True):
        if queue == "":
            queue = self.defqueue
        if queue == "":
            raise ValueError("There are no queues defined")
        if not data:
            # raise ValueError("Nothing to add to queue")
            data = ""
        if queue in self.queues:
            if newline:
                self.queues[queue].put(str(data) + "\n")
            else:
                self.queues[queue].put(str(data))
            return True
        raise KeyError(queue + " is an invalid queue name")

    def hasqueued(self, queue):
        if queue in self.queues:
            if self.queues[queue].empty():
                return False
            else:
                return True
        raise KeyError(queue + " is an invalid queue name")

    def get_nowait(self, queue):
        if queue in self.queues:
            return self.queues[queue].get_nowait()
        raise KeyError(queue + " is an invalid queue name")
