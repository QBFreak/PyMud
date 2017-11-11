#!/usr/bin/python
"""
    pymud.py - PyMud main file
"""
import sys, time
import PyMud.db, PyMud.net

print("== PyMud server ==")

db = PyMud.db.Database()
portNum = db.read_config("MUD_PORT")

net = PyMud.net.Network(port=portNum)

net.start()
while net.is_alive():
    try:
        time.sleep(0.1)
        while net.hasqueued('console'):
            sys.stdout.write(net.get_nowait('console'))
    except KeyboardInterrupt:
        # print("You want to shut down")
        print("")
        net.shutdown()
