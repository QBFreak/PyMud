#!/usr/bin/python
"""
    PyMud/db.py - PyMud database handler
"""

import cPickle as Pickle, multiqueue, sqlite3, threading, time

class Database(multiqueue.MultiQueue, threading.Thread):
    def __init__(self, dbfile = "", initdb=True):
        multiqueue.MultiQueue.__init__(self,('console', 'control', 'database', 'results'), 'console')
        threading.Thread.__init__(self)
        self.started = False
        if dbfile == "":
            dbfile = "pymud.db"
        self.file = dbfile
        self.conn = sqlite3.connect(dbfile)
        self.c = self.conn.cursor()
        if initdb:
            try:
                dbver = self._read_config("DATABASE_VERSION")
            except sqlite3.OperationalError:
                self.initdb()
        # Close the connection so we can reopen it as the thread
        self.conn.close()

    def console(self, msg):
        "Enqueue a message for console output"
        self.enqueue('console', str(msg))

    def shutdown(self):
        """
        Tell the database thread it's time to shutdown
        """
        self.enqueue('control', "shutdown", newline=False)

    def do_shutdown(self):
        """
        Prepare the database for game shutdown
        """
        # self.conn.commit() # Do we really want to do this here?
        self.conn.close()

    def write_config(self, name, value):
        """
        Write a config value to the database
          This is thread-safe
        """
        if not str(name):
            raise ValueError("name must be a valid string: " + str(name))
        self.enqueue('database', Pickle.dumps(('write_config', (name, value))))

    def read_config(self, name):
        """
        Read a config value from the database
          This is thread-safe
        """
        if not str(name):
            raise ValueError("name must be a valid string: " + str(name))
        self.enqueue('database', Pickle.dumps(('read_config', str(name))))
        # Wait for results
        while self.hasqueued('results') == False:
            time.sleep(0.1)
        return Pickle.loads(self.get_nowait('results'))

    def player_count(self):
        """
        Return a count of the players in the database
          This is thread-safe
        """
        self.enqueue('database', Pickle.dumps(('player_count', '')))
        # Wait for results
        while self.hasqueued('results') == False:
            time.sleep(0.1)
        return Pickle.loads(self.get_nowait('results'))

    def initdb(self):
        """
        Initialize the database with default values
          ONLY CALL FROM __init__()

        TODO:
          Thread-safe
          Only create tables if they don't exist
          Only populate tables if empty
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

    def _fetchall(self, query):
        """
        Return results of query, wrapper for sqlite3 cursor.fetchall
        """
        self.c.execute(query)
        return self.c.fetchall()

    def _execute(self, query):
        """
        Execute a query, wrapper for sqlite3 cursor.execute, followed up with
            a connection.commit
        """
        self.c.execute(query)
        self.conn.commit()

    def _read_config(self, name):
        """
        Read a config value from the database
          This is only meant to be called by the database thread
        """
        res = self._fetchall("SELECT value FROM config WHERE name=\'" + str(name) + "\'")
        # Return the first record [0], first field [0]
        return res[0][0]

    def _write_config(self, name, value):
        """
        Write a config value to the database
          This is only meant to be called by the database thread
        """
        self._execute("INSERT INTO config VALUES (\'" + str(name) + "\', \'" + str(value) + "\')")

    def _player_count(self):
        """
        Return a count of the players in the database
          This is only meant to be called by the database thread
        """
        res = self._fetchall("SELECT COUNT(*) FROM players")
        # Return the first record [0], first field [0]
        return [0][0]

    def run(self):
        """
        Database main thread
        """
        self.started = False
        self.console("Database started")
        self.conn = sqlite3.connect(self.file)
        self.c = self.conn.cursor()
        self.started = True
        while True:
            # Don't max out the processor with our main loop
            time.sleep(0.1)
            # Check the control queue for commands
            while self.hasqueued('control'):
                cmd = self.get_nowait('control')
                if cmd == 'shutdown':
                    # Shut down the network thread
                    self.do_shutdown()
                    self.console("Database stopped")
                    return
                else:
                    # Whaaat? I don't know how to do that
                    self.console("WARNING: Unknown control issued to Database: " + str(cmd))
            # Check the database queue
            while self.hasqueued('database'):
                cmd, val = Pickle.loads(self.get_nowait('database'))
                if cmd == 'read_config':
                    self.enqueue('results', Pickle.dumps(self._read_config(val)))
                elif cmd == 'write_config':
                    name, val = val
                    self._write_config(name, val)
                elif cmd == 'player_count':
                    self.enqueue('results', Pickle.dumps(self._player_count()))
                else:
                    self.console("WARNING: Unknown 'database' command: " + str(cmd))
