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
        
