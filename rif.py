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
from debugtools import debug

import plugin

"""
 schema.classes
 schmea.superclasses(class)
 schema.is_class(class)
 schema.properties(class)
 schema.property(class, propname)

 schema.cls(clsname).prop(propname).PROP ?

 p.min_occurs = (0/1)
 p.max_occurs = (0/1) 
       if max_occurs > 1 then list-valued

"""

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
        try:
            (pre,rest) = obj
            return pre+":"+rest
        except:
            pass
        
        if isinstance(obj, basestring):
            return obj  # not a great idea....

        raise RuntimeError("dont know how to serialized %s in ps" % obj)

def ps_quoted_string(s):
    if '"' in s:
        raise RuntimeError("no way to serialize a string with a double-quote in it")
    return '"'+s+'"'

class SmartObj(object):
    xml_ns = "http://www.w3.org/2007/rif#"
    
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __str__(self):
        return self.as_debug()

    def __repr__(self):
        return str(self)

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
        try:
            (id, frames) = self.meta
        except:
            try:
                id = self.id.lexrep
                frames = self.meta
            except:
                return ""
        
        s = "(* "
        if id:
            s += "<"+id+">"
        if len(frames) == 0:
            pass
        elif len(frames) == 1:
            s += " "+frames[0].as_ps(newline+"    ")
        else:
            s += "And("+newline
            newline += "    "
            for f in frames:
                s += "    " +  frames[0].as_ps(newline) + newline
            s += ")"
        s += " *) " + newline
        return s

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

class Document(SmartObj):
    
    def ps_heart(self, newline):
        s = newline
        if self.get_base():
            s += 'Base('+ps_quoted_string(self.base)+')'+newline
            s += newline
        if self.get_prefix():
            for (short, long) in self.prefix:
                s += 'Prefix(%s %s)%s' % (short, long, newline)
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

    def get_prefix(self):
        if hasattr(self, 'prefix'):
            return self.prefix
        return None  # for now...

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

    def as_ps(self, newline):
        
        # hack for now
        try:
            s = self.value
            if isinstance(s, basestring):
                return s
        except:
            pass
            
        # hack for now!
        try:
            (pre,rest) = self.value
            return pre+":"+rest
        except:
            pass

        # hack for now
        try:
            i = self.value
            if isinstance(i, int):
                return str(i)
        except:
            pass

        # want a flag about whether to use APS !?
        self.determine_lexrep()
        return (ps_quoted_string(self.lexrep) + 
                "^^" + 
                # needs qname smarts -- prefix and stuff!
                #  IF CURIE  as_ps(self.datatype, newline))
                #  IF IRI:
                "<"+self.datatype+">"
                )

    def determine_lexrep(self):
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
        return self.left.as_ps(newline) + "=" + self.right.as_ps(newline)


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
        Property('meta', Frame, list_valued=True),
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
       return ("", as_ps(doc))
 
plugin.register(Plugin())
