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

    def __init__(self, indent_factor, slot_operator):
        super(Serializer, self).__init__(indent_factor=indent_factor)
        self.slot_operator = slot_operator

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
        self.out(" "+self.slot_operator+" ")
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


class Plugin (plugin.OutputPlugin):
   """A variant, made up, presentation syntax"""

   id="xps_out"

   options = [
       plugin.Option('indent_factor', 'Number of spaces to indent each level',
                     default="4"),
       plugin.Option('slot_operator', 'Which character to use as the slot operator',  default="->"),
       
       ]
 
   def __init__(self, **kwargs):
       # We *could* make the Plugin *be* the Serializer, but that feels a
       # little too confusing for me right this moment.
       self.ser = Serializer(**kwargs)

   def serialize(self, doc, output_stream):
       self.ser.output_stream = output_stream
       self.ser.do(doc)
  
plugin.register(Plugin)

        
