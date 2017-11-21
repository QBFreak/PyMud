# PyMud

PyMud is a Multi-threaded MUD server written in Python. The goal is to have a mud server capable of supporting a procedurally generated, infinite universe for the game SolarWinds. This will include 2D (planet surface) and 3D (space) environments. Present state of the engine is non-functional, in the very beginning stages. Multiple attempts have been made at SolarWinds with different engines and all have run into inherent limitations that ultimately required the creation of PyMud. A single-threaded version was in it's infancy when the need for multiple threads was recognized and this iteration of the project started.

# The pieces

## pymud.py

This is the main program, the server. It handles instantiating the objects, starting and stopping the threads, and monitoring the threads for console output,.

## PyMud/client.py

client.py provides the Client object, which handles incoming client connections. New connections accepted by pymud.py are sent to new instances of Client.

## PyMud/db.py

db.py provides the Database object, which is the database handler. It abstracts the sqlite database into game-specific requests using thread-safe methods that the other objects can call to retrieve or store data.

## PyMud/game.py

game.py provides the Game object, which is the main game engine. At the moment it simply accepts notifications for new Client connections.

## PyMud/multiqueue.py

This contains the MultiQueue class which is a superclass of all of the other objects (Client, Database, Game, Network). It provides the Queues that are used for communication between threads.

## PyMud/net.py

net.py provides the Network object, which handles listening for incoming TCP connections and passing them to new Client instances.
