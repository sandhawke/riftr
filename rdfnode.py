#!/usr/bin/env python2.5
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

Another nodecentric implementation, like datanode, but this one is
backed by an rdflib Graph.

This turns out to be messier than I had hoped.  List handling ugh!

"""

import decimal

from rdflib.Graph import ConjunctiveGraph
from rdflib import URIRef, BNode, Literal

import debugtools 
from debugtools import debug
import nodecentric as nc
from nodecentric import XS, RDF

RDF_FIRST = RDF+"first"
RDF_REST = RDF+"rest"
RDF_NIL = RDF+"nil"

class NodeFactory(nc.NodeFactory):

    def __init__(self, graph=None):
        nc.NodeFactory.__init__(self)
        self.graph = graph or ConjunctiveGraph()

    def rawInstance(self):
        return Instance()

    def rawSequence(self):
        return Sequence()

    def rawMulti(self, **kwargs):
        return Multi(**kwargs)

    def DataValue(self, value, datatype=None):
        return DataValue(value, datatype)

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
            if v == RDF_NIL:
                s = Sequence(attached=True, empty=True)
                s.factory = self.factory
                yield s
            elif (v, RDF_FIRST, None) in self.factory.graph:
                s = Sequence(attached=True, empty=False,_node=v)
                s.factory = self.factory
                yield s
            else:
                yield v

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

        triple = (self.subj, self.prop, new) 

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
    __slots__ = [ "_subj" ]    

    def __init__(self):
        object.__setattr__(self, "_subj", BNode())

    @property
    def properties(self):
        return self._factory.graph.predicates(self._subj)

    def _getpv(self, prop):
        prop = self._q(prop)
        return self._factory.Multi(subj=self._subj, prop=URIRef(prop))
    




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
            self.factory.graph.add(    (self._last, RDF_FIRST, new) )
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
        self.factory.graph.add(    (current, RDF_FIRST, self._items[-1]) )
        self.factory.graph.add(    (current, RDF_REST, RDF_NIL) )
        next = current
        for item in reversed(self._items[:-1]):
            current = BNode()
            self.factory.graph.add(    (current, RDF_FIRST, item) )
            self.factory.graph.add(    (current, RDF_REST, next) )
            next = current
        self._node = current
        return current
        
    @property
    def items(self):
        if not self.attached:
            for item in self._items:
                yield item
        else:
            current = self._node
            while current != RDF_NIL:
                x = only(self.factory.graph.objects(current, RDF_FIRST))
                yield x
                self._last = current
                current = only(self.factory.graph.objects(current, RDF_REST))

def only(items):
    value = None
    for i in items:
        if value is None:
            value = i
        else:
            raise RuntimeException
    if value is None:
        raise RuntimeException
    return value

datatypes = {}

class BaseDataValue(nc.DataValue):
    """
    This is what gets instantiated.  Don't count on what you get Being
    a "DataValue".   (why not...?)

    """

    @property
    def serialize_as_type(self):
        return "BaseDataValue"

    def __repr__(self):
        return "DataValue("+`self.lexrep`+", "+`self.datatype`+")"

    def to_python(self, map=None):
        raise RuntimeError("Don't know how to convert to python datatype: "+`self.datatype`)

    def __eq__(self, other):
        return (isinstance(other, BaseDataValue) and
                self.datatype == other.datatype and
                self.lexrep == other.lexrep)
                   
    def __cmp__(self, other):
        c1 = cmp(self.datatype, other.datatype)
        if c1 == 0:
            return cmp(self.lexrep, other.lexrep)
        else:
            return c1

    def deepcopy(self):
        n = obtainDataValue(self.lexrep, self.datatype)
        assert n == self and n is not self
        return n

    def value_fits(self, other_type):
        if self.datatype == other_type:
            return True
        # @@@@ try promotion and demotion-with-testing
        return False

def obtainDataValue(lexrep, datatype):
    """

    This is a fairly sketchy implementation, but I think the interface
    is about right. My big question is whether to use something like
    __new__ to give a subtype...

    >>> d = DataValue("003", XS+"int")
    >>> d
    DataValue('3', 'http://www.w3.org/2001/XMLSchema#int')
    >>> d.to_python() is 3
    True
    >>> DataValue("hello", XS+"string").to_python() is "hello"
    True

    """
    dts = datatypes.get(datatype, [])
    for dt in dts+[UnimplementedDataValue]:
        try:
            d = dt(lexrep, datatype)
            return d
        except ValueError:
            pass
    raise RuntimeError('not reached')


class DataValue (BaseDataValue) :
    """
    I don't know yet if this is nice, or a stupid hack....
    """

    __slots__ = []

    def __new__(self, lexrep, datatype):
        return obtainDataValue(lexrep, datatype)

class DecimalValue (BaseDataValue) :
    """ 
    Uses a reasonable internal representation, but remembers the name
    you used for the type -- maybe it doesn't have to.

    >>> d = DataValue("043423423423324234.234234234230", XS+"decimal")
    >>> d
    DataValue('43423423423324234.234234234230', 'http://www.w3.org/2001/XMLSchema#decimal')
    >>> type(d.to_python())
    <class 'decimal.Decimal'>

    >>> d = DataValue("043423423423324234", XS+"decimal")
    >>> d
    DataValue('43423423423324234', 'http://www.w3.org/2001/XMLSchema#decimal')
    >>> type(d.to_python())
    <type 'long'>

    >>> d = DataValue("10", XS+"decimal")
    >>> d
    DataValue('10', 'http://www.w3.org/2001/XMLSchema#decimal')
    >>> type(d.to_python())
    <type 'int'>

    >>> d = DataValue("10", XS+"byte")
    >>> d
    DataValue('10', 'http://www.w3.org/2001/XMLSchema#byte')
    >>> type(d.to_python())
    <type 'int'>


    """

    __slots__ = ['value', 'datatype']   # keep dt around...???

    def __init__(self, lexrep, datatype):
        self.value = decimal.Decimal(lexrep, decimal.ExtendedContext)
        self.datatype = datatype

    def to_python(self, map=None):
        return self.value

    @property
    def lexrep(self):
        return str(self.value)

class IntValue (BaseDataValue) :
    """

    Several tests/demos in Decimal

    DOES NOT ENFORCE the sub-type -- just tries to store it.   
    >>> d = DataValue("-4", XS+"nonNegativeInteger")
    >>> d
    DataValue('-4', 'http://www.w3.org/2001/XMLSchema#nonNegativeInteger')
    >>> type(d.to_python())
    <type 'int'>

    """

    @property
    def serialize_as_type(self):
        return "IntValue"

    __slots__ = ['value', 'datatype']   # keep dt around...???

    def __init__(self, lexrep, datatype):
        self.value = int(lexrep)  
        self.datatype = datatype

    def to_python(self, map=None):
        return self.value

    @property
    def lexrep(self):
        return str(self.value)

datatypes[XS+"decimal"] = [IntValue, DecimalValue]
datatypes[XS+"integer"] = [IntValue]
datatypes[XS+"long"] = [IntValue]
datatypes[XS+"nonPositiveInteger"] = [IntValue]
datatypes[XS+"nonNegativeInteger"] = [IntValue]
datatypes[XS+"int"] = [IntValue]
datatypes[XS+"short"] = [IntValue]
datatypes[XS+"byte"] = [IntValue]



class StringValue (BaseDataValue) :
    """

    >>> d = DataValue("hello", XS+"string")
    >>> d
    DataValue('hello', 'http://www.w3.org/2001/XMLSchema#string')
    >>> d.to_python() is "hello"
    True


    """

    __slots__ = ['value', 'datatype']   # keep dt around, for subtypes

    @property
    def serialize_as_type(self):
        return "StringValue"

    def __init__(self, lexrep, datatype=None):
        self.lexrep = lexrep
        if datatype is None:
            datatype = XS+"string"
        else:
            if datatype != XS+"string":
                raise ValueError
        self.datatype = datatype

    def to_python(self, map=None):
        return self.lexrep

datatypes[XS+"string"] = [StringValue]

class PlainLiteral (BaseDataValue) :
    
    __slots__ = ['value']

    @property
    def serialize_as_type(self):
        return "PlainLiteral"

    def __init__(self, lexrep, datatype=None):
        self.lexrep = lexrep
        if datatype is not None and datatype != RDF+"PlainLiteral":
                raise ValueError

    def to_python(self, map=None):
        return self.lexrep

    @property
    def datatype(self):
        return RDF+"PlainLiteral"

datatypes[RDF+"PlainLiteral"] = [PlainLiteral]
# datatypes[RDF+"string"] = [PlainLiteral]

class UnimplementedDataValue (BaseDataValue) :

    __slots__ = ['lexrep', 'datatype'] 

    def __init__(self, lexrep, datatype):
        self.lexrep = lexrep
        self.datatype = datatype





    

class Python_Map (object):
    """
    I've written various versions of this, eg in webdata.py called
    "reconstruct"

    """

    def __init__(self, class_map, prop_map):
        """
        class_map is a mapping from namespaces to modules
        prop_map is a mapping from namespaces to some text
             you want prepended to the names of attributes
             (maybe "" if you're not afraid of collisions)
        sv_props is a collection of single-valued properties,
             it those that are guaranteed to only have one
             value, and so the python attribute can be just
             given that value, instead of given a list of values.

        getattr(class_map[ns], local) is the class to use

        prop_map[ns]+local is the name of the class attribute

        and maybe we use introspection to see if we should pass everything
           to the constructor, or nothing and then use setattr?

        and what about multi-values?   we can pass a list for Multi,
        we can pass a list for Sequence, but ... both???   What if it's a
        Multi of Sequences?   (that can happen.)  What do we pass THEN?
        Maybe the class tells us:
            ast_multi_as_list = [ "p1", "p2", "p3" ]
        """
        self.class_map = class_map
        self.prop_map = prop_map
        
    def from_python(self, object):
        raise RuntimeError()



def string(s):
    return StringValue(s, XS+"string")

def test1():
    
    f = NodeFactory()
    i = f.Instance("rif_Document", rif_a=5)
    j = f.Instance("rif_Test", rif_a=i)
    print `j`

        
if __name__ == "__main__":
    import doctest
    doctest.testmod()

    # test1()
    
