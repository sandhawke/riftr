#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""



"""

import serializer
import plugin
from cStringIO import StringIO

import AST

from ps_parse import RIF_IRI

class Serializer(serializer.General):

    def begin(self, tag,  one_line=False):
        #if not one_line: self.lend(2)
        self.out(tag+"(")
        self.lend(2)
        self.indent += 1

    def end(self, one_line=False):
        self.indent -= 1
        self.out(")")
        if not one_line: self.lend(2)

    def do_str(self, obj):
        self.out(repr(obj))

    def do_IRI(self, obj):
        self.out("<"+obj.text+">")

    def do_Const(self, obj):
        if obj.datatype == RIF_IRI:
            self.out("<"+obj.lexrep+">")
        else:
            self.out('"', obj.lexrep, '"^^')
            self.do(obj.datatype)

    def do_Slot(self, obj):
        self.do(obj.key)
        self.out(" -> ")
        self.do(obj.value)

    def do_Frame(self, obj):
        self.do(obj.object)
        self.out("[")
        self.lend(2)
        self.indent += 1
        for slot in obj.slot:
            self.do(slot)
            self.brsp()
        self.indent -= 1
        self.out("]")

    def default_do(self, obj):

        self.begin(obj._type[1])
        for (key, value) in obj.__dict__.items():
            if value is None:
                continue
            if key.startswith("_"):
                continue
            if key.endswith("_"):
                key = key[:-1]
            if isinstance(value, list):
                count = len(value)
                for item in value:
                    self.out(key, '=')
                    self.do(item)
                    self.lend(1)
            elif isinstance(value, AST.Sequence):
                self.out(key, '= [')
                for item in value.items:
                    self.do(item)
                self.out("]")
            else:
                self.out(key, '=')
                self.do(value)
                self.lend(1)
        self.end()

_default_serializer = Serializer()

def do(obj):
    _default_serializer.do(obj)


class Plugin (plugin.OutputPlugin):
   """A variant, made up, presentation syntax"""

   id="xps"
   
   def serialize(self, doc):
       buffer = StringIO()
       ser  = Serializer(stream=buffer)
       ser.do(doc)
       return buffer.getvalue()
 
plugin.register(Plugin())

        
if __name__ == "__main__":
    
    import ps_parse
    import sys

    s = sys.stdin.read()
    doc = ps_parse.parse(s)
    do(doc)
    print

