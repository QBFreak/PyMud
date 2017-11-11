#!/usr/bin/python
"""
    pymud.py - PyMud main file
"""
import sys
import PyMud.db, PyMud.net

db = PyMud.db.Database()
portNum = db.read_config("MUD_PORT")

net = PyMud.net.Network(port=portNum)

while net.hasqueued('console'):
    sys.stdout.write(net.get_nowait('console'))
