#!/usr/bin/env python2.5
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

Support for Abstract Syntax Trees (ASTs).  An AST.Instance is a node
in an abstract syntax tree; it represents a syntactic object,
something you talk about when you're talking about a particular
expression in some language (like a "compilation unit", an
"expression", a "literal", etc.

Syntax translation is all about mapping from some sequence of
characters into a tree of AST.Instances (that is, and AST) and then
mapping back another sequence of characters.  (In some cases we might
map from one AST to another more-or-less equivalent one before we
serialize.)

This interface to ASTs walks a line between having AST.Insance be
simple python objects and ensuring they have a correct, general form.
In a previous version, I would do something like:

    mydoc = rif.Document(group=g, meta=m)

but now, using AST, we say instead:

    mydoc = AST.Instance('Document', group=g, meta=m)

In addition to Nodes, we have special additional types for Sequence
and DataValue.  We also have Multi, to support properties which have
multiple values (foreign to python, natural to RDF).

Related Modules:

   ns      -- provides namespaces for the types and attribute names
              used here
   graph   -- provides an RDF graph API to a set of ASTs

Issues:

   -- Okay to have strings as attribute values, or must they be other
      AST objects?

   -- even more: Okay to have all python types as attribute values?


****************

  * Instead of default_namespace, have a qname map.  (but only use it
    when there's no match, so it never intercepts?)

       -- have it be in a Factory

  * It's so hard to know if we should just use an xml dom or an rdf
    graph as the AST...  :-(

  * rename as absyn or absynt, and bring in Serializer/Writer and
    Parser/Reader.

"""

import sys
import inspect
import decimal

import debugtools 
from debugtools import debug

XS = "http://www.w3.org/2001/XMLSchema#"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDF_TYPE = RDF+"type"

# @@@@ Should use a factory for this...
default_namespace = None

def q(name):
    '''Add the default_namespace prefix if name is unqualified.

    At some point we'll probably want:

      (1) to do full qname/curie expansion
          (using the Guha rule -- if the prefix is declared, then
          it's a qname, otherwise it's a URI)
      (2) have some connection/portal/state/constructor object,
          so this isn't module-global.

    '''
    if default_namespace and name.find(":") == -1:
        return default_namespace + name
    return name


class Multi (object) :
    """

    >>> m = Multi()
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
    RuntimeError


    """
    
    __slots__ = ["values"]

    def __init__(self, values=None):
        self.values = []
        if values:
            for value in values:
                self.add(value)

    def deepcopy(self):
        ''' I know python has a deepcopy, but I can't figure out how
        to get it to work right in the presence of my getattr.  dumb. '''
        n = Multi()
        for v in self.values:
            n.values.append(v.deepcopy())
        assert n == self and n is not self
        return n

    def add(self, new):
        debug('ast2-multi-add', 'multi add', new)
        assert not isinstance(new, Multi)

        if not (new in self.values):
            self.values.append(new)
            return True
        else:
            return False

    def remove(self, value):
        self.values.remove(value)

    def replace_values(self, new_values):
        # please use this interface to replace the list of values,
        # instead of mucking with values directly.
        #
        # (this way, we could do special processing...)
        self.values = new_values

    def __repr__(self):
        return "Multi(values="+`self.values`+")"

    def __len__(self):
        return len(self.values)

    def __eq__(self, other):
        if not isinstance(other, Multi):
            return False

        others = other.values[:]
        for v1 in self.values:
            found = False
            for v2 in others:
                if v1 == v2:
                    found = True
                    others.remove(v2)
                    break
            if not found:
                return False
        if others:
            return False
        return True

    @property
    def the(self):
        if len(self.values) == 1:
            return self.values[0]
        else:
            raise RuntimeError('Expecting exactly one value, but there are '+
                               str(len(self.values)))

    @property
    def any(self):
        if len(self.values) > 0:
            return self.values[0]
        else:
            return None

    @property
    def first(self):
        """Using this implies you require that values
        be kept in a stable order.   Use .any unless you
        mean this."""
        if len(self.values) > 0:
            return self.values[0]
        else:
            return None

    def diff(self, other, prefix=""):
        if not isinstance(other, Multi):
            print "Value type mismatch", self.__class__, other.__class__
            return False

        #for v in self.values:
        #    for u in other.values:
        #        if 
            

class Instance (object) :
    """

    Note the property values are often IRIs.   Just use
    setattr/getattr instead of python's "obj.attr" notation.

    Should we maye primary_type look like a value of RDF_TYPE?  Eh, I
    dunno....

    """
    __slots__ = [ "primary_type", "dict" ]    

    def __init__(self, primary_type=None, **kwargs):
        object.__setattr__(self, "dict", {})
        object.__setattr__(self, "primary_type", q(primary_type))
        for (prop, value) in kwargs.items():
            setattr(self, prop, value)

    def has_primary_type(self, type):
        return self.primary_type == q(type)

    def has_type(self, type):
        return self.primary_type == q(type)

    @property
    def properties(self):
        return self.dict.keys()

    @property
    def child_instances(self):
        '''yield each instance directly under this one (via Multi/Sequence)'''

        for prop in self.properties:
            for value in getattr(self, prop):
                if isinstance(value, Sequence):
                    items = value.items
                else:
                    items = (value,)
                for item in items:
                    if isinstance(item, Instance):
                        yield item
                    elif isinstance(item, BaseDataValue):
                        pass
                    else:
                        raise RuntimeError('bad AST tree')
        return 

    def map_replace(self, func, *args, **kwargs):
        '''call the func on each descendant Instance, replacing it
        with whatever Instance func returns.  Works from the leaves
        up, operating on children before their parents.  If func
        returns None, that list-item or property value is simply
        removed'''

        debug('ast2-map(', 'begin')
        for prop in self.properties:
            multi = getattr(self, prop)
            self.list_map(multi.values, func, True, args, kwargs)
        new_self = func(self, *args, **kwargs)
        debug('ast2-map)')
        return new_self

    def list_map(self, values, func, collapse_dups, args, kwargs):
        '''call func on each item in this array of instances and
        return a new array of the resulting instances; used by map_in_place'''

        result = []
        for value in values:

            if isinstance(value, Sequence):
                self.list_map(value.items, func, False, args, kwargs)
                result.append(value)
            elif isinstance(value, Instance):
                new = value.map_replace(func, *args, **kwargs)
                # new = func(value, *args, **kwargs)
                if collapse_dups:
                    if new in result:
                        pass
                    else:
                        result.append(new)
                else:
                    result.append(new)
            elif isinstance(value, BaseDataValue):
                result.append(value)
            else:
                raise RuntimeError('bad AST tree:'+`value`)

        values[:] = result

    def __setattr__(self, prop, value):
        if prop[0] is "_":
            raise AttributeError
        assert not isinstance(value, Multi)
        assert isinstance(prop, basestring)   # unicode?   IRI.
        prop = q(prop)
        debug('ast2', 'adding',prop,"=",value)
        self.dict.setdefault(prop, Multi()).add(value)

    def __getattr__(self, prop):
        if prop[0] is "_":
            raise AttributeError

        prop = q(prop)
        debug('ast2-get', 'returning attr for', prop)
        return self.dict.setdefault(prop, Multi())
    
    def deepcopy(self):
        n = Instance(self.primary_type)
        for p,v in self.dict.items():
            n.dict[p] = v.deepcopy()
        assert n == self and n is not self
        return n
    
    def __getstate__(self):
        return (self.primary_type, self.dict)

    def __setstate__(self, state):
        (self.primary_type, self.dict) = state

    def __eq__(self, other):
        if not isinstance(other, Instance):
            return False
        k1 = sorted(self.dict.keys())
        k2 = sorted(other.dict.keys())
        if k1 != k2:
            return False
        for k in k1:
            if not self.dict[k] == other.dict[k]:
                return False
        return True

    def __str__(self):
        return "Instance("+self.primary_type+", ...)"

    def __repr__(self):
        s = "Instance("+self.primary_type+", "
        for (prop, value) in self.dict.items():
            s += `prop`+"="+`value`+", "
        s += ")"
        return s


    def to_python(self, map):
        """
        


        ...  wow, have I written code like this a lot, and I'm never
        very happy with it.  It might make sense to use some sort of
        schema; I think we have one floating around somewhere.

        """
        (ns, local) = ns_split(self.primary_type)
        cls = getattr(map.class_map[ns], local)
        lvas = list_valued_attributes(cls)
        args = {}
        for (prop, value) in self.dict.items():
            (ns, local) = ns_split(prop)
            attr = map.prop_map[ns]+local
            if attr in lvas:
                if (len(value.values) == 1 and 
                    isinstance(value.the, Sequence)):
                    # A list arg is expected, but we only have one
                    # value, AND it's a sequence of values, so... pass
                    # those sequence items in (instead of the multi.values)
                    #
                    # This is somewhat suspect, but it's usually what is
                    # wanted....
                    args[attr] = [v.to_python(map) for v in value.the.items]
                else:
                    args[attr] = [v.to_python(map) for v in value.values]
            else:
                if value.the:
                    args[attr] = value.the.to_python(map)
        return cls(**args)

    def diff(self, other, prefix=""):
        """print/return the differences with another AST
        
        still rough
        """
        if not isinstance(other, Instance):
            print "Value type mismatch", self.__class__, other.__class__
            return False

        if self.primary_type != other.primary_type:
            print "Primary Type Difference", self.primary_type, "<>", other.primary_type
            return False

        print prefix, self.primary_type
        for p in self.properties:
            if p not in other.dict:
                print "Only self has ", p
        for p in other.properties:
            if p not in self.dict:
                print "Only other has ", p
        all_passed = True                
        for p in sorted(self.properties):
            print prefix+"  ", p
            vo = getattr(self, p)
            vn = getattr(other, p)
            result = vo.diff(vn, prefix+"  ")
            if result is False:
                all_passed = False
        return all_passed

class Sequence (object) :

    __slots__ = [ "items" ]

    def __init__(self, items=None):
        self.items = items or []

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

class BaseDataValue (object):
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



class test_class_1 (object) :
    def __init__(self, a, b, c, d=[], e=None, f=[], g=[], h=None):
        pass

class test_class_2 (object) :
    def __init__(self, e=None, f=[], g=[], h=None, i=[]):
        pass

class test_class_3 (object) :
    def __init__(self):
        pass


def list_valued_attributes(cls):
    """
    Which attributes of this class can/should be initialized with a
    list?  

    We determine this by looking at the classes' __init__ function,
    assuming that any which are initialized with a list are list
    valued attributes.  Obviously, this relies on several conventions!

    >>> list_valued_attributes(test_class_1)
    ['d', 'f', 'g']
    >>> list_valued_attributes(test_class_2)
    ['f', 'g', 'i']
    >>> list_valued_attributes(test_class_3)
    []

    """

    result = []
    (args, varargs, varkw, defaults) = inspect.getargspec(cls.__init__)
    if defaults is None:
        return []
    offset = len(args) - len(defaults)
    #print >>sys.stderr, "offset, l1, l2", offset,len(args), len(defaults)
    for i in range(offset, len(args)):
        arg = args[i]
        default = defaults[i-offset]
        #print >>sys.stderr, "arg %d: %s  default %s" % (i, arg, `default`)
        if isinstance(default, list):
            result.append(arg)
    return result
        

# OBSOLETE --- use   inst.map_replace()
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


def string(s):
    return StringValue(s, XS+"string")

if __name__ == "__main__":
    import doctest, sys
    doctest.testmod(sys.modules[__name__])
