#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

To do...

    --- qnames/curies/prefix
    --- meta
    --- real datatype handling, with PS/APS flag
           (third arg, FLAGS, or more cleverly 
           a state object?     ctl.newline += "   "
           ctl.forcehathat, ctl.width, ...
           maybe even ctl.oneline --- although, 
           perhaps newline can just come in as ""?
    --- to XML
    --- some kind of from XML
    --- to RDF
    --- from RDF

"""

import re

from debugtools import debug

import plugin
import ps_lex

#use_qnames = False

def as_debug(obj, newline="\n"):
    if hasattr(obj, 'as_debug'):
        return obj.as_debug(newline)
    else:
        return `obj`

def as_ps(obj, newline="\n"):
    if hasattr(obj, 'as_ps'):
        return obj.as_ps(newline)
    else:

        # @HACK
        #try:
        #    (pre,rest) = obj
        #    return pre+":"+rest
        #except:
        #    pass
        
        #if isinstance(obj, basestring):
        #    return obj  # not a great idea....

        raise RuntimeError("dont know how to serialized %s in ps" % obj)

def ps_quoted_string(s):
    if '"' in s:
        raise RuntimeError("no way to serialize a string with a double-quote in it")
    return '"'+s+'"'

class SmartObj(object):
    xml_ns = "http://www.w3.org/2007/rif#"
    
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

        # this is a form of metadata which ps_parser provides,
        # and it would be hard to change it, so we'll convert here.
        annotation = getattr(self, "annotation", None)
        if annotation is not None:
            id = getattr(annotation, "iri", None)
            if id is not None:
                self.id = id
            meta = getattr(annotation, "sentence", None)
            if meta is not None:
                self.meta = meta

    def __str__(self):
        return self.as_debug()

    #def __repr__(self):
    #    return str(self)

    def as_debug(self, newline="\n"):
        newline += "-  "
        s=""
        for (key, value) in self.__dict__.items():
            if value is None: 
                continue
            s += " %s: " % key
            if isinstance(value, list):
                s += "[ "
                if len(value) == 0:
                    pass
                elif len(value) == 1:
                    s += as_debug(value[0], newline)
                else:
                    s += newline
                    for v in value:
                        s+= "   %s, \n%s" % (as_debug(v, newline), newline)
                s += " ]" + newline
            else:
                s += "%s\n%s" % (as_debug(value, newline), newline)
        return self.__class__.__name__ + "("+newline + s + ")"

    def do_meta_ps(self, newline):

        s = ""
        id = getattr(self, "id", None)
        if id is not None:
            s += id.as_ps(newline)
            s += " "
            
            
        meta = getattr(self, "meta", None)
        if meta is not None:
            s += meta.as_ps(newline)

        #if len(frames) == 0:
        #    pass
        #elif len(frames) == 1:
        #    s += " "+frames[0].as_ps(newline+"    ")
        #else:
        #    s += "And("+newline
        #    newline += "    "
        #    for f in frames:
        #        s += "    " +  frames[0].as_ps(newline) + newline
        #    s += ")"
            
        if s == "":
            return s
        else:
            return "(* " + s + " *) " + newline

    def as_ps(self, newline="\n"):

        s = self.do_meta_ps(newline)
        try:
            s += self.ps_name
        except:
            s += self.__class__.__name__
        s += " ("
        s += self.ps_heart(newline+'    ')
        if s.endswith('    '):
            s = s[:-4]
        s += ")"
        return s

    def add_to_prefix_map(self, map):

        debug('prefix_map(', 'scanning', `self`)

        for (key, value) in self.__dict__.items():
            debug('prefix_map(', 'key=', key, `value`)
            if key.startswith("_"):
                debug('prefix_map)', 'key starts with _')
                continue

            if isinstance(value, list):
                values = value
            else:
                values = (value,)

            for v in values:
                debug('prefix_map(', 'a value:',  `v`)
                try:
                    f =  v.add_to_prefix_map
                except:
                    debug('prefix_map)', '... is opaque')
                    continue

                f(map)
                debug('prefix_map)', 'done with value')

            debug('prefix_map)', 'done with key', key)
        debug('prefix_map)')

class Document(SmartObj):
    
    def ps_heart(self, newline):
        s = newline
        
        # figure out a smart base?
        #if self.get_base():
        #    s += 'Base('+ps_quoted_string(self.base)+')'+newline
        #    s += newline


        if use_qnames:
            if hasattr(self, '_prefix_map'):
                map = self._prefix_map
            else:
                map = PrefixMap()
            self.add_to_prefix_map(map)
            debug('prefix_map', 'final map:', `map.entries`)
            for (short, long) in map.entries:
                s += 'Prefix(%s <%s>)%s' % (short, long, newline)
            s += newline

        # @@@ import

        if self.payload:
            s += self.payload.as_ps(newline)
            s += newline
        return s

    def get_base(self):
        if hasattr(self, 'base'):
            return self.base
        return None  # for now...



common = {
    "http://www.w3.org/2007/rif#" : "rif",
    "http://www.w3.org/2007/rif-builtin-function#" : "rifbif",
    "http://www.w3.org/2007/rif-builtin-predicate#" : "rifbip",
    'http://www.w3.org/1999/02/22-rdf-syntax-ns#':'rdf',
    'http://www.w3.org/2000/01/rdf-schema#' :'rdfs',
    'http://www.w3.org/2001/XMLSchema#' : 'xsd',
    'http://purl.org/dc/elements/1.0/' : 'dc10',
    'http://purl.org/dc/elements/1.1/' : 'dc',
    'http://xmlcommon.com/foaf/0.1/' : 'foaf',
    'http://www.w3.org/2000/10/swap/log#' : 'log',
    'http://www.w3.org/2002/07/owl#' : 'owl',
}

class PrefixMap:
    """Why not just use a dict, or a pair of them?  I guess I find
    this less confusing, and for some reason I find this subject very
    confusing."""

    def __init__(self):
        self.entries = []
        self.gen_count = 0

    def add(self, short, long):
        if self.has_short(short):
            if self.expand(short) == long:
                pass  # just a dup
            else:
                raise RuntimeError, 'changing prefix binding'
        self.entries.append( (short, long) )
        debug('prefix_map', 'added entry', short, long)
        
    def add_long(self, long):
        """When you don't know what the short should be..."""
        if self.has_long(long):
            return

        if long in common:
            short = common[long]
            if not self.has_short(short):
                self.add(short, long)
                return

        short = "ns"+str(self.gen_count)
        self.gen_count += 1
        self.add(short, long)
        
    def has_short(self, short):
        for (s, l) in self.entries:
            if s == short:
                return True
        return False

    def has_long(self, long):
        for (s, l) in self.entries:
            if l == long:
                return True
        return False

    def get_long(self, short):
        for (s, l) in self.entries:
            if s == short:
                return l
        raise KeyError(short)

    def get_short(self, long):
        for (s, l) in self.entries:
            if l == long:
                return s
        raise KeyError(short)

    def get_pair(self, iri):
        for (s, l) in self.entries:
            if iri.startswith(l):
                return (s, iri[len(l):])
        raise KeyError(iri)




def ncname_char(char):
    """
    Is this text a valid ncname character?

    Doesn't really implement 
    http://www.w3.org/TR/REC-xml-names/#NT-NCName
    as it should.   Is there some code somewhere in
    the python library that does that?
    """
    return char.isalnum() or char == "-"

def ncname_start_char(char):
    return char.isalpha()

host_only_pattern = re.compile(r'''^[-a-zA-Z_]*://[-a-zA-Z0-9_.]*$''')

def iri_split(text):
    """
    Split an IRI into a long_part and a local_part, where local_part
    is as long as possible while still matching the NCName production
    http://www.w3.org/TR/REC-xml-names/#NT-NCName

    Also, don't split the host part of the URI?


    >>> iri_split("http://www.w3.org#x")
    ('http://www.w3.org#', 'x')

    >>> iri_split("http://www.w3.org#foo")
    ('http://www.w3.org#', 'foo')

    >>> iri_split("http://www.w3.org/foo")
    ('http://www.w3.org/', 'foo')

    >>> iri_split("http://www.w3.org?foo=bar")
    ('http://www.w3.org?foo=', 'bar')

    >>> iri_split("http://www.w3.org")
    Traceback (most recent call last):
    ...
    IndexError

    # can't start with a number
    >>> iri_split("http://www.w3.org/123abc")
    ('http://www.w3.org/123', 'abc')

    >>> iri_split("http://www.w3.org#")
    Traceback (most recent call last):
    ...
    IndexError: string index out of range

    >>> iri_split("http://www.w3.org#123")
    Traceback (most recent call last):
    ...
    IndexError: string index out of range

    """
    m = host_only_pattern.match(text)
    if m is not None:
        raise IndexError
    pos = len(text)-1
    while ncname_char(text[pos]):
        pos -= 1
    while not ncname_start_char(text[pos]):
        pos += 1
    if pos < len(text):
        return (text[0:pos], text[pos:])
    else:
        raise IndexError
    
class IRI (SmartObj):
    
    def __init__(self, text):
        self.text = text
        self.map = None
    
    def add_to_prefix_map(self, map):
        
        debug('prefix_map', 'adding IRI', self.text)

        # hack!   save the map used!    hack!   hack!
        #
        #   (otherwise, we'd have to pass it all the way down,
        #   or switch to using a serializer object.)
        #
        self.map = map

        try:
            (long, local_part) = iri_split(self.text)
            map.add_long(long)
        except IndexError:
            pass

    def as_ps(self, newline):

        if use_qnames:
            try:
                (prefix, local_part) = self.map.get_pair(self.text)
            except KeyError:
                return "<"+self.text+">"
            return prefix+":"+local_part
        else:
            return "<"+self.text+">"

    def __cmp__(self, other):
        return cmp(self.text, other.text)

class Import (SmartObj):

    def ps_heart(self, newline):
        s = self.location.as_ps(newline)
        if hasattr(self, 'profile'):
            s += " "+self.profile.as_ps(newline)
        return s

class Group(SmartObj):

    def ps_heart(self, newline):
        s = newline
        for sent in self.sentence:
            s += sent.as_ps(newline) + newline
        return s

class And(SmartObj):

    def ps_heart(self, newline):
        s = newline
        for sent in self.formula:
            s += sent.as_ps(newline) + newline
        return s

class TERM(SmartObj):
    pass

class UNITERM(TERM):
    pass

class Atom(UNITERM):
    
    def as_ps(self, newline):
        sa = []
        debug('ps_out', 'args: ', `self.args`)
        for arg in self.args:
            sa.append(as_ps(arg, newline))
        return self.op.as_ps(newline) + "(" + " ".join(sa) + ")"

class Expr(UNITERM):

    def as_ps(self, newline):
        sa = []
        for arg in self.args:
            sa.append(arg.as_ps(newline))
        return self.op.as_ps(newline) + "(" + " ".join(sa) + ")"

class External(TERM):

    ps_name = "External"
        
    def ps_heart(self, newline):
        return as_ps(self.content, newline)
        
class ExternalExpr(External):
    pass

class ExternalAtom(External):
    pass

class Const(SmartObj):
    
    #def __str__(self):
    #    self.determine_lexrep()
    #    return("%s^^<%s>" % (`self.lexrep`, self.datatype))

    def add_to_prefix_map(self, map):
        
        if use_qnames:

            self.datatype.add_to_prefix_map(map)

            if self.datatype.text == 'http://www.w3.org/2007/rif#iri':
                self.iri_value = IRI(self.lexrep)
                self.iri_value.add_to_prefix_map(map)
            
    def as_ps(self, newline):
        
        try:
            return self.iri_value.as_ps(newline)
        except:
            pass

        if self.datatype.text == 'http://www.w3.org/2007/rif#local':
            if ps_lex.token_type(self.lexrep) == 'LOCALNAME':
                return self.lexrep

        if self.datatype.text == 'http://www.w3.org/2001/XMLSchema#integer':
            if ps_lex.token_type(self.lexrep) == 'INTEGER':
                return self.lexrep
            
        return (ps_quoted_string(self.lexrep) + 
                "^^" + 
                self.datatype.as_ps(newline)
                )

    def XXXXXX_determine_lexrep(self):
        try:
            x = self.lexrep
            return
        except AttributeError:
            pass
        try:
            value = self.value
        except AttributeError:
            raise RuntimeError('Cant serialize Const without value')
        
        if isinstance(value, int):
            self.lexrep = str(value)
            self.datatype = XSD_INT

        raise RuntimeError('Dont know how to serialize %s' % `value`)
            
            
            
class Var(SmartObj):
    
    def as_ps(self, newline):
        return "?"+self.name

class Implies(SmartObj):

    def as_ps(self, newline):
        return self.then.as_ps(newline) + " :- " + self.if_.as_ps(newline)

class Forall(SmartObj):
    
    def as_ps(self, newline):
        s = "Forall "
        for v in self.declare:
            s += v.as_ps(newline)+" "
        newline += "    "
        s += "("+newline+self.formula.as_ps(newline)+newline[:-4]+")"
        return s

class Slot(SmartObj):

    def as_ps(self, newline):
        return "*slot*"

class Frame(SmartObj):
    
    def as_ps(self, newline):
        s = as_ps(self.object, newline)
        if len(self.slot) == 1:
            s += "[%s -> %s]" % (
                as_ps(slot.key, newline+"    "),
                as_ps(slot.value, newline+"    "),
                )
        else:
            newline += "    "
            s += "["+newline
            for slot in self.slot:
                s += "%s -> %s%s" % (
                    as_ps(slot.key, newline),
                    as_ps(slot.value, newline),
                    newline)
            s += "] "
        return s


class Equal(TERM):

    def as_ps(self, newline):
        return self.left.as_ps(newline) + " = " + self.right.as_ps(newline)


class Annotation(SmartObj):

    pass

class Property:
    def __init__(self, name, range, 
                 list_valued=False, required=False,
                 python_name=None):
        self.name = name
        self.range = range
        self.list_valued = list_valued
        self.required = required
        self.python_name = python_name or name

    @property
    def xml_name(self):
        return '{http://www.w3.org/2007/rif#}'+self.name

    def __repr__(self):
        return 'Property(%s)' % `self.name`

bld_schema = {
    
    Document : 
    [
        Property("payload", Group),
        ],
    
    Frame :
        [
        Property("object", Const, required=True),
        Property("slot", None, list_valued=True),  # WEIRD
        ],
    
    Group :
        [
        Property('id', Const),
        Property('meta', None),
        Property('sentence', None, list_valued=True),
        ],
    
    Atom :
        [
        Property('op', Const, required=True),
        Property('args', None, list_valued=True),
        ],
    
    Expr :
        [
        Property('op', Const, required=True),
        Property('args', None, list_valued=True),
        ],
    
    External :
        [
        Property('content', UNITERM, required=True),
        ],
    
    
    And :
        [
        Property('formula', TERM, list_valued=True),
        ],
    
    
    Equal :
        [
        Property('left', None, required=True),
        Property('right', None, required=True),
        ],

    Implies :
        [
        Property('if', None, required=True, python_name="if_"),
        Property('then', None, required=True),
        ],


    Forall :
        [
        Property('declare', None, list_valued=True),
        Property('formula', None, required=True),
        ],


}


#   required == minOccurs 0/1
#   list_valued == maxOccurs 1, >1 
#                  AND ALSO how python handles it.




class Plugin (plugin.OutputPlugin):
   """RIF Presentation Syntax"""

   id="ps"
   spec="http://www.w3.org/TR/2008/WD-rif-bld-20080730/#EBNF_Grammar_for_the_Presentation_Syntax_of_RIF-BLD"
   
   def serialize(self, doc):
       global use_qnames
       use_qnames = True
       return as_ps(doc)
 
plugin.register(Plugin())

class Plugin2 (plugin.OutputPlugin):
   """RIF Presentation Syntax (with full IRIs -- no QNames)"""

   id="psnq"
   spec="http://www.w3.org/TR/2008/WD-rif-bld-20080730/#EBNF_Grammar_for_the_Presentation_Syntax_of_RIF-BLD"
   
   def serialize(self, doc):
       global use_qnames
       use_qnames = False
       return as_ps(doc)
 
plugin.register(Plugin2())


if __name__ == "__main__":
    import doctest, sys
    doctest.testmod(sys.modules[__name__])

