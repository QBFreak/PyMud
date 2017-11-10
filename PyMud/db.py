#!/usr/bin/python
"""
    PyMud/db.py - PyMud database handler
"""

import sqlite3

class Database:
    def __init__(self, dbfile = ""):
        if dbfile == "":
            dbfile = "pymud.db"
        self.file = dbfile
        self.conn = sqlite3.connect(dbfile)
        self.c = self.conn.cursor()

    def shutdown(self):
        """
        Prepare the database for game shutdown
        """
        # self.conn.commit() # Do we really want to do this here?
        self.conn.close()

    def fetchall(self, query):
        """
        Return results of query, wrapper for sqlite3 cursor.fetchall
        """
        self.c.execute(query)
        return self.c.fetchall()

    def execute(self, query):
        """
        Execute a query, wrapper for sqlite3 cursor.execute, followed up with
            a connection.commit
        """
        self.c.execute(query)
        self.conn.commit()

    def write_config(self, name, value):
        """
        Write a config value to the database
        """
        if not str(name):
            raise ValueError("name must be a valid string: " + str(name))
        self.execute("INSERT INTO config VALUES (\'" + str(name) + "\', \'" + str(value) + "\')")

    def read_config(self, name):
        """
        Read a config value from the database
        """
        if not str(name):
            raise ValueError("name must be a valid string: " + str(name))
        res = self.fetchall("SELECT value FROM config WHERE name=\'" + str(name) + "\'")
        # Return the first record [0], first field [0]
        return res[0][0]

    def initdb(self):
        """
        Initialize the database with default values
        """
        # Config
        dbver = 0.1
        self.execute("CREATE TABLE config (name text, value text)")
        self.write_config("DATABASE_VERSION", dbver)
        self.write_config("MUD_PORT", 32767)
        # Rooms
        self.execute("CREATE TABLE rooms (id int, name text, color text, desc text)")
        self.execute("INSERT INTO rooms VALUES (0, 'Limbo', 1, '')")
        # Players
        self.execute("CREATE TABLE players (id int, name text, color text, desc text, channel text, channels text)")
        # Objects
        self.execute("CREATE TABLE objects (id int, name text, color text, desc text)")
        # Zones
        self.execute("CREATE TABLE zones (id int, name text, color text, desc text)")
        # channels
        self.execute("CREATE TABLE channels (id int, name text, color text)")
        self.execute("INSERT INTO channels VALUES (0, 'public', 1)")
        return dbver
