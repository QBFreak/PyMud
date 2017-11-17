#!/usr/bin/python
"""
    pymud.py - PyMud main file
"""
import Queue, sys, time
import PyMud.db, PyMud.net

print("== PyMud server ==")

db = PyMud.db.Database()
# Start the database thread so we can actually USE it
db.start()
# Wait for the database to start
while not db.started:
    time.sleep(0.1)
portNum = db.read_config("MUD_PORT")

net = PyMud.net.Network(db, port=portNum)

net.start()
while net.is_alive() or db.is_alive():
    try:
        time.sleep(0.1)
        # Check for console messages from the Database object
        while db.hasqueued('console'):
            try:
                sys.stdout.write(db.get_nowait('console'))
            except Queue.Empty:
                pass
        # Check for console messages from the Network object
        while net.hasqueued('console'):
            try:
                sys.stdout.write(net.get_nowait('console'))
            except Queue.Empty:
                pass
        # Check for console messages from the Client objects
        for c in net.clients:
            while c.hasqueued('console'):
                try:
                    sys.stdout.write(c.get_nowait('console'))
                except Queue.Empty:
                    pass

    except KeyboardInterrupt:
        # print("You want to shut down")
        print("")
        net.shutdown()
        db.shutdown()
