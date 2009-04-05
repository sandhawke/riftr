#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

"""

import sys
import serializer2
import plugin
from cStringIO import StringIO

import AST2
import xml_in

rifns = xml_in.RIFNS

class Serializer(serializer2.General):

    def default_do(self, obj):

        if isinstance(obj, AST2.Instance):
            classname = obj.primary_type
            self.xml_begin(classname)
            for prop in obj.properties:
                for value in getattr(obj, prop).values:
                    if prop == AST2.RDF_TYPE and value.lexrep == classname:
                        continue
                    self.xml_begin(prop)
                    self.do(value)
                    self.xml_end()
            self.xml_end()
        else:
            msg = "Don't know how to serialize a "+str(type(obj))+ ": "+repr(obj)
            self.xml_begin("ERROR", {(None, "msg"): msg})
            self.xml_end()
            #raise RuntimeError(msg)

    def do_Var(self, obj):
        self.xml_begin(rifns+'Var')
        self.xml_set_text(getattr(obj, rifns+"name").the.lexrep)
        self.xml_end()

    def do_StringValue(self, obj):
        self.xml_set_text(obj.lexrep)

    def do_BaseDataValue(self, obj):
        self.xml_begin(rifns+'Const', {(None, 'type'):obj.datatype})
        self.xml_set_text(obj.lexrep)
        self.xml_end()

    def do_Sequence(self, obj):
        self.current_element.setAttributeNS(None, "ordered", "yes")
        for item in obj.items:
            self.do(item)

    # strings?   data values?


_default_serializer = Serializer()

def do(obj):
    _default_serializer.do(obj)


class Plugin (plugin.OutputPlugin):
   """RIF XML out."""

   id=__name__

   spec="http://www.w3.org/TR/2008/WD-rif-bld-20080730/#XML_Serialization_Syntax_for_RIF-BLD"

   options = [
       plugin.Option('indent_factor', 'Number of spaces to indent each level',
                     default="4"),
       ]


   def __init__(self, **kwargs):
       self.ser = Serializer(**kwargs)

   def serialize(self, doc, output_stream):
       self.ser.output_stream = output_stream
       self.ser.do(doc)
  
plugin.register(Plugin)
