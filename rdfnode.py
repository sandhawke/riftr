#!/usr/bin/env python2.5
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

Another nodecentric implementation, like datanode, but this one is
backed by an rdflib Graph.

This turns out to be messier than I had hoped.  List handling ugh!


when you a add something, use its ._node

"""

import decimal

from rdflib.Graph import ConjunctiveGraph
from rdflib import URIRef, BNode, Literal

import debugtools 
from debugtools import debug
import nodecentric as nc
from nodecentric import XS, RDF

RDF_FIRST = URIRef(RDF+"first")
RDF_REST = URIRef(RDF+"rest")
RDF_NIL = URIRef(RDF+"nil")

class NodeFactory(nc.NodeFactory):

    def __init__(self, graph=None):
        nc.NodeFactory.__init__(self)
        self.graph = graph or ConjunctiveGraph()

    def rawInstance(self, **kwargs):
        return Instance(**kwargs)

    def rawSequence(self):
        return Sequence()

    def rawMulti(self, **kwargs):
        return Multi(**kwargs)

    def DataValue(self, value, datatype=None):
        return DataValue(value, datatype)

    def wrap(self, x):
        # we're skipping lots of the nodecentric/base constructors here.

        if unicode(x) == RDF_NIL:
            s = Sequence(attached=True, empty=True)
            s.factory = self
            return s
        if isinstance(x, URIRef):
            s = Instance(id=unicode(x))
            object.__setattr__(s, "_factory", self)
            return s
        if isinstance(x, Literal):
            return self.DataValue(str(x), str(x.datatype))
        if isinstance(x, BNode):
            if (x, RDF_FIRST, None) in self.graph:
                s = Sequence(attached=True, empty=False,_node=x)
                s.factory = self
                return s
            else:
                return self.Instance()

class Multi(nc.Multi) :
    """
    
    For us, here, a Multi is a (S,P) pair.  You really should tell us
    what the (S and P) are before adding values, but maybe we'll do
    placeholders if necessary?

    >>> nf = NodeFactory()
    >>> m = nf.Multi()

    x>>> m.add(1)
    xTrue
    x>>> m.add(1)
    xFalse
    x>>> m
    xMulti(values=[1])
    x>>> m.the
    x1
    x>>> m.add(2)
    xTrue
    >x>> m
    xMulti(values=[1, 2])
    x>>> m.any
    x1
    x>>> m.the
    xTraceback (most recent call last):
    x...
    xRuntimeError: Too many values for "the"


    """
    
    __slots__ = ["subj", "prop"]

    def __init__(self, subj=None, prop=None):
        self.subj = subj
        self.prop = prop

    @property
    def values(self):
        if self.subj is None:
            return
        for v in self.factory.graph.objects(self.subj, self.prop):
            yield self.factory.wrap(v)

    def clear(self):
        self.factory.graph.remove(  (self.subj, self.prop, None)  )

    def add(self, new, graph_if_adding=None):
        """if this value is in the merged graph, just return false;
        If it's not, then add it to the graph_if_adding graph.
        """
        debug('ast2-multi-add', 'multi add', new)
        assert not isinstance(new, Multi)
        assert self.subj is not None

        if isinstance(new, Sequence):
            new = new.attach(self.factory.graph)

        triple = (self.subj, self.prop, new._node) 

        if triple not in self.factory.graph:
            self.factory.graph.add(triple)
            return True
        else:
            return False

class Instance(nc.Instance):
    """

    How do we get the ID for non-BNodes???   Can we get it later
    and do a full replace?    set _id ??!?!

    """
    __slots__ = [ "_node" ]    

    def __init__(self, id=None, **kwargs_ignored_here):
        if id is None:
            object.__setattr__(self, "_node", BNode())
        else:
            object.__setattr__(self, "_node", URIRef(id))

    @property
    def properties(self):
        for x in self._factory.graph.predicates(self._node):
            yield str(x)

    def _getpv(self, prop):
        prop = self._q(prop)
        return self._factory.Multi(subj=self._node, prop=URIRef(prop))
    




class Sequence(nc.Sequence):
    """
    
    Multis and Lists do NOT go together well.  If you have this:
        <a> <b> ( 1 2 )
    and you want to add this graph:
        <a> <b> ( 1 2 3 )
    so that you end up with:
        <a> <b> ( 1 2 )
        <a> <b> ( 1 2 3 )
    you're going to have a hard time.  You can't just start with an
    empty list, then append 1, 2, and 3, because at the point where
    you have just 1 and 2 in it, you have:
        <a> <b> ( 1 2 )
    and then when you add 3, ... how do you know to make two lists
    again?  Maybe bnode identifies can help, but not in the case where
    the existing list is empty (rdf:nil).

    Solutions:
       1. never combine multis and lists (but the old RIF syntax does,
          for slots [ironically])
       2. never modify a list in place -- assert or retract the triple.
          (this seems like a big hassle, and breaks nodecentric's API)

    I guess we'll encourage people to create and modify their
    instances first, and use nodeIDs once they have contents.  Forbid
    updating the empty list in place.

    >>> nf = NodeFactory()
    >>> nf.nsmap.bind('', "http://example.com/")
    >>> s = nf.Sequence()
    >>> s.append(nf.StringValue("hello"))
    >>> s.append(nf.StringValue("world"))
    >>> [x.lexrep for x in s.items]
    ['hello', 'world']

    >>> p = nf.Instance()
    >>> p.motto = s
    >>> [x.lexrep for x in p.motto.the.items]
    ['hello', 'world']

    >>> p.motto.the.append(nf.StringValue("you're"))
    >>> p.motto.the.append(nf.StringValue("cool"))
    >>> [x.lexrep for x in p.motto.the.items]
    ['hello', 'world', "you're", 'cool']




    """

    def __init__(self, attached=False, empty=True, _node=None):
        self._items = []    # before attached
        self.attached = attached
        self.empty = empty
        self._node = _node
    
    def append(self, new):
        assert isinstance(new, nc.Value)
        if self.attached:
            if self.empty:
                raise RuntimeError, "Sorry, but you can't append to an empty list, once its be set as a value, due to limitation in the RDF model.  Crazy, I know.   You'll have to retract it and add it again yourself, if that's what you want."

            # set self._last; perhaps we should cache it.
            [x for x in self.items]

            self.factory.graph.remove( (self._last, RDF_REST, RDF_NIL) )
            old_last = self._last
            self._last = BNode()
            self.factory.graph.add(    (old_last, RDF_REST, self._last) )
            self.factory.graph.add(    (self._last, RDF_FIRST, new._node) )
            self.factory.graph.add(    (self._last, RDF_REST, RDF_NIL) )
        else:
            self._items.append(new)

    def attach(self, graph):
        #
        #  kind of funny, looking back that I wrote this using the rdflib
        #  api instead of nodecentric....
        #
        if self.attached:
            raise RuntimeError
        self.attached = True
        if len(self._items) == 0:
            self.empty = True
            return RDF_NIL
        self._last = BNode()
        current = self._last
        self.factory.graph.add(    (current, RDF_FIRST, self._items[-1]._node) )
        self.factory.graph.add(    (current, RDF_REST, RDF_NIL) )
        next = current
        for item in reversed(self._items[:-1]):
            current = BNode()
            self.factory.graph.add(    (current, RDF_FIRST, item._node) )
            self.factory.graph.add(    (current, RDF_REST, next) )
            next = current
        self._node = current
        return self
        
    @property
    def items(self):
        if not self.attached:
            for item in self._items:
                yield item
        else:
            current = self._node
            while current != RDF_NIL:
                x = only(self.factory.graph.objects(current, RDF_FIRST))
                yield self.factory.wrap(x)
                self._last = current
                current = only(self.factory.graph.objects(current, RDF_REST))

def only(items):
    value = None
    for i in items:
        if value is None:
            value = i
        else:
            raise RuntimeError
    if value is None:
        raise RuntimeError
    return value

datatypes = {}

class DataValue(nc.DataValue):
    """

    I tried to do it with multiple inheritance, but we have slightly
    different semantics for "datatype", in that I use PlainLiterals
    (for some crazy reason).

    """
    
    def __init__(self, lexrep, datatype):
        self.lexrep = lexrep
        self.datatype = datatype
        if datatype == RDF+"PlainLiteral":
            (text, lang) = lexrep.rsplit("@", 1)
            if lang == "":
                self._node = Literal(text)
            else:
                self._node = Literal(text, language=lang)
        else:
            self._node = Literal(lexrep, datatype=datatype)

    @property
    def serialize_as_type(self):
        return "BaseDataValue"

    def __repr__(self):
        return "DataValue("+`self.lexrep`+", "+`self.datatype`+")"

def test1():
    
    f = NodeFactory()
    i = f.Instance("rif_Document", rif_a=5)
    j = f.Instance("rif_Test", rif_a=i)
    #  print `j`

        
if __name__ == "__main__":
    import doctest
    doctest.testmod()

    #test1()
    
