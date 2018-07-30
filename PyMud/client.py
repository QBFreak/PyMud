#!/usr/bin/python
"""
    PyMud/client.py - PyMud client thread
"""
import multiqueue, socket, threading, time

telnet = {}
telnet[240] = 'SE'
telnet[241] = 'NOP'
telnet[242] = 'Data Mark'
telnet[243] = 'Break'
telnet[244] = 'Interrupt Process'
telnet[245] = 'Abort output'
telnet[246] = 'Are You There'
telnet[247] = 'Erase character'
telnet[248] = 'Erase Line'
telnet[249] = 'Go ahead'
telnet[250] = 'SB'
telnet[251] = 'WILL (option code)'
telnet[252] = 'WON\'T (option code)'
telnet[253] = 'DO (option code)'
telnet[254] = 'DON\'T (option code)'
telnet[255] = 'IAC'

IAC_WONT_ECHO = '\xFF\xFC\x01'
IAC_WILL_ECHO = '\xFF\xFB\x01'

class Client(multiqueue.MultiQueue, threading.Thread):
    def __init__(self, socket, address, db, game):
        multiqueue.MultiQueue.__init__(self,('console', 'control', 'recv', 'send'), 'console')
        threading.Thread.__init__(self)
        self.status = "INIT"
        self.socket = socket
        self.address, self.port = address
        self.db = db
        self.game = game
        self.socket.setblocking(False)
        self.currentPrompt = None
        self.bitBucket = {}
        self.bucketLock = threading.Lock()

    def _send(self, msg):
        """
            Send a message to the socket
              Internal use - NOT thread-safe
              Threads should make use of Client.send(msg, [newline])
        """
        try:
            self.socket.send(str(msg))
        except socket.error, e:
            if e.errno == 32:
                self.console("Broken pipe!")
            else:
                self.console("Error sending " + str(e))

    def console(self, msg, newline=True, prefix=True):
        """
            Enqueue a message for console output
              This is thread-safe
        """
        if prefix:
            msg = "[" + str(self.address) + ":" + str(self.port) + "]: " + str(msg)
        self.enqueue('console', str(msg), newline=newline)

    def shutdown(self):
        """
            Enqueue the shutdown command in the command queue
              This is thread-safe
        """
        self.enqueue('control', "shutdown", newline=False)

    def send(self, msg, newline=True):
        """
            Send a message to the client
              This is thread-safe
        """
        self.enqueue('send', msg, newline=newline)

    def echoOff(self):
        """
            Turn off local-echo
                This is thread safe
        """
        # SERVER says it will echo, so client wont
        self.enqueue('send', IAC_WILL_ECHO, newline=False)

    def echoOn(self):
        """
            Turn on local-echo
                This is thread safe
        """
        # SERVER says it wont echo, so client will
        self.enqueue('send', IAC_WONT_ECHO, newline=False)

    def run(self):
        """
            Client main thread
        """
        self.status = "RUNNING"
        self.console("New client connected")
        self.game.connect(self)
        while True:
            # Don't max out the processor with our main loop
            time.sleep(0.1)
            # Check for user input
            data = None
            ###
            # So this bit here where we read the socket is ugly. Because sockets are ugly.
            #  First, if the socket is closed, the .recv() will return nothing
            #  Second, if the socket is normal with nothing to read, it will raise an exception
            #   Oh, but not just any exception, we have to check that e.errno is 11 to be sure
            # Please feel free to email me about discount rates on rubber rooms
            ###
            try:
                data = self.socket.recv(8192) # 8k
                # Don't move this check down below with the if data:
                #  It breaks down there (always returns no data)
                if not data:
                    self.console("Socket closed")
                    self.shutdown()
            except socket.error, e:
                if e.errno == 11:
                    pass
                else:
                    self.console("Error reading from socket: " + str(e))
            if data:
                # Is it a telnet command?
                if data[0] == '\xFF': # Doesn't start with IAC
                    telnet_cmd = ""
                    for i in range(len(data)):
                        keyval = int(data[i].encode("hex"),16)
                        if keyval in telnet:
                            telnet_cmd += str(telnet[keyval]) + " "
                        else:
                            telnet_cmd += "[" + str(keyval) + "] "
                    self.console("Telnet command received: " + telnet_cmd)
                else:
                    # Lets get rid of the newline characters on the end
                    data = data.rstrip("\r\n")
                    self.enqueue('recv', data)
                    #self.console("DEBUG: Recv: " + str(data))
                    self.game.receive(self, data)
            # Check the control queue for commands
            while self.hasqueued('control'):
                cmd = self.get_nowait('control')
                if cmd == 'shutdown':
                    # Shut down the network thread
                    self.socket.shutdown(socket.SHUT_RDWR)
                    self.socket.close()
                    self.console("Client stopped")
                    self.game.disconnect(self)
                    self.status = "SHUTDOWN"
                    return
                else:
                    # Whaaat? I don't know how to do that
                    self.console("WARNING: Unknown control issued to Client: " + str(cmd))
            # Check the send queue for output
            while self.hasqueued('send'):
                self._send(self.get_nowait('send'))
