#!/usr/bin/env python2.5
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

Something like XML Schema for Python objects (and/or AST_Nodes)

   * read/write something like asn06
   * read/write something like xml schema
   * schema checking

"""

import debugtools 
from debugtools import debug


class Schema:

    def __init__(self):
        self.classes = []

class Property:

    # make this be on Classes,   add_property

    def __init__(self, name, range=None, optional=False, multi=False,
                 namespace="", python_name=None):
        self.name = name
        self.range = range
        self.optional = optional
        self.multi = multi
        self.namespace = namespace
        self.python_name = python_name or name
        
class Type:
    pass

class Class(Type, WebNamed):
    
    # make this be on Schema, add_class
    # (and we have get_class)

    def __init__(self, schema, name, inherits=None,
                 namespace="", python_name=None,
                 properties=None):
        self.schema = schema
        self.name = name
        self.inherits = inherits or []
        self.namespace = namespace
        self.python_name = python_name or name
        self.properties = properties or []

    @property
    def self_and_supers(self):
        yield self
        for s in self.inherits:
            yield s.self_and_supers()

    def check(self, node):
        if node.type in [cls.xml_name for cls in self.self_and_supers]:
            for p in self.properties:
                ... get the value/valueList, and check them...
        else:
            raise Error(self, node)

class Datatype(Type, WebNamed):

    def __init__(self, schema, name, inherits=None,
                 namespace="", python_name=None):
        self.schema = schema
        self.name = name
        self.namespace = namespace
        self.python_name = python_name or name

class Sequence(Type):

    def __init__(self, schema, item_type):
        self.schema = schema
        self.item_type = item_type


def check(node, range):
    """
    Check to see if this thing (this node) matches the given range (in
    whatever schema it's in).
    """


