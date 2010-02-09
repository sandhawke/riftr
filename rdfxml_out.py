#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

"""

import sys

import nodecentric
import nodewriter
import plugin
from cStringIO import StringIO

import xml_in

XS = nodecentric.XS
xmlns = "http://www.w3.org/XML/1998/namespace"
rifns = xml_in.RIFNS
rifrns = "http://www.w3.org/2007/rifr#"
rdfns = nodecentric.RDF

rank = {
    rifns+"id": "01",
    rifns+"meta": "02",
    }

class Writer(nodewriter.General):

    def default_do(self, obj):

        need_close = 0

        if isinstance(obj, nodecentric.Instance):
            if self.current_element is None and self.add_root:
                self.xml_begin(rdfns+"RDF")
                need_close += 1

            classname = obj.primary_type.replace(rifns, rifrns)

            if self.skip:
                if ( self.current_element is None or 
                     need_close == 1 or 
                     self.current_element.getAttributeNS(rdfns, "parseType") ):
                    self.xml_begin(classname)
                    need_close += 1
                else:
                    self.current_element.setAttributeNS(rdfns, "parseType", "Resource")
            else:
                self.xml_begin(classname)
                need_close = True

            properties = obj.properties
            properties = sorted(properties,
                                key=lambda x: rank.get(x,"99")+x
                                )
            for prop in properties:
                for value in getattr(obj, prop).values:
                    if prop == nodecentric.RDF_TYPE: # @@@ and value.lexrep == classname:
                        continue
                    prop = prop.replace(rifns, rifrns)
                    self.xml_begin(prop)
                    self.do(value)
                    self.xml_end()
            
            while need_close > 0:
                self.xml_end()
                need_close -= 1
        else:
            msg = "Don't know how to serialize a "+str(type(obj))+ ": "+repr(obj)
            self.xml_begin("ERROR", {(None, "msg"): msg})
            self.xml_end()
            #print >>sys.stderr, msg
            raise RuntimeError(msg)

    def do_BaseDataValue(self, obj):  
        if obj.datatype == rifns+"iri":
            self.current_element.setAttributeNS(rdfns, "resource", obj.lexrep)
        elif obj.datatype == rdfns+"PlainLiteral":
            (text, lang) = obj.lexrep.rsplit("@",1)
            if lang:
                self.current_element.setAttribute("xml:lang", lang)
            self.xml_set_text(text)
        else:
            self.current_element.setAttributeNS(rdfns, "datatype", obj.datatype)
            self.xml_set_text(obj.lexrep)

    def do_Sequence(self, obj):
        self.current_element.setAttributeNS(rdfns, "parseType", "Collection")
        for item in obj.items:
            self.do(item)

_default_writer = Writer()

def do(obj):
    _default_writer.do(obj)

class Plugin (plugin.OutputPlugin):
   """RIF in RDF/XML out."""

   id=__name__

   spec=""

   options = [
       plugin.Option('indent_factor', 'Number of spaces to indent each level',
                     default="4"),
       plugin.Option('skip', 'Use parsetype=Resource to make more-terse RDF',
                     default=False),
       plugin.Option('add_root', 'Add an rdf:RDF element',
                     default=False),
       ]


   def __init__(self, **kwargs):
       # should plugin.Plugin do this for us, somehow?
       for option in self.options:
           kwargs.setdefault(option.name, option.default)
       self.ser = Writer(**kwargs)

   def serialize(self, doc, output_stream):
       self.ser.stream = output_stream
       self.ser.do(doc)
  
plugin.register(Plugin)


if __name__ == "__main__":
    import xml_in_etree

    docnode = xml_in_etree.Plugin().parse(sys.stdin.read())
    Plugin().serialize(docnode, sys.stdout)
    
