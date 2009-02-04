#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

A "fully-striped" XML Serialization, knowing nothing of RIF (or RDF),
just out AST notion.   (ie, properties, values, Sequences)

Very, very verbose.  :-)

"""

import sys
import serializer
import plugin
from cStringIO import StringIO
import xml.sax.saxutils as saxutils

import AST

class Serializer(serializer.General):

    def default_do(self, obj):

        if obj is None:
            self.out('**NONE**')
            return
        if isinstance(obj, list):
            self.out('**LIST**')
            return
        if isinstance(obj, tuple):
            self.out('**TUPLE**')
            return


        if isinstance(obj, basestring):
            self.out(saxutils.escape(obj))
            return

        self.xml_begin(obj._type[1])
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
                    self.xml_begin(key, one_line=(count==1))
                    self.do(item)
                    self.xml_end(one_line=(count==1))
            elif isinstance(value, AST.Sequence):
                self.xml_begin(key)
                self.xml_begin('List')
                for item in value.items:
                    if isinstance(item, basestring):
                        self.xml_begin("li")
                        self.do(item)
                        self.xml_end()
                    else:
                        self.do(item)
                self.xml_end()
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
   """A fully-striped XML Syntax (not the RIF XML Syntax -- easier to implement, but more verbose)."""

   id="fsxml"
   #spec="http://www.w3.org/TR/2008/WD-rif-bld-20080730/#XML_Serialization_Syntax_for_RIF-BLD"
   
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

