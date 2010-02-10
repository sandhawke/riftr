#!/usr/bin/env python2.5
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

Prolog-backed version of the nodecentric API.

This version stores it all in the prolog engine, but it might make
sense to keep a copy in python of what we've already inferred, for
performance.

"""

import debugtools 
from debugtools import debug
import nodecentric as nc
from nodecentric import XS, RDF
from swi_prolog import Prolog
import decimal

class NodeFactory(nc.NodeFactory):

    def __init__(self, *args, **kwargs):
        nc.NodeFactory.__init__(self, *args, **kwargs)
        self.id_count = 0
        self.engine = Prolog()
    
    def rawInstance(self):
        return Instance(self)

    def rawSequence(self):
        return Sequence()

    def rawMulti(self):
        return Multi()

    def DataValue(self, value, datatype=None):
        return obtainDataValue(value, datatype)

class Multi(nc.Multi) :

    __slots__ = ["subj", "prop"]

    @property
    def values(self):
        for r in self.factory.engine.query("rdf({self.subj},{self.prop},X)",
                                           locals()):
            yield r["X"]
    
    def add(self, new, graph_if_adding=None):
        """if this value is in the merged graph, just return false;
        If it's not, then add it to the graph_if_adding graph.
        """
        if not (new in self.values):
            self.factory.engine.assertz("rdf_fact({self.subj},{self.prop},{new})", locals())
            return True
        else:
            return False

class Instance(nc.Instance):

    __slots__ = [ "_ident" ]    

    def __init__(self, factory):
        # the factory is also an attribute, but it's not 
        # set until later, so we're passed it here.
        ident = "inst_"+str(factory.id_count)
        factory.id_count += 1
        object.__setattr__(self, "_ident", ident)

    # Uhhhh, why isn't this happening automatically?
    @property
    def _primary_type(self):
        try:
            return getattr(self, nc.RDF_TYPE).first.lexrep
        except IndexError:
            return None


    @property
    def properties(self):
        done = set()
        for r in self._factory.engine.query("rdf({self._ident},X,_)",
                                           locals()):
            prop = r["X"]
            if prop in done:
                continue
            done.add(prop)
            yield prop

    def __setattr__(self, prop, value):
        if prop[0] is "_":
            raise AttributeError, "Instance.__setattr__ called on internal attribute %s.  Ooops." % `prop`

        assert not isinstance(value, Multi)
        assert isinstance(prop, basestring)   # unicode?   IRI.
        prop = self._q(prop)
        debug('ast2', 'adding',prop,"=",value)
        self._factory.engine.assertz("rdf({self._ident}, {prop}, {value})",
                                    locals())

    def __getattr__(self, prop):
        if prop[0] is "_":
            raise AttributeError, "Instance.__getattr__ called on internal attribute %s.  Ooops." % `prop`

        prop = self._q(prop)
        debug('ast2-get', 'returning attr for', prop)
        m = self._factory.Multi()
        m.subj = self._ident
        m.prop = prop
        return m
    


class Sequence(nc.Sequence):

    __slots__ = [ "items" ]

    def __init__(self):
        nc.Sequence.__init__(self)
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

    def __eq__(self, other):
        if not isinstance(other, Sequence):
            return False
        if len(self.items) != len(other.items) :
            return False
        for i in range(0, len(self.items)):
            if not self.items[i] == other.items[i]:
                return False
        return True
                
datatypes = {}

class BaseDataValue(nc.DataValue):
    """
    This is what gets instiated.   Don't count on what you get Being a "DataValue".

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
    is about right.  My big question is whether to use something like
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
    
    __slots__ = ['value', 'datatype']   # keep dt around...???

    @property
    def serialize_as_type(self):
        return "PlainLiteral"

    def __init__(self, lexrep, datatype=None):
        self.lexrep = lexrep
        if datatype is None:
            datatype = RDF+"PlainLiteral"
        else:
            if datatype != RDF+"PlainLiteral":
                raise ValueError
        self.datatype = datatype

    def to_python(self, map=None):
        return self.lexrep

datatypes[RDF+"string"] = [PlainLiteral]

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
    # f.nsmap.bind("", "http://www.example.com#")
    i = f.Instance("rif_Document")
    j = f.Instance("rif_Test") #, rif_a=i)
    print `j`

        
if __name__ == "__main__":
    import doctest, sys
    doctest.testmod(sys.modules[__name__])

    test1()
