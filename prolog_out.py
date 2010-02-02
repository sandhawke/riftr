#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""


Needs some (optional) stuff before it can be serious

   -- iterative deepening
   -- link to a library for handling builtins

sandro@waldron:~/riftr$ time swipl -g '[fp], halt.'
?- tell(pdump), listing(frame), told.

"""

import sys
import serializer2
import plugin
from cStringIO import StringIO
import re
import tempfile
import subprocess

from debugtools import debug
import qname
import AST2
import xml_in
import escape
import query

rifns = xml_in.RIFNS
rif_bif = 'http://www.w3.org/2007/rif-builtin-function#'
rif_bip = 'http://www.w3.org/2007/rif-builtin-predicate#'

class MissingBuiltin (Exception):
    pass

################################################################
#
#  swipl atom quoting
#

safe_atom = re.compile("[a-z][a-zA-Z_0-9]*$")
def atom_quote(s):
    if isinstance(s, unicode):
        s = s.encode('utf-8')
    m = safe_atom.match(s)
    if m is None:
        # it seems like we don't actually need to escape anything else...
        s = "'"+s.replace('\\', '\\\\').replace(r"'", r"\'")+"'"
    return s

def atom_unquote(s):
    if s[0] == "'":
        s = s[1:-1]
        s = s.replace("\'", "'")
        s = s.replace("\\\\", "\\")
    return s

class Serializer(serializer2.General):

    def __init__(self, supress_nsmap=False, **kwargs):
        serializer2.General.__init__(self, **kwargs)
        self.assertional = True
        self.metadata = []
        self.if_keep = ""
        self.in_external = False
        if 'nsmap' in kwargs:
            self.nsmap = kwargs['nsmap']
        else:
            self.nsmap = qname.Map()
            self.nsmap.defaults = [qname.common]
        self.supress_nsmap = supress_nsmap
        self.atom_prefix = ""   # or "riftr_"


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

    def do_IntValue(self, obj):
        self.outk(str(obj.value))

    def do_Const(self, obj):
        value = getattr(obj, rifns+"value").the
        if value.datatype == rifns+"iri":
            self.iri(value.lexrep)
        elif value.datatype == rifns+"local":
            self.local(value.lexrep)
        else:
            self.outk('data(')
            self.outk(atom_quote(value.lexrep))
            self.outk(", ")
            self.iri(value.datatype)
            #  hmmm   what was I thinking with this next line?
            #self.outk(", ", value.serialize_as_type)
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

        if not self.supress_nsmap:
            self.out('\n% This namespace table isnt actually used yet.')
            self.out(':- discontiguous(ns/2).')
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
        
    def do_Document(self, obj):
        self.out("\n% very rough machine-translated Document by riftr\n\n")
        buf = self.str_do(obj.payload.the)
        self.irimap()
        self.flush_metadata()
        self.stream.write(buf)

    def do_Query(self, obj):
        self.out("\n% very rough machine-translated Query by riftr\n\n")
        self.assertional = False
        self.indent += 1
        buf = self.str_do(obj.pattern.the)
        self.indent -= 1

        self.irimap()
        self.flush_metadata()

        self.out("query(Bindings) :-")
        self.indent += 1
        self.outk("Bindings = [")
        try:
            vars = [v for v in obj.selected.the]
        except:
            vars = []
        if len(vars) > 1:
            for v in vars[0:-1]:
                self.do(v)
                self.outk(", ")
        if vars:
            self.do(vars[-1])
        self.out("],")
        self.stream.write(buf)
        self.out(".")

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
            self.out(".\n\n")
        #self.flush_metadata()

    def do_Forall(self, obj):
        # ignore declares
        for formula in obj.formula.values:
            self.do(formula)
            #self.out(".\n\n")

    def do_Implies(self, obj):
        was_assertional = self.assertional
        self.assertional = False
        self.do(obj.then.the)
        self.out(" :- ")
        self.indent += 1
        self.do(getattr(obj, "if").the)
        self.indent -= 1
        self.assertional = was_assertional

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
        try:
            self.handle_builtin_atom(obj)
            return
        except MissingBuiltin:
            pass

        self.do(obj.op.the)
        self.outk("(")
        self.do(obj.args.the)
        self.outk(")")
        

    def handle_builtin_atom(self, obj):
        pred = obj.op.the
        if pred.datatype == rifns+"iri":
            (ns, local) = qname.uri_split(pred.lexrep)
            if ns == rif_bip:
                arg = obj.args.the.items
                method_name = "builtin_"+local.replace("-","_")
                debug('prolog-bi', 'looking for pred ', method_name)
                attr = getattr(self, method_name, None)
                if attr:
                    attr(*arg)
                    return
        raise MissingBuiltin()
                    

    def builtin_calc(self, var, expr):
        func = expr.op.the
        if func.datatype == rifns+"iri":
            (ns, local) = qname.uri_split(func.lexrep)
            if ns == rif_bif:
                arg = expr.args.the.items
                method_name = "builtin_"+local.replace("-","_")
                debug('prolog-bi', 'looking for func ', method_name)
                attr = getattr(self, method_name, None)
                if attr:
                    attr(var, *arg)
                    return
        raise MissingBuiltin()

    def builtin_subtract(self, var, left, right):
        self.do(var)
        self.outk(' is ')
        self.do(left)
        self.outk(' - ')
        self.do(right)

    def builtin_numeric_greater_than(self, left, right):
        self.do(left)
        self.outk(" > ")
        self.do(right)

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
        if op.datatype == rifns+"iri":
            s = "iri_"
        elif op.datatype == rifns+"local":
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
                if self.assertional:
                    self.out(".")                
                else:
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
   """Prolog out (very experimental)."""

   id=__name__

   spec="http://www.w3.org/TR/2008/WD-rif-bld-20080730/#XML_Serialization_Syntax_for_RIF-BLD"

   options = [
       plugin.Option('indent_factor', 'Number of spaces to indent each level',
                     default="4"),
       ]


   def __init__(self, **kwargs):
       self.ser = Serializer(**kwargs)

   def serialize(self, doc, output_stream):
       AST2.default_namespace = rifns
       self.ser.stream = output_stream
       self.ser.do(doc)
  
plugin.register(Plugin)


def read_solutions(stream):
    """
    Read sets of atoms from the stream, one per line, with a blank
    line between each set.
    """
    results = []
    binding = []
    for line in stream:
        line = line.strip()
        if line == "end marker":   # could never appear in data unquoted
            results.append(binding)
            binding = []
        else:
            binding.append(atom_unquote(line))
    return results
            
def run_query(kb, query):
    """assert the document, then query for the pattern, returning
    all the sets of bindings."""

    to_pl = tempfile.NamedTemporaryFile('wb', delete=False)
    from_pl = tempfile.NamedTemporaryFile('rb', delete=False)
    
    print to_pl.name, from_pl.name
    nsmap = qname.Map()
    nsmap.defaults = [qname.common]
    Plugin(nsmap=nsmap, supress_nsmap=True).serialize(kb, to_pl)
    Plugin(nsmap=nsmap).serialize(query, to_pl)
    to_pl.close()
    subprocess.check_call(["swipl", "-g", "[run_query], run_query(%s, %s), halt." %
                          (atom_quote(to_pl.name), atom_quote(from_pl.name))])
    result = read_solutions(from_pl)
    return result

def test():
    import xml_in_etree

    tc = 'Frames'
               
    kb = xml_in_etree.Plugin().parse_file('tc/%s/%s-premise.rif' % (tc, tc))
    conclusion = xml_in_etree.Plugin().parse_file('tc/%s/%s-conclusion.rif' % (tc, tc))
    pattern = query.from_conclusion(conclusion)
                    
    result = run_query(kb, pattern)
    if result:
        n = 1
        for r in result:
            print "Result %d: %s" % (n, r)
            n += 1
    else:
        print "Failed."

if __name__=="__main__":
    test()                    
