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
        s += self.ps_heart(newline+'    ')
        if s.endswith('    '):
            s = s[:-4]
        s += ")"
        return s

class Document(SmartObj):
    
    def ps_heart(self, newline):
        s = newline
        if self.meta:
            s += as_ps(self.meta, newline)
            s += newline
        if self.base:
            s += 'Base('+ps_quoted_string(self.base)+')'+newline
            s += newline
        if self.prefix:
            for (short, long) in self.prefix:
                s += 'Prefix(%s %s)%s' % (short, long, newline)
            s += newline
        # @@@ import, group
        return s
    

class Group(SmartObj):
    pass

class And(SmartObj):
    pass

class Atom(SmartObj):
    pass

class ExternalExpr(SmartObj):
    pass

class ExternalAtom(SmartObj):
    pass

class Const(SmartObj):
    pass

class Var(SmartObj):
    pass

class Implies(SmartObj):
    pass

class Forall(SmartObj):
    pass
