#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""


Needs some (optional) stuff before it can be serious

   -- iterative deepening
   -- link to a library for handling builtins


"""

import sys
import serializer2
import plugin
from cStringIO import StringIO
import re

from debugtools import debug
import qname
import AST2
import xml_in
import escape


safe_atom = re.compile("[a-z][a-zA-Z_0-9]*$")
def atom_quote(s):
    if isinstance(s, unicode):
        s = s.encode('utf-8')
    m = safe_atom.match(s)
    if m is None:
        return "'"+s.replace("'", "\\\'")+"'"
    else:
        return s

class Serializer(serializer2.General):

    def default_do(self, obj):

        if isinstance(obj, AST2.Instance):
            self.out("not_implemented('%s')" % obj.primary_type)
        else:
            self.out("not_implemented('%s')" % str(type(obj)))

    def do_Var(self, obj):
        debug('prolog', 'a Var:', obj)
        self.outk(escape.alnumEscape(obj.name.the.lexrep).capitalize())

        
    #def do_StringValue(self, obj):
    #    self.out(atom_quote(obj.lexrep))

    def do_BaseDataValue(self, obj):
        if obj.datatype == xml_in.RIFNS+"iri":
            self.iri(obj.lexrep)
        elif obj.datatype == xml_in.RIFNS+"local":
            self.local(obj.lexrep)
        else:
            self.outk('data(')
            self.outk(atom_quote(obj.lexrep))
            self.outk(", ")
            self.iri(obj.datatype)
            self.outk(')')

    def iri(self, text):
        (long, local) = qname.uri_split(text)
        short = self.nsmap.getShort(long)
        if short != "rif":
            short = self.atom_prefix+short
        #self.outk(short+":"+atom_quote(local))
        self.outk(atom_quote(short+"_"+local))

    def irimap(self):

        #self.out(":- ensure_loaded(library('semweb/rdf_db')).")
        #for short in self.nsmap.shortNames():
            #self.out(':- rdf_register_ns('+short+', '+atom_quote(self.nsmap.getLong(short)), ").")

        self.out('\n% This namespace table isnt actually used yet.')
        for short in self.nsmap.shortNames():
            self.out('ns('+short+', '+atom_quote(self.nsmap.getLong(short)), ").")
        self.out('\n')

    def local(self, text):
        self.outk(atom_quote(self.atom_prefix+text))

    def do_Sequence(self, obj):
        #self.outk('[')      -- no, this would be a List -- something different
        for item in obj.items[0:-1]:
            self.do(item)
            self.outk(', ')
        self.do(obj.items[-1])
        #self.outk(']')
        
    # strings?   data values?

    def do_Document(self, obj):
        self.out("\n% very rough machine-translated by riftr\n\n")
        self.metadata = []
        self.if_keep = ""
        self.in_external = False
        self.nsmap = qname.Map()
        self.nsmap.defaults = [qname.common]
        self.atom_prefix = ""   # or "riftr_"
        buf = self.str_do(obj.payload.the)
        self.irimap()
        self.flush_metadata()
        self.stream.write(buf)

    def handle_metadata(self, obj):
        '''Show the id/meta for any given object'''
        first = True
        for id in obj.id.values:
            if first:
                self.lend()
                first = False
            self.out('%%rif_id=%s' % id.lexrep)
        for frame in obj.meta.values:
            self.metadata.append(frame)

    def flush_metadata(self):
        #if self.metadata:
        #    self.out("\n% metadata concerning above terms")
        for frame in self.metadata:
            self.out("rif_meta( [ ")
            self.indent += 1
            self.do(frame)
            self.out(" ] ).")
            self.indent -= 1
        self.out()
        self.metadata = []

    def do_Group(self, obj):
        self.out("")
        self.out("%%")
        self.handle_metadata(obj)
        for s in obj.sentence.values:
            self.do(s)
        #self.flush_metadata()

    def do_Forall(self, obj):
        # ignore declares
        for formula in obj.formula.values:
            self.do(formula)
            self.out(".\n\n")

    def do_Implies(self, obj):
        self.do(obj.then.the)
        self.out(" :- ")
        self.indent += 1
        self.do(getattr(obj, "if").the)
        self.indent -= 1

    def do_And(self, obj):
        values = obj.formula.values
        if len(values) == 0:
            self.outk('fail')
        elif len(values) == 1:
            self.do(values[0])
        else:
            self.open_paren(",")
            for formula in values[0:-1]:
                self.do(formula)
                self.out(",")
            self.do(values[-1])
            self.close_paren()

    def open_paren(self, op):
        # some day, this can be smart and leave out parens when the 
        # given operator is higher precedence than any above us here
        # in some stack we keep
        self.outk("(")

    def close_paren(self):
        self.outk(")")
            
    def do_Atom(self, obj):
        self.do(obj.op.the)
        self.outk("(")
        self.do(obj.args.the)
        self.outk(")")

    def do_Equal(self, obj):
        self.open_paren("=")
        self.do(obj.left.the)
        self.outk("=")
        self.do(obj.right.the)
        self.close_paren()

    def do_External(self, obj):
        assert not self.in_external
        self.in_external = True
        self.do(obj.content.the)
        self.in_external = False

    def do_Expr(self, obj):
        self.do(obj.op.the)
        self.outk("(")
        self.do(obj.args.the)
        self.outk(")")

    def op(self, op):
        if op.datatype == xml_in.RIFNS+"iri":
            s = "iri_"
        elif op.datatype == xml_in.RIFNS+"local":
            s = "local_"
        else:
            raise RuntimeError()
        if self.in_external:
            s = "external_"+s
        self.outk(atom_quote(s+op.lexrep))

    def do_Frame(self, obj):
        subj = obj.object.the
        if obj.slot.values:
            for slot in obj.slot.values[:-1]:
                self.single_frame(subj, slot)
                self.out(",")
            self.single_frame(subj, obj.slot.values[-1])

    def single_frame(self, subj, slot):
            p = slot.items[0]
            o = slot.items[1]
            self.outk("frame(")
            self.do(subj)
            self.outk(", ")
            self.do(p)
            self.outk(", ")
            self.do(o)
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
       ]


   def __init__(self, **kwargs):
       self.ser = Serializer(**kwargs)

   def serialize(self, doc, output_stream):
       AST2.default_namespace = xml_in.RIFNS
       self.ser.output_stream = output_stream
       self.ser.do(doc)
  
plugin.register(Plugin)
