#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""


"""

import serializer2
import plugin
import bnf_tools
from cStringIO import StringIO
import AST2

def position_after(big, little):
    l = len(little)
    return big.index(little) + l

class Serializer(serializer2.General):

    def __init__(self, indent_factor=4):
        super(Serializer, self).__init__(indent_factor=indent_factor)
        self.tokens = bnf_tools.TokenSet()

    def default_do(self, obj):
        self.out("ERROR"+`obj`)
        if isinstance(obj, AST2.Multi): 
            raise RuntimeError('unexpected multi')

    def generate_parser(self, root):

        root = self.tokens.ingest(root)
        bnf_tools.convert_to_yacc_form(root)

        tf = open("ply_template.py", "r")
        template = tf.read()
        tf.close()
        cut1 = position_after(template, "# GENERATED LEX CODE BEGINS HERE\n")
        cut2 = position_after(template, "# GENERATED YACC CODE BEGINS HERE\n")

        self.out(template[:cut1])
        self.out(self.tokens.for_lex())
        self.out(getattr(root, "lex_extra", "").the.lexrep)
        self.out(template[cut1:cut2])
        self.do_Grammar(root)
        self.out(getattr(root, "yacc_extra", "").the.lexrep)
        self.out(template[cut2:])
  
    def do_str(self, obj):
        self.outk(repr(obj))

    #def do_Sequence(self, obj):

    def do_Grammar(self, obj):
        for i in obj.productions.the.items:
            self.do(i)
            self.out()


    def do_Production(self, obj):
        self.out()
        if len(obj.branches.the.items) > 1:
            count = 0
            for branch in obj.branches.the.items:
                count += 1
                self.do_branch(branch, obj.name, count)
        else:
            self.do_branch(obj.branches.the.items[0],  obj.name, 0)
        self.out()

    def do_branch(self, obj, name, count):
        if count:
            index = "_%d" % count
        else:
            index = ""
        self.lend()
        self.out("def p_%s%s(t):" % (name.the.lexrep, index))
        self.indent += 1
        self.out("'''%s : " % name.the.lexrep, keep=1)
        self.do(obj)
        self.out(" '''")
        self.out("pass")
        self.indent -= 1


    def do_Seq(self, obj):
        self.do(obj.left.the)
        self.out(" ", keep=0.8)
        self.do(obj.right.the)

    def do_Alt(self, obj):
        #self.out("(")
        self.do(obj.left.the)
        self.lend()
        self.out(" | ", keep=0.6)
        self.do(obj.right.the)
        #self.out(")")

    def do_Reference(self, obj):
        self.outk(obj.name.the.lexrep)

    def do_Precedence(self, obj):
        #self.out("(", keep=0.9)
        self.do(obj.expr.the)
        #self.out(")", keep=0.9)
        self.out(" %prec ", obj.reference.the.lexrep, keep=0.9)


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


    def do_Star(self, obj):
        self.outk("(")
        self.do(obj.expr)
        self.outk(")")
        self.outk("*")

    def do_Literal(self, obj):
        self.outk('"', obj.text, '"')    # escaping



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
       self.ser.stream = output_stream
       self.ser.generate_parser(doc)

plugin.register(Plugin)

        
