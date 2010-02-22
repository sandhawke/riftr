#!/usr/bin/env python2.5
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

Used to be called AST2, this is a simple dict/list backing for nodecentric.

The data values get a little complicated, though.

"""

import decimal

import debugtools 
from debugtools import debug
import nodecentric as nc
from nodecentric import XS, RDF

class NodeFactory(nc.NodeFactory):
    
    def rawInstance(self):
        return Instance()

    def rawSequence(self):
        return Sequence()

    def rawMulti(self):
        return Multi()

    def DataValue(self, value, datatype=None):
        return obtainDataValue(value, datatype)

class ValueHolder (object) :
    """For quads/provenance"""
    __slots__ = ["value", "graph"]
    def __init__(self, value, graph=None):
        self.value=value
        self.graph=graph

class Multi(nc.Multi) :
    """

    >>> m = NodeFactory().Multi()
    >>> m.add(1)
    True
    >>> m.add(1)
    False
    >>> m
    Multi(values=[1])
    >>> m.the
    1
    >>> m.add(2)
    True
    >>> m
    Multi(values=[1, 2])
    >>> m.any
    1
    >>> m.the
    Traceback (most recent call last):
    ...
    RuntimeError: Too many values for "the"


    """
    
    __slots__ = ["value_holders", "nsmap"]

    def __init__(self):
        self.value_holders = []

    @property
    def values(self):
        for vh in self.value_holders:
            yield vh.value

    def clear(self):
        self.value_holders = []

    def add(self, new, graph_if_adding=None):
        """if this value is in the merged graph, just return false;
        If it's not, then add it to the graph_if_adding graph.
        """
        debug('ast2-multi-add', 'multi add', new)
        assert not isinstance(new, Multi)

        if not (new in self.values):
            self.value_holders.append(ValueHolder(new, graph_if_adding))
            return True
        else:
            return False

    def __len__(self):
        return len(self.value_holders)

class Instance(nc.Instance):
    """

    Note the property values are often IRIs.   Just use
    setattr/getattr instead of python's "obj.attr" notation.

    Or use the ulqname form, qnames using underscores.

    """
    __slots__ = [ "_dict" ]    

    def __init__(self):
        object.__setattr__(self, "_dict", {})

    @property
    def properties(self):
        return self._dict.keys()

    def _getpv(self, prop):
        if prop[0] is "_":
            raise RuntimeError, "Looping into __getattr__ for "+prop
        prop = self._q(prop)
        return self._dict.setdefault(prop, self._factory.Multi())

    def __getstate__(self):
        return (self._factory, self._dict)

    def __setstate__(self, state):
        object.__setattr__(self, "_factory", state[0])
        object.__setattr__(self, "_dict", state[2])



class Sequence(nc.Sequence):

    __slots__ = [ "items" ]

    def __init__(self):
        self.items = []

    def deepcopy(self):
        n = Sequence()
        for v in self.items:
            n.items.append(v.deepcopy())
        assert n == self and n is not self
        return n

    def append(self, new):
        self.items.append(new)

    def extend(self, new):
        if isinstance(new, Sequence):
            new = new.items
        self.items.extend(new)

    def __add__(self, other):
        return Sequence(items=(self.items + other.items))

                
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
    import doctest, sys
    doctest.testmod(sys.modules[__name__])

    test1()
