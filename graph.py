#!/usr/bin/env python2.5
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

Provide a more-traditional RDF graph interface to ASTs, since they
*are* more or less equivalent to RDF Graphs.

Specifically:

An AST is a slightly restricted RDF graph.

        - one root node (but you can make collections of ASTs, which
          the "Graph" class does).

        - no loops or lattices (but some code will be okay if you
          construct them -- you might get some infinite loops, etc,
          though)

        - AST.Sequence is a terminated rdf:List without loops, and
          with the List and all "rest" sublists being b-nodes.

        - a Node has exactly one "type.  (Well, maybe it can be None,
          and maybe you can put more types in the dictionary.)


"""



class Graph (object):
    """
    Some sort of collection of Nodes, which are owned by the graph,
    connected only to other nodes which are owned by the graph.  Use
    this to get an graph-centric API to a set of ASTs, instead of the
    above/normal node-centric API.
    """

    def __init__(self):
        self._nodes = []
        self._node_from_id = {}

    def add_node(self, node):
        """Recursively add this node, and all nodes reachable from it,
        if they are not present.  Returns True if it wasn't present
        and was thus added; returns False if it was already there and
        nothing was done."""
        if hasattr(node, '_graph'):
            if node._graph == self:
                return False # already in this graph
            else:
                raise RuntimeError("Node is already in some other graph")
        node._graph = self
        self._nodes.append(node)

        id = getattr(node, "_id", None)
        if id:
            self._node_from_id[id] = node

        for (key, value) in node.__dict__.items():
            self.add_obj(value)

    def add_sequence(self, node):
        something_added = False
        for i in node.items:
            if self.add_obj(i):
                something_added = True
        return something_added

    def add_object(self, obj):
        if isinstance(obj, Sequence):
            return self.add_sequence(obj)
        elif isinstance(obj, Node):
            return self.add_node(obj)
        elif isinstance(obj, DataValue):
            return False
        else:
            raise RuntimeError('bad type')

