#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

Output AST as fully striped XML, without knowing anything about RIF.

Use ordered=yes on everything that's a list.  Other options would be
to only do it on lists with 0 or 1 items, and to call it
parsetype=list or items=0/1 or count=0/1.  or numitems=0/1.

"""

import sys
import nodewriter
import nodecentric
import plugin
import qname

RDF = qname.common.rdf
RDFS = qname.common.rdfs

class Serializer(nodewriter.General):

    def default_do(self, obj):

        if isinstance(obj, nodecentric.Instance):
            classname = obj._primary_type() or RDFS+"Resource"
            self.xml_begin(classname)
            properties = obj.properties
            properties = sorted(properties)
            for prop in properties:
                for value in getattr(obj, prop).values:
                    if prop == nodecentric.RDF_TYPE and value.lexrep == classname:
                        continue
                    self.xml_begin(prop)
                    self.do(value)
                    self.xml_end()
            self.xml_end()
        elif isinstance(obj, nodecentric.DataValue):
            self.do_DataValue(obj)
        else:
            msg = "Don't know how to serialize a "+str(type(obj))+ ": "+repr(obj)
            self.xml_begin("ERROR", {(None, "msg"): msg})
            self.xml_end()
            #raise RuntimeError(msg)

    def xxx_do_StringValue(self, obj):
        self.xml_set_text(obj.lexrep)

    def do_PlainLiteral(self, obj):
        (text, lang) = obj.lexrep.rsplit("@",1)
        assert lang == ""
        self.xml_set_text(text)

    def do_Sequence(self, obj):
        self.current_element.setAttributeNS(None, "ordered", "yes")
        for item in obj.items:
            self.do(item)

    def do_DataValue(self, obj):
        self.current_element.setAttributeNS(None, "type", obj.datatype)
        self.xml_set_text(obj.lexrep)


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
       self.ser.stream = output_stream
       self.ser.do(doc)
  
