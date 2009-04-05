#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""



"""

import serializer2
import plugin
from cStringIO import StringIO

import AST2

class Serializer(serializer2.General):

    def default_do(self, obj):
        
        if isinstance(obj, AST2.Instance):
            self.out("primary_type=", obj.primary_type)
            self.indent += 1
            for prop in obj.properties:
                self.out("property: ", prop)
                self.indent += 1
                for value in getattr(obj, prop).values:
                    self.do(value)
                self.indent -= 1
            self.indent -= 1
        else:
            self.out("unknown:"+repr(obj))

class Plugin (plugin.OutputPlugin):
   """A variant, made up, presentation syntax"""

   id=__name__

   options = [
       plugin.Option('indent_factor', 'Number of spaces to indent each level',
                     default="4"),
       ]
 
   def __init__(self, **kwargs):
       # We *could* make the Plugin *be* the Serializer, but that feels a
       # little too confusing for me right this moment.
       self.ser = Serializer(**kwargs)

   def serialize(self, doc, output_stream):
       self.ser.output_stream = output_stream
       self.ser.do(doc)
  
plugin.register(Plugin)

        
