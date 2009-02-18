#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""



 We need some trick for knowing when parens are needed....

"""

import serializer
import plugin
from cStringIO import StringIO

import AST

class Serializer(serializer.General):

    def __init__(self, indent_factor, show_annotations, html):
        super(Serializer, self).__init__(indent_factor=indent_factor)
        self.show_annotations = show_annotations
        self.html = html

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

    #def do_Sequence(self, obj):

    def do_Grammar(self, obj):
        for i in obj.productions:
            self.do(i)
            self.out("\n\n")

    def do_Production(self, obj):
        self.out(obj.name, " : ")
        self.do(obj.expr)


    def do_Seq(self, obj):
        #self.out("(")
        self.do(obj.left)
        self.out(" ")
        self.do(obj.right)
        #self.out(")")

    def do_Alt(self, obj):
        #self.out("(")
        self.do(obj.left)
        self.lend()
        self.out(" | ")
        self.do(obj.right)
        #self.out(")")

    def do_Reference(self, obj):
        self.out(obj.name)

    def do_Precedence(self, obj):
        self.out("(")
        self.do(obj.expr)
        self.out(")")
        self.out(" %prec ", obj.reference)


    def do_Property(self, obj):
        self.out(obj.property)
        self.out("::(")    # how do to parens only when necessary?
        self.do(obj.expr)
        self.out(")")

    def do_Plus(self, obj):
        self.out("(")
        self.do(obj.expr)
        self.out(")")
        self.out("+")

    def do_Optional(self, obj):
        self.out("(")
        self.do(obj.expr)
        self.out(")")
        self.out("?")

    def do_Times(self, obj):
        self.out("(")
        self.do(obj.expr)
        self.out(")")
        self.out("*")

    def do_Literal(self, obj):
        self.out('"', obj.text, '"')    # escaping

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
       self.ser.do(doc)
  
plugin.register(Plugin)

        
