#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

"""

import sys
import serializer
import plugin

class Serializer(serializer.General):

    def xxx_do_Document(self, obj):
        #gather_ns(obj)
        self.xml_begin("Document")
        self.xml_begin("payload")

        if obj.group:
            self.do(obj.group)

        self.xml_end()
        self.xml_end()

    def default_do(self, obj):

        if isinstance(obj, basestring):
            self.out(obj)
            return

        if isinstance(obj, tuple):
            self.out("TUPLE("+`obj`+")")
            return

        classname = type(obj).__name__
        self.xml_begin(classname)
        for (key, value) in obj.__dict__.items():
            if value is None:
                continue
            if isinstance(value, list):
                # which style to do?   repeat or nest???
                for item in value:
                    self.xml_begin(key)
                    self.do(item)
                    self.xml_end()
            else:
                self.xml_begin(key)
                self.do(value)
                self.xml_end()
        self.xml_end()

_default_serializer = Serializer()

def do(obj):
    _default_serializer.do(obj)


class Plugin (plugin.OutputPlugin):
   """RIF XML Syntax"""

   id="xml"
   spec="http://www.w3.org/TR/2008/WD-rif-bld-20080730/#XML_Serialization_Syntax_for_RIF-BLD"
   
   def serialize(self, str):
       buffer = StringIO()
       ser  = bld_xml_out.Serializer(stream=buffer)
       ser.do(doc)
       return (notes, buffer.getvalue())
 
plugin.register(Plugin())

        
if __name__ == "__main__":
    
    import ps_parse
    import sys

    s = sys.stdin.read()
    doc = ps_parse.parse(s)
    do(doc)
    print

