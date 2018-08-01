#!/usr/bin/python
"""
    PyMud/object.py - PyMud objects

    TODO:
        We aren't doing nearly enough to verify the data passed into the __init__()s
"""
import random

class Object:
    "A standard object"
    def __init__(self, id, name, color=None, desc=None):
        if type(id) != type(int()) or id < 0:
            raise(ValueError("id Must be a positive integer"))
        self.id = id
        if type(name) != type(str()) or name == "":
            raise(ValueError("name Must be a non-empty string"))
        self.name = name
        if color == None:
            self.color = 0
        else:
            if type(color) != type(int()) or color < 0 or color > 15:
                raise(ValueError("color Must be an integer in the range 0-15 [{0}, {1}]".format(type(color), color)))
            self.color = color
        if desc == None:
            self.desc = ""
        else:
            if type(desc) != type(str()):
                raise(ValueError("desc Must be a string"))
            self.desc = desc
        self.type = "Object"

    def __repr__(self):
        # Return the dbref
        return "#" + str(self.id)

    def __str__(self):
        # Return the name + dbref
        return self.name + "(#" + str(self.id) + ")"

class Room(Object):
    "A room, inherits from the standard object"
    def __init__(self, id, name, color=None, desc=None):
        # Let the Object init perform sanity checks on the values,
        #  as well as handling most of them
        Object.__init__(self, id, name, color=color, desc=desc)
        # Room get a random color if none is specified
        if color == None:
            self.color = random.randint(0, 15)
        else:
            self.color = color
        self.type = "Room"

class Player(Object):
    "A player, inherits from the standard object"
    def __init__(self, id, name, color=None, desc=None, channel=None, channels=None):
        # Let the Object init perform sanity checks on the values,
        #  as well as handling most of them
        Object.__init__(self, id, name, color=color, desc=desc)
        # Player get a random color if none is specified
        if color == None:
            self.color = random.randint(0, 15)
        else:
            self.color = color
        if channel == None:
            if channels != None and type(channels) == type([]):
                channel = channels[0]
            else:
                channel = "public"
        if channels == None:
            if channel != None:
                channels = [channel]
            else:
                channels = ["public"]
        if type(channel) != type(str()) or len(channel) < 1:
            raise ValueError("channel Must be a non-empty string")
        if type(channels) != type([]) or len(channels) < 1:
            raise ValueError("channels must be a non-empty list of strings")
        self.type = "Player"
