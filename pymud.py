#!/usr/bin/python
"""
    pymud.py - PyMud main file
"""
import Queue, sys, time
import PyMud.db, PyMud.net, PyMud.game

print("== PyMud server ==")

db = PyMud.db.Database()
# Start the database thread so we can actually USE it
db.start()
# Wait for the database to start
while not db.started:
    time.sleep(0.1)
portNum = db.read_config("MUD_PORT")

net = PyMud.net.Network(db, port=portNum)
game = PyMud.game.Game(net, db)

net.start()
game.start()

threads = [db, net, game]

# Set is_alive flag for thread(s)
is_alive = False
for thread in threads:
    if thread.is_alive():
        is_alive = True
        break

while is_alive:
    try:
        # Don't let the loop eat the processor
        time.sleep(0.1)
        # Check for console messages from the the threads
        for thread in threads:
            while thread.hasqueued('console'):
                try:
                    sys.stdout.write(thread.get_nowait('console'))
                except Queue.empty:
                    pass

        # Check for console messages from the client threads
        for c in net.clients:
            while c.hasqueued('console'):
                try:
                    sys.stdout.write(c.get_nowait('console'))
                except Queue.Empty:
                    pass

    except KeyboardInterrupt:
        # print("You want to shut down")
        print("")
        for thread in threads:
            if thread.is_alive():
                thread.shutdown()
        # net.shutdown()
        # db.shutdown()
    # Set is_alive flag for thread(s)
    is_alive = False
    for thread in threads:
        if thread.is_alive():
            is_alive = True
            break
