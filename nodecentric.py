#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""
The abstract, common base classes for a node centric data API.  You
probably want to use datanode or rdflibnode or some such.

This API will be different things to different people:

   ** It's a nice representation of Abstract Syntax Trees (ASTs), such
      as produced by a parser.  Much of riftr involves conversion of a
      character stream into an AST, maybe some processing of the AST,
      then conversion back into a character stream.    

      There are three kinds of Nodes:

          Instance - ordinary syntactic elements.  An Instance is a
                      collection of (property,value) pairs; it's
                      basically a generic python object.  The properties
                      and the instance's type(s) are named internally
                      with URLs (IRIs), but the namespace map makes
                      that painless.

          DataValue - syntactic elements that correspond to
                      to values which can be represented with
                      XML datatypes, such as strings and numbers.  These
                      cannot have properties.

          Sequence  - an ordered collection of Nodes.

      Together, these three give a general object structuring, very
      much like we see in JSON.

      Two more classes:

          Factory   - use one of these this to create your Instance,
                      DataValue, and Sequence objects.  We need this
                      because there are different underlying implementations 
                      of the Nodes; to work together nodes need to be
                      from the same factory. 

          Multi     - each property of an Instance can have multiple values,
                      and we handle this via "Multi".   If you expect only
                      one value, use "the", like this:
                            my_person.mother.the

   ** It's an RDF triplestore (or quadstore) API, of the node-centric
      variety.  DataValues are RDF Literals, Sequences are rdf:Lists,
      and Instances are nodes which are neither of the above.  (We
      don't support rdf:Lists having other properties or being oddly
      formed; we treat them as syntactically primitive.)

      You can use nodecentric WITHOUT knowing about RDF, and the basic
      AST functionality is available without rdflib, etc.


"""

import sys
import decimal 

import qname
from debugtools import debug

XS = qname.common.xs
RDF = qname.common.rdf
RDF_TYPE = RDF+"type"

################################################################
#
#   Base Classes -- common stuff shared by various instantiations
#
#   (I know, this feels more like Java/C++ that Python, but in this
#   case I think it's pretty elegant.)
#

class Value (object) :
    pass

class SubclassShouldProvideThis(Exception):
    pass

class NodeFactory(object):
    
    # Should we promise to keep track of the nodes we create?  Or
    # do you need to remember the roots yourself?   It's up to the
    # concrete implementation you're using...

    def __init__(self, nsmap=None):
        if nsmap:
            self.nsmap = nsmap
        else:
            self.nsmap = qname.Map([qname.common])

    def rawInstance(self, **kwargs):
        raise SubclassShouldProvideThis
    def rawSequence(self):
        raise SubclassShouldProvideThis
    def rawMulti(self):
        raise SubclassShouldProvideThis

    def Instance(self, primary_type=None, **kwargs):
        result = self.rawInstance(**kwargs)
        # have to do it this way because __setattr__ is overridden
        object.__setattr__(result, "_factory", self)
        if primary_type is not None:
            #setattr(result, RDF_TYPE, self.DataValue(primary_type, XS+"anyURI"))
            setattr(result, RDF_TYPE, self.StringValue(primary_type))
        for (prop, value) in kwargs.items():
           setattr(result, prop, value)
        return result

    def Sequence(self, items=[]):
        result = self.rawSequence()
        result.nsmap = self.nsmap
        result.factory = self
        for item in items:
            result.append(item)
        return result
    
    def DataValue(self, value, datatype=None):
        """Return a DataValue object suitable for this value.  If the
        datatype is omitted, we use something based on the python type
        and the value (eg the number 10 would be an xs:unsigned_byte);
        if you really care, give us the datatype.  If you give a
        datatype and the value is a python string, it will be taken,
        untouched, as the lexical representation."""
        raise SubclassShouldProvideThis
    
    def PlainLiteral(self, text):
        return self.DataValue(text, RDF+"PlainLiteral")

    def StringValue(self, text):
        return self.DataValue(text, XS+"string")

    # generally, you these should be created internally by Instance
    def Multi(self, values=[], **kwargs):
        result = self.rawMulti(**kwargs)
        result.nsmap = self.nsmap
        result.factory = self
        for v in values:
            result.add(v)
        return result

    def deepcopy(self, item):
        """Make a deep copy of the given node item, using this
        factory."""

        if isinstance(item, Instance):
            n = self.Instance()
            for p in item.properties:
                m = getattr(n, p)
                for v in getattr(item, p).values:
                    vv = self.deepcopy(v)
                    m.add(vv)
        elif isinstance(item, Sequence):
            n = self.Sequence()
            for i in item.items:
                n.append(self.deepcopy(i))
        elif isinstance(item, DataValue):
            n = self.DataValue(item.lexrep, item.datatype)
        elif isinstance(item, Multi):
            raise RuntimeError("don't try to copy a Multi; they're internal")
        else:
            raise RuntimeError("dont know how to copy "+repr(item))

        assert isinstance(n, Value)
        assert n is not item
        if item == n:
            pass # print >>sys.stderr, "\nDeepcopy DID work:\n     ", `item`, "\n     ", `n`, "\n"
        else:
            print >>sys.stderr, "\nDeepcopy did NOT work:\n     ", `item`, "\n     ", `n`, "\n"
            if n == item:
                raise RuntimeError
        if item == item:
            pass # print >>sys.stderr, "\nItem Self eq:    ", `item`
        else:
            print >>sys.stderr, "\nItem Self NOT eq:    ", `item`
        if n == n:
            pass # print >>sys.stderr, "\nNew Self eq:    ", `n`
        else:
            print >>sys.stderr, "\nNew Self NOT eq:    ", `n`
        return n


class Multi(object):
    
    __slots__ = ["nsmap", "factory"]

    @property
    def is_Multi(self):
        return True

    @property
    def values_list(self):
        """When a generator (.values) isn't good enough, and you want
        a real list.  Should we make it so assignment to this changes
        the values...?"""
        return [x for x in self.values]

    def __repr__(self):
        return "Multi(values="+`self.values_list`+")"

    def __len__(self):
        return len(self.values_list)

    def __eq__(self, other):
        #print >>sys.stderr, "multi eq running", self
        if not isinstance(other, Multi):
            return False

        others = set(other.values)
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
        n = 0
        for v in self.values:
            n +=1 
            result = v
            if n > 1:
                raise RuntimeError('Too many values for "the", including: '+`self.values_list[0]`+' and '+`v`)
        if n == 0:
            raise RuntimeError('Too few values for "the"')
        return result


    @property
    def any(self):
        for v in self.values:
            return v
        raise IndexError

    @property
    def first(self):
        """Using this implies you require that values
        be kept in a stable order.   Use .any unless you
        mean this."""
        for v in self.values:
            return v
        raise IndexError


class Instance(Value):

    __slots__ = [ "_factory", ]    

    @property
    def is_Instance(self):
        return True

    def has_type(self, type):
        for v in getattr(self, RDF_TYPE).values:
            if isinstance(v, DataValue) and v.lexrep == type:
                return True
        return False

    @property
    def properties(self):
        raise SubclassShouldProvideThis

    def _q(self, name):
        if ":" in name:
            return name
        # as low-level as we can go, since self._factory isnt working
        f = object.__getattribute__(self, "_factory")
        nsmap = f.nsmap
        return nsmap.uri(name, joining_character="_")

    def _primary_type(self):
        # not a @property, because... that breaks stuff????
        # 
        # I suggest just using _type.first.lexrep ones self, usually.
        try:
            return self._type.first.lexrep
        except IndexError:
            return None

    def _getpv(self, prop):
        raise SubclassShouldProvideThis

    def _addpv(self, prop, value):
        multi = self._getpv(prop)
        multi.add(value)

    def _setpv(self, prop, value):
        multi = self._getpv(prop)
        multi.clear()
        multi.add(value)

    def __getattr__(self, prop):
        if prop[0] is "_":
            if prop == "_type":
                prop = RDF+"type"
            else:
                # try to catch when you didn't mean it to be dynamic
                raise AttributeError
        return self._getpv(prop)
    
    def __setattr__(self, prop, value):
        if prop[0] is "_":
            if prop == "_type":
                prop = RDF+"type"
            else:
                # try to catch when you didn't mean it to be dynamic
                raise AttributeError
        return self._setpv(prop, value)
    
    def __getstate__(self):
        raise SubclassShouldProvideThis

    def __setstate__(self, state):
        raise SubclassShouldProvideThis

    def __eq__(self, other):
        #print >>sys.stderr, "instance eq running", self
        if not isinstance(other, Instance):
            return False
        k1 = sorted(self.properties)
        k2 = sorted(other.properties)
        if k1 != k2:
            return False
        for k in k1:
            if not getattr(self, k) == getattr(other, k):
                return False
        return True

    def __str__(self):
        return "Instance("+(self._primary_type() or "None")+", ...)"

    def __repr__(self):
        s = "Instance("+(self._primary_type() or "None")+", "
        for prop in self.properties:
            m = getattr(self, prop)
            for value in m.values:
                s += `prop`+"="+`value`+", "
        s += ")"
        return s


    @property
    def child_instances(self):
        '''yield each instance directly under this one (via Multi and 
        Sequence)'''

        for prop in self.properties:
            for value in getattr(self, prop):
                if isinstance(value, Sequence):
                    items = value.items
                else:
                    items = (value,)
                for item in items:
                    if isinstance(item, Instance):
                        yield item
                    elif isinstance(item, DataValue):
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
            values = self.list_map(multi.values, func, True, args, kwargs)
            multi.clear()
            for value in values:
                multi.add(value)
        new_self = func(self, *args, **kwargs)
        debug('ast2-map)')
        return new_self

    def list_map(self, values, func, collapse_dups, args, kwargs):
        '''call func on each item in this array of instances and
        return a new array of the resulting instances; used by map_in_place

        Don't use it directly -- it's secretly destructive inside :-(
        '''

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
            elif isinstance(value, DataValue):
                result.append(value)
            else:
                raise RuntimeError('bad AST tree:'+`value`)

        return result

    def to_python(self, map):
        """
        


        ...  wow, have I written code like this a lot, and I'm never
        very happy with it.  It might make sense to use some sort of
        schema; I think we have one floating around somewhere.

        """
        (ns, local) = ns_split(self._primary_type())
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

        if self._primary_type() != other._primary_type():
            print "Primary Type Difference", self._primary_type(), "<>", other._primary_type()
            return False

        print prefix, self._primary_type()
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

class Sequence(Value):

    __slots__ = [ "factory" ]

    @property
    def is_Sequence(self):
        return True

    def append(self, new):
        raise SubclassShouldProvideThis

    def extend(self, new):
        # override this for more efficiency, of course
        for item in new:
            self.append(item)

    def __add__(self, other):
        return self.factory.Sequence(items=(self.items + other.items))

    def __eq__(self, other):
        #print >>sys.stderr, "sequence eq running", self
        if not isinstance(other, Sequence):
            return False
        self_items = [x for x in self.items]
        other_items = [x for x in other.items]
        if len(self_items) != len(other_items) :
            return False
        for i in range(0, len(self_items)):
            if not self_items[i] == other_items[i]:
                return False
        return True

    def __repr__(self):
        s = "[ "
        for i in self.items:
            s += repr(i)
            s += " "
        s += "]"
        return s

class DataValue(Value):

    __slots__ = []

    @property
    def is_DataValue(self):
        return True

    def __eq__(self, other):
        #print >>sys.stderr, "datavalue eq running", `self.lexrep`, `self.datatype`
        #print >>sys.stderr, "                    ", `other.lexrep`, `other.datatype`
        #lr_same = self.lexrep == other.lexrep
        #print >>sys.stderr, "lr_same? ", lr_same
        #dt_same = self.datatype == other.datatype
        #print >>sys.stderr, "dt_same? ", dt_same
        #same = lr_same and dt_same
        return self.lexrep == other.lexrep and self.datatype == other.datatype

if __name__ == "__main__":
    import doctest, sys
    doctest.testmod(sys.modules[__name__])
