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

import decimal 

import qname

XS = "http://www.w3.org/2001/XMLSchema#"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDF_TYPE = RDF+"type"

################################################################
#
#   Base Classes -- common stuff shared by various instantiations
#
#   (I know, this feels more like Java/C++ that Python, but in this
#   case I this it's pretty elegant.)
#


class SubclassShouldProvideThis(Exception):
    pass

class NodeFactory(object):
    
    # Should we promise to keep track of the nodes we create?  Or
    # do you need to remember the roots yourself?

    def __init__(self, nsmap=None):
        if nsmap:
            self.nsmap = nsmap
        else:
            self.nsmap = qname.Map([qname.common])

    def rawInstance(self):
        raise SubclassShouldProvideThis
    def rawSequence(self):
        raise SubclassShouldProvideThis
    def rawMulti(self):
        raise SubclassShouldProvideThis

    def Instance(self, primary_type=None, **kwargs):
        result = self.rawInstance()
        # have to do it this way because __setattr__ is overridden
        object.__setattr__(result, "nsmap", self.nsmap)
        object.__setattr__(result, "factory", self)
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
    def Multi(self, values=[]):
        result = self.rawMulti()
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
            for p,v in item.items():
                n.add(p,self.deepcopy(v))
        elif isinstance(item, Sequence):
            n = self.Sequence()
            for i in item:
                n.append(self.deepcopy(i))
        elif isinstance(item, DataValue):
            n = self.DataValue(item.lexrep, item.datatype)
        elif isinstance(item, Multi):
            raise RuntimeError("don't try to copy a Multi; they're internal")
        else:
            raise RuntimeError("dont know how to copy "+repr(item))

        assert n == self and n is not self
        return n


class Multi(object):
    
    __slots__ = ["nsmap", "factory"]

    @property
    def value_list(self):
        return [x for x in self.values]

    def __repr__(self):
        return "Multi(values="+`self.value_list`+")"

    def __len__(self):
        return len(self.values_list)

    def __eq__(self, other):
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
                raise RuntimeError('Too many values for "the"')
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


class Instance(object):

    __slots__ = [ "nsmap", "factory", ]    

    def has_type(self, type):
        for v in getattr(self.RDF_TYPE):
            if isinstance(v, DataValue) and v.lexrep == type:
                return True
        return False

    @property
    def properties(self):
        raise SubclassShouldProvideThis

    @property
    def primary_type(self):
        try:
            return getattr(self, RDF_TYPE).first.lexrep
        except IndexError:
            return None

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
        ### @@@@
        if prop[0] is "_":
            raise AttributeError
        assert not isinstance(value, Multi)
        assert isinstance(prop, basestring)   # unicode?   IRI.
        prop = q(prop)
        debug('ast2', 'adding',prop,"=",value)
        self.dict.setdefault(prop, self.factory.Multi(self.nsmap)).add(value)

    def __getattr__(self, prop):
        ### @@@@
        if prop[0] is "_":
            raise AttributeError

        prop = q(prop)
        debug('ast2-get', 'returning attr for', prop)
        return self.dict.setdefault(prop, self.factory.Multi(self.nsmap))
    
    def __getstate__(self):
        raise SubclassShouldProvideThis

    def __setstate__(self, state):
        raise SubclassShouldProvideThis

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
        return "Instance("+(self.primary_type or "None")+", ...)"

    def __repr__(self):
        s = "Instance("+(self.primary_type or "None")+", "
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

class Sequence(object):

    __slots__ = [ "factory", "nsmap" ]

    def append(self, new):
        raise SubclassShouldProvideThis

    def extend(self, new):
        # override this for more efficiency, of course
        for item in new:
            self.append(item)

    def __add__(self, other):
        return self.factory.Sequence(items=(self.items + other.items))

    def __eq__(self, other):
        if not isinstance(other, Sequence):
            return False
        if len(self.items) != len(other.items) :
            return False
        for i in range(0, len(self.items)):
            if not self.items[i] == other.items[i]:
                return False
        return True

class DataValue(object):

    __slots__ = []


if __name__ == "__main__":
    import doctest, sys
    doctest.testmod(sys.modules[__name__])
