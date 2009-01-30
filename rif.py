#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

"""

def as_debug(obj, newline="\n"):
    if hasattr(obj, 'as_debug'):
        return obj.as_debug(newline)
    else:
        return `obj`

def as_ps(obj, newline="\n"):
    if hasattr(obj, 'as_ps'):
        return obj.as_debug(newline)
    else:
        raise RuntimeError("dont know how to serialized %s in ps" % obj)

def ps_quoted_string(s):
    if '"' in s:
        raise RuntimeError("no way to serialize a string with a double-quote in it")
    return '"'+s+'"'

class SmartObj:
    
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

    def as_ps(self, newline="\n"):
        try:
            s = self.ps_name
        except:
            s = self.__class__.__name__
        s += " ("

        # @@@ do meta here

        s += self.ps_heart(newline+'    ')
        if s.endswith('    '):
            s = s[:-4]
        s += ")"
        return s

class Document(SmartObj):
    
    def ps_heart(self, newline):
        s = newline
        if self.base:
            s += 'Base('+ps_quoted_string(self.base)+')'+newline
            s += newline
        if self.prefix:
            for (short, long) in self.prefix:
                s += 'Prefix(%s %s)%s' % (short, long, newline)
            s += newline
        # @@@ import
        if self.group:
            s += self.group.as_ps(newline)
            s += newline
        return s

class Group(SmartObj):

    def ps_heart(self, newline):
        s = newline
        for sent in self.sentence:
            s += sent.as_ps(newline) + newline
        return s

class And(SmartObj):
    pass

class Atom(SmartObj):
    
    def as_ps(self, newline):
        sa = []
        for arg in self.args:
            sa.append(arg.as_ps(newline))
        return self.op.as_ps(newline) + "(" + " ".join(sa) + ")"

class ExternalExpr(SmartObj):
    pass

class ExternalAtom(SmartObj):
    pass

class Const(SmartObj):
    
    def as_ps(self, newline):
        
        # hack for now!
        try:
            (pre,rest) = self.value
            return pre+":"+rest
        except:
            pass

        # want a flag about whether to use APS !?
        self.determine_lexrep()
        return (ps_quoted_string(self.lexrep) + 
                "^^" + 
                # needs qname smarts -- prefix and stuff!
                self.datatype.as_ps(newline))

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
