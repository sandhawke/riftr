#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""


"""

import serializer
import plugin
import bnf_tools
from cStringIO import StringIO

import AST

class Serializer(serializer.General):

    def __init__(self, indent_factor):
        super(Serializer, self).__init__(indent_factor=indent_factor)

    def do_str(self, obj):
        self.out(repr(obj))

    #def do_Sequence(self, obj):

    def do_Grammar(self, obj):
        for i in obj.productions:
            self.do(i)
            self.out("\n\n")

    def do_Production(self, obj):
        self.out("\n")
        if len(obj.branches):
            count = 0
            for branch in obj.branches:
                count += 1
                self.do_branch(branch, obj.name, count)
        else:
            self.do_branch(branch)
        self.out("\n")

    def do_branch(self, obj, name, count):
        if count:
            index = "_%d" % count
        else:
            index = ""
        expr = self.str_do(obj)
        self.out("def p_%s%s(t):\n   '''%s : %s '''\n" % (
                name, index, name, expr
                ))
        self.out("   pass\n")


    def do_Seq(self, obj):
        self.do(obj.left)
        self.out(" ")
        self.do(obj.right)

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


    def do_Star(self, obj):
        self.out("(")
        self.do(obj.expr)
        self.out(")")
        self.out("*")

    def do_Literal(self, obj):
        self.out('"', obj.text, '"')    # escaping


class Plugin (plugin.OutputPlugin):
   """Generate the PLY-compatible Python code for parsing the given grammar.
   """

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
       assert doc is not None
       toks = bnf_tools.TokenSet()
       doc = toks.ingest(doc)
       output_stream.write("\n#stuff for lex\n\n")
       output_stream.write(toks.for_lex())
       output_stream.write("\n\n#stuff for yacc\n\n")
       bnf_tools.convert_to_yacc_form(doc)
       self.ser.do(doc)
  

plugin.register(Plugin)

        
