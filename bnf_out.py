#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""



 We need some trick for knowing when parens are needed....

"""

import serializer2
import plugin
from cStringIO import StringIO

from debugtools import debug

import AST2
NS = "http://www.w3.org/2009/02/blindfold/ns#"
AST2.default_namespace = NS

class Serializer(serializer2.General):

    def __init__(self, indent_factor, show_annotations, html):
        super(Serializer, self).__init__(indent_factor=indent_factor)
        self.show_annotations = show_annotations
        self.html = html

    def begin(self, tag,  one_line=False):
        #if not one_line: self.lend(2)
        self.outk(tag+"(")
        self.lend(2)
        self.indent += 1

    def end(self, one_line=False):
        self.indent -= 1
        self.outk(")")
        if not one_line: self.lend(2)

    def do_str(self, obj):
        self.outk(repr(obj))

    #def do_Sequence(self, obj):

    def do_Grammar(self, obj):
        for i in obj.productions.the.items:
            self.do(i)
            self.outk("\n\n")

    def do_Production(self, obj):
        self.outk(obj.name.the.lexrep, " ::= ")
        self.do(obj.expr.the)


    def do_Seq(self, obj):
        #self.outk("(")
        self.do(obj.left.the)
        self.outk(" ")
        self.do(obj.right.the)
        #self.outk(")")

    def do_Alt(self, obj):
        #self.outk("(")
        self.do(obj.left.the)
        self.lend()
        self.outk(" | ")
        self.do(obj.right.the)
        #self.outk(")")

    def do_AltN(self, obj):
        self.indent += 1
        exprs = obj.exprs.values
        for expr in exprs[:-1]:
            self.do(expr)
            self.lend()
            self.outk(" | ")
        self.do(exprs[-1])
        self.indent -= 1

    def do_Reference(self, obj):
        self.outk(obj.name.the.lexrep)

    def do_Precedence(self, obj):
        self.outk("(")
        self.do(obj.expr.the)
        self.outk(")")
        self.outk(" %prec ", obj.reference.the.lexrep)


    def do_Property(self, obj):
        self.outk(obj.property.the)
        self.outk("::(")    # how do to parens only when necessary?
        self.do(obj.expr.the)
        self.outk(")")

    def do_Plus(self, obj):
        self.outk("(")
        self.do(obj.expr.the)
        self.outk(")")
        self.outk("+")

    def do_Optional(self, obj):
        self.outk("(")
        self.do(obj.expr.the)
        self.outk(")")
        self.outk("?")


    def do_Times(self, obj):
        self.outk("(")
        self.do(obj.expr.the)
        self.outk(")")
        self.outk("*")

    def do_Literal(self, obj):
        s = obj.text.the.lexrep
        s = s.replace('"', r'\"')
        self.outk('"', s, '"')

    def default_do(self, obj):

        self.out('**UNKNOWN**', obj.primary_type)
        return
        self.begin(obj.primary_type)
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
                    self.outk(key, '=')
                    self.do(item)
                    self.lend(1)
            elif isinstance(value, AST2.Sequence):
                self.outk(key, '= [')
                for item in value.items:
                    self.do(item)
                self.outk("]")
            else:
                self.outk(key, '=')
                self.do(value)
                self.lend(1)
        self.end()


class Plugin (plugin.OutputPlugin):
   """...."""

   id=__name__

   options = [
       plugin.Option('indent_factor', 'Number of spaces to indent each level',
                     default="4"),

       plugin.Option('html', 'Generate the output as HTML, with links to itself',
                     default="False"),
       plugin.Option('show_annotations', 'Include the semantic (class, property, action) annotations',
                     default="True"),

       ]
 
   def __init__(self, **kwargs):
       # We *could* make the Plugin *be* the Serializer, but that feels a
       # little too confusing for me right this moment.
       self.ser = Serializer(**kwargs)

   def serialize(self, doc, output_stream):
       self.ser.output_stream = output_stream
       debug('bnf_out(', 'running')
       self.ser.do(doc)
       debug('bnf_out)')
  
plugin.register(Plugin)

        
