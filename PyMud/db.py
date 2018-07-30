#!/usr/bin/python
"""
    PyMud/db.py - PyMud database handler
"""

import pickle, PyMud.multiqueue, PyMud.object, random, sqlite3, threading, time
from passlib.hash import pbkdf2_sha256

class Database(PyMud.multiqueue.MultiQueue, threading.Thread):
    def __init__(self, dbfile = "", initdb=True):
        PyMud.multiqueue.MultiQueue.__init__(self,('console', 'control', 'database', 'results'), 'console')
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
        self.enqueue('control', "shutdown")

    def do_shutdown(self):
        """
        Prepare the database for game shutdown
        """
        # self.conn.commit() # Do we really want to do this here?
        self.conn.close()

    def next_dbref(self):
        """
        Find the next (lowest) available dbref in the database
            This is thread-safe
        """
        self.enqueue('database', pickle.dumps(('next_dbref', '')))
        # Wait for results
        while self.hasqueued('results') == False:
            time.sleep(0.1)
        return pickle.loads(self.get_nowait('results'))

    def write_config(self, name, value):
        """
        Write a config value to the database
          This is thread-safe
        """
        if not str(name):
            raise ValueError("name must be a valid string: " + str(name))
        self.enqueue('database', pickle.dumps(('write_config', (name, value))))

    def read_config(self, name):
        """
        Read a config value from the database
          This is thread-safe
        """
        if not str(name):
            raise ValueError("name must be a valid string: " + str(name))
        self.enqueue('database', pickle.dumps(('read_config', str(name))))
        # Wait for results
        while self.hasqueued('results') == False:
            time.sleep(0.1)
        return pickle.loads(self.get_nowait('results'))

    def player_count(self):
        """
        Return a count of the players in the database
          This is thread-safe
        """
        self.enqueue('database', pickle.dumps(('player_count', '')))
        # Wait for results
        while self.hasqueued('results') == False:
            time.sleep(0.1)
        return pickle.loads(self.get_nowait('results'))

    def get_player(self, name):
        """
        Read a player from the database
          This is thread-safe
        """
        self.enqueue('database', pickle.dumps(('get_player', name)))

    def create_player(self, name, passwd):
        """
        Write a new player to the database
          This is thread-safe
        """
        # Hash the password
        pwhash = pbkdf2_sha256.encrypt(passwd, rounds=200000, salt_size=16)
        self.enqueue('database', pickle.dumps(('create_player',(name, pwhash))))

    def initdb(self):
        """
        Initialize the database with default values
          ONLY CALL FROM __init__()

        TODO:
          Thread-safe
          Only create tables if they don't exist
          Only populate tables if empty
        """
        # Everything
        self._execute("CREATE TABLE IF NOT EXISTS ids (id int UNIQUE, type text)")
        # Config
        dbver = 0.1
        self._execute("CREATE TABLE IF NOT EXISTS config (name text, value text)")
        # Populate minimum default values if needed
        if not self._read_config('DATABASE_VERSION'):
            self.write_config("DATABASE_VERSION", dbver)
        if not self._read_config('MUD_PORT'):
            self.write_config("MUD_PORT", 32767)
        # Rooms
        self._execute("CREATE TABLE IF NOT EXISTS rooms (id int, name text, color text, desc text)")
        # TODO: Get next dbref
        lid = 0
        lname = 'limbo'
        lcolor = random.randint(0,15)
        ldesc = ''
        self._execute("INSERT INTO rooms VALUES (" + str(lid) + ", '" + lname + "', " + str(lcolor) + ", '" + ldesc + "')")
        # Players
        self._execute("CREATE TABLE IF NOT EXISTS players (id int, name text, color text, desc text, channel text, channels text)")
        self._execute("CREATE TABLE IF NOT EXISTS passwd (name text, password text)")
        # Objects
        self._execute("CREATE TABLE IF NOT EXISTS objects (id int, name text, color text, desc text)")
        # Zones
        self._execute("CREATE TABLE IF NOT EXISTS zones (id int, name text, color text, desc text)")
        # channels
        self._execute("CREATE TABLE IF NOT EXISTS channels (id int, name text, color text)")
        # TODO: Get next dbref
        cid = 0
        cname = 'public'
        ccolor = random.randint(0, 15)
        self._execute("INSERT INTO channels VALUES (" + str(cid) + ", '" + cname + "', " + str(ccolor) + ")")
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

    def _next_dbref(self):
        """
        Find the next (lowest) available dbref in the database
            This is only meant to be called by the database threads
        """
        self.c.execute("SELECT min(id)+1 FROM ids WHERE id+1 NOT IN (SELECT id FROM ids)")
        return self.c.fetchall()

    def _read_config(self, name):
        """
        Read a config value from the database
          This is only meant to be called by the database thread
        """
        res = self._fetchall("SELECT value FROM config WHERE name=\'" + str(name) + "\'")
        # Return the first record [0], first field [0]
        if len(res):
            return res[0][0]
        else:
            return None

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

    def _get_player(self, name):
        """
        Read a player from the database, return a Player object
          This is only meant to be called by the database thread
        """
        res = self.fetchall("SELECT * FROM players WHERE name LIKE \'" + name + "\'")
        pid = res['id']
        pname = res['name']
        pcolor = res['color']
        pdesc = res['desc']
        pchannel = res['channel']
        pchannels = res['channels'].split(" ")
        po = PyMud.object.Player(pid, pname, color=pcolor, desc=pdesc, channel=pchannel, channels=pchannels)
        return po

    def _create_player(self, name, passwd):
        """
        Write a new player to the database
          This is only meant to be called by the database thread
        """
        # TODO: We really need to get the next available database number...
        pnum = 0
        pcolor = random.randint(0, 15)
        pdesc = ""
        pchans = ["public"]
        self._execute("INSERT INTO players VALUES (" + str(pnum) + ",'" + str(name) + "'," + str(pcolor) + ",'" + pchans[0] + "','" + " ".join(pchans) + "')")
        self._execute("INSERT INTO passwd VALUES (" + str(pnum) + ",'" + passwd + "')")

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
                cmd, val = pickle.loads(self.get_nowait('database'))
                if cmd == 'read_config':
                    self.enqueue('results', pickle.dumps(self._read_config(val)))
                elif cmd == 'write_config':
                    name, val = val
                    self._write_config(name, val)
                elif cmd == 'player_count':
                    self.enqueue('results', pickle.dumps(self._player_count()))
                elif cmd == 'get_player':
                    self.enqueue('results', pickle.dumps(self._get_player(val)))
                elif cmd == 'create_player':
                    name, val = val
                    self._create_player(name, val)
                else:
                    self.console("WARNING: Unknown 'database' command: " + str(cmd))
