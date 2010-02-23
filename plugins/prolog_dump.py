#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

Output AST as fully striped prolog, without knowing anything about RIF.

"""

import sys
import nodewriter
import nodecentric
import plugin
import qname
from swi_prolog import atom_quote

RDF = qname.common.rdf
RDFS = qname.common.rdfs

class Serializer(nodewriter.General):

    def __init__(self, supress_nsmap=False, **kwargs):
        nodewriter.General.__init__(self, **kwargs)
        self.do_props = True
        self.assertional = True
        self.metadata = []
        self.if_keep = ""
        self.in_external = False
        if 'nsmap' in kwargs:
            self.nsmap = kwargs['nsmap']
        else:
            self.nsmap = qname.Map()
            self.nsmap.defaults = [qname.common]
            self.nsmap.bind('', qname.common.rif)
        self.supress_nsmap = supress_nsmap
        self.atom_prefix = ""   # or "riftr_"

    def iri(self, text):
        # errrrr, duplicating stuff already in qname, yes?
        try:
            (long, local) = qname.uri_split(text)
        except qname.Unsplitable:
            long = ""
            local = text
        short = self.nsmap.getShort(long)
        if short != "rif":
            short = self.atom_prefix+short
        #self.outk(short+":"+atom_quote(local))
        if short == "":
            local = local.lower()  # hack...
            self.outk(atom_quote(local))
        else:
            self.outk(atom_quote(short+"_"+local))

    def irimap(self):

        #self.out(":- ensure_loaded(library('semweb/rdf_db')).")
        #for short in self.nsmap.shortNames():
            #self.out(':- rdf_register_ns('+short+', '+atom_quote(self.nsmap.getLong(short)), ").")

        if not self.supress_nsmap:
            self.out('\n% Namespaces used:')
            # self.out(':- discontiguous(ns/2).')
            for short in self.nsmap.shortNames():
                self.out('ns('+atom_quote(short)+', '+atom_quote(self.nsmap.getLong(short)), ").")
            self.out('\n')

        # someone should call irimap at the end....

    def default_do(self, obj):

        if isinstance(obj, nodecentric.Instance):
            classname = obj._primary_type() or RDFS+"Resource"
            self.iri(classname)
            self.indent += 1
            if self.do_props:
                self.out("(")
            else:
                self.outk("(")
            properties = obj.properties
            properties = sorted(properties)
            pos = 0
            for prop in properties:
                pos += 1
                value = getattr(obj, prop).the
                if prop == nodecentric.RDF_TYPE and value.lexrep == classname:
                    continue
                if self.do_props:
                    self.iri(prop)
                    self.outk("->")
                self.do(value)
                #if self.do_props:
                #   self.outk(")")
                if pos < len(properties):
                    self.out(", ")
            self.outk(")")
            self.indent -= 1
        elif isinstance(obj, nodecentric.DataValue):
            self.do_DataValue(obj)
        else:
            msg = "Don't know how to serialize a "+str(type(obj))+ ": "+repr(obj)
            self.xml_begin("ERROR", {(None, "msg"): msg})
            self.xml_end()
            #raise RuntimeError(msg)

    def xxx_do_StringValue(self, obj):
        self.xml_set_text(obj.lexrep)

    def xxx_do_PlainLiteral(self, obj):
        (text, lang) = obj.lexrep.rsplit("@",1)
        assert lang == ""
        self.xml_set_text(text)

    def do_Sequence(self, obj):
        self.outk("[")
        items = [x for x in obj.items]
        if items:
            self.indent += 1
            self.out()
            self.do(items[0])
            for item in items[1:]:
                self.out(", ")
                self.do(item)
            self.indent -= 1
        self.outk("]")

    def do_DataValue(self, obj):
        self.outk("data(", atom_quote(obj.lexrep), ", ")
        self.iri(obj.datatype)
        self.outk(")")

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
       plugin.Option('do_props', 'Output the names of properties',
                     default=True),
       ]


   def __init__(self, **kwargs):
       self.ser = Serializer(**kwargs)

   def serialize(self, doc, output_stream):
       self.ser.stream = output_stream
       output_stream.write("%\n")
       # output_stream.write(":- op(800,xfx,'->').\n")
       self.ser.do(doc)
       output_stream.write(".\n")
       self.ser.irimap()
       output_stream.write("%\n")
  
