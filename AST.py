#!/usr/bin/env python2.5
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

Support for Abstract Syntax Trees (ASTs).  An AST.Node is a node in an
abstract syntax tree; it represents a syntactic object, something you
talk about when you're talking about a particular expression in some
language (like a "compilation unit", an "expression", a "literal",
etc.  

Syntax translation is all about mapping from some sequence of
characters into a tree of AST.Nodes (that is, and AST) and then
mapping back another sequence of characters.  (In some cases we might
map from one AST to another more-or-less equivalent one before we
serialize.)

This interface to ASTs is walks a line between having AST.Nodes be
simple python objects and ensuring they have a correct, general form.
In a previous version, I would do something like:

    mydoc = rif.Document(group=g, meta=m)

but now, using AST, we say instead:

    mydoc = AST.Node('Document', group=g, meta=m)


In addition to Nodes, we have special additional types for Sequence
and DataValue.   

Related Modules:

   ns      -- provides namespaces for the types and attribute names
              used here
   graph   -- provides an RDF graph API to a set of ASTs

Issues:

   -- Okay to have strings as attribute values, or must they be other
      AST objects?

   -- even more: Okay to have all python types as attribute values?


"""

import debugtools 
from debugtools import debug

class SyntacticObject (object):
    """
    Just to east type-checking, to group all three AST object types.
    """
    pass


class Node (SyntacticObject):
    """
    pretty free form!
    """
    
    def __init__(self, type, **kwargs):
        self._type = type
        self.__dict__.update(kwargs)
        # there's a self._graph, which Graph maintains for us.

    def __cmp__(self, other):
        return cmp(self.__dict__, other.__dict__)

    def __str__(self):
        return "Node("+self._type[1]+", ...)"


    # I dunno, do we want to tread _id specially?  I think we probably
    # do...  But we'd also kind of like it in the dictionary, so we
    # can serialize it like the other stuff?  But what if it has
    # multiple values?  Ugh!  RDF treats it differently, but doesn't
    # treat type differently.  shrug!
    #
    # is it a string, a special IRI type, or a DataValue?
    #
    #
    #      set_annotation, or something...?
    #
    def set_id(self, new_id):
        if hasattr(self._id):
            assert self._id == new_id
        else:
            self._id = new_id

    def __setattr__(self, attr, new_value):
        """On behalf of graph.Graph, make sure that after setting an
        attribute all the connected nodes are still in the Graph.

        Maybe we should be cleaner (with proper layering) and just
        make a _setattr_hooks list?   Or a subclass of AST.Node for
        when it's part of a graph?
        """
        try:
            self._graph.add_object(new_value)
        except AttributeError:
            pass
        # if Graph ever gets some kind of "remove", we might want to
        # hook on that here...?    All sorts of GC issues.

        self.__dict__[attr] = new_value
    
class Sequence (SyntacticObject):
    """
    When the value is a sequence of values, use this. 
    (when it just has multiple values, then use python list).

    WARNING: if you change the item list, Graph may lose certain
    properties.

    """
    
    def __init__(self, items=None):
        self.items = items or []
    
class DataValue (SyntacticObject):

    def __init__(self, lexrep, datatype):
        self.lexrep = lexrep
        self.datatype = datatype


    # python to/from conversions?

    # operators?

    # special handling to/from IRIs
        


def map(function, obj, *args, **kwargs):
    """
    Apply this function to every node in the tree, starting with the
    leaves and building up to the root.

    The function is called with the first parameter being an object in
    the tree (a node or data value), and the other args are as given.
    The function returns whatever the node should be replaced with.

    (Should we allow None to mean list items are removed from the
    list?  Right now it puts a None in the list.)

    """

    if obj is None:
        return None
    if isinstance(obj, str):    # do we allow these...?
        return obj
    
    debug('AST.map(', 'obj begins', obj)

    assert obj is not None

    if isinstance(obj, DataValue):
        obj = function(obj, *args, **kwargs)
    elif isinstance(obj, Sequence):
       for i in range(0, len(obj.items)):
           value = obj.items[i]
           assert value is not None
           value = map(function, value, *args, **kwargs)
           assert value is not None
           obj.items[i] = function(value, *args, **kwargs)
    elif isinstance(obj, list):
       for i in range(0, len(obj)):
           value = obj[i]
           assert value is not None
           value = map(function, value, *args, **kwargs)
           assert value is not None
           obj[i] = function(value, *args, **kwargs)
    elif isinstance(obj, Node):
        for (key, value) in obj.__dict__.items():
            if key.startswith("_"):
                continue
            debug('AST.map', 'property ', key)
            value = map(function, value, *args, **kwargs)
            obj.__dict__[key] = function(value, *args, **kwargs)
        obj = function(obj, *args, **kwargs)
    else:
        raise RuntimeError, 'Cant map a %s' % type(obj)


    debug('AST.map)', 'obj ends as ', obj)
    assert obj is not None

    return obj



