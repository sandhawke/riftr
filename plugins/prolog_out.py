#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""


Needs some (optional) stuff before it can be serious

   -- iterative deepening


"""

import sys
from cStringIO import StringIO
import re
import tempfile
import subprocess

from debugtools import debug
import qname

import nodecentric
import datanode
import nodewriter
import plugin
import xml_in
import escape
import query
import test_cases
import error
import func_to_pred

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

class Serializer(nodewriter.General):

    def __init__(self, supress_nsmap=False, **kwargs):
        nodewriter.General.__init__(self, **kwargs)
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

        if isinstance(obj, nodecentric.Instance):
            error.notify(error.NotImplemented("Not Implemented: "
                                              +obj.rdf_type.any.as_string))
            self.out("not_implemented('%s')" % obj.rdf_type.any.as_string)
        else:
            error.notify(error.NotImplemented("Not Implemented (obj): "+
                                              str(type(obj))))
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
        try:
            (long, local) = qname.uri_split(text)
        except qname.Unsplitable:
            long = ""
            local = text
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
            # self.out(':- discontiguous(ns/2).')
            for short in self.nsmap.shortNames():
                self.out('ns('+atom_quote(short)+', '+atom_quote(self.nsmap.getLong(short)), ").")
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
        for v in obj.directive.values:
            self.do(v)
        if obj.payload.values:
            self.do(obj.payload.the)
        self.irimap()
        self.flush_metadata()

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
        self.assertional = True
        self.do(obj.then.the)
        self.out(" :- ")
        self.indent += 1
        self.assertional = False
        self.do(getattr(obj, "if").the)
        self.indent -= 1
        self.assertional = was_assertional

    def do_And(self, obj):
        values = obj.rif_formula.values_list
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
        # surprisingly, the <args> is optional in the XML Schema
        if obj.args.values_list:
            self.outk("(")
            self.do(obj.args.the)
            self.outk(")")

    def handle_builtin_atom(self, obj):
        pred = obj.op.the.value.the
        if pred.datatype == rifns+"iri":
            (ns, local) = qname.uri_split(pred.lexrep)
            if ns == rif_bip:
                arg = obj.args.the.items
                method_name = "builtin_"+local.replace("-","_")
                debug('prolog-bi', 'looking for pred ', method_name)
                attr = getattr(self, method_name, None)
                if attr:
                    attr(*arg)
                else:
                    self.outk(method_name)
                    self.outk("(")
                    self.do(obj.args.the)
                    self.outk(")")
                return
        raise MissingBuiltin  # it's not builtin

    def builtin_calc(self, var, expr):
        # not currently used...
        func = expr.op.the.value.the
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
        raise MissingBuiltin  # it's not builtin...

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
        # assert not self.in_external
        #     externals CAN be nested, as in Builtins_Numeric
        # External(pred:is-literal-short(External(xs:short("1"^^xs:string))))
        self.in_external = True
        self.do(obj.content.the)
        self.in_external = False

    def do_Expr(self, obj):
        op = obj.op.the.value.the
        if op.datatype == rifns+"iri":
            (ns, local) = qname.uri_split(op.lexrep)
            if ns == rif_bif:
                name = "builtin_"+local.replace("-","_")
                self.outk(name)
            else:
                self.do(op)
        else:
            self.do(op)

        self.outk("(")
        self.do(obj.args.the)
        self.outk(")")

    def op(self, op):
        if op.datatype == rifns+"iri":
            s = "iri_"
        elif op.datatype == rifns+"local":
            s = "local_"
        else:
            notify(error.Structural('op is neither rif:local nor rif:iri'))
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

    def do_List(self, obj):
        self.outk('[') 
        items = obj.items.the.items
        for item in items[:-1]:
            self.do(item)
            self.outk(', ')
        self.do(items[-1])
        self.outk(']')

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
       # nodecentric.default_namespace = rifns
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
    if binding:
        error.notify(error.SyntaxErrorFromSubprocess('no end marker'))
    return results
            
def run_query(kb, query, msg):
    """assert the document, then query for the pattern, returning
    all the sets of bindings."""

    to_pl = tempfile.NamedTemporaryFile('wb', dir="testing_tmp", delete=False)
    from_pl = tempfile.NamedTemporaryFile('rb', dir="testing_tmp", delete=False)
    
    debug('prolog', to_pl.name, from_pl.name)
    global filenames
    filenames = (to_pl.name, from_pl.name)

    nsmap = qname.Map()
    nsmap.defaults = [qname.common]
    nsmap.bind("", "http://www.w3.org/2007/rif#")

    to_pl.write("% "+msg)
    ast = datanode.NodeFactory()
    rifeval = ast.Instance('rif_Const')
    rifeval.rif_value = ast.DataValue(rif_bip+'eval', rifns+'iri')
    kb_pform = func_to_pred.Plugin(calc_pred=rifeval,factory=kb.factory).transform(kb)
    query_pform = func_to_pred.Plugin(calc_pred=rifeval).transform(query)
    Plugin(nsmap=nsmap, supress_nsmap=True).serialize(kb_pform, to_pl)
    Plugin(nsmap=nsmap).serialize(query_pform, to_pl)
    to_pl.close()
    popen = subprocess.Popen(
        ["swipl", "-q", "-g", "[builtins], run_query(%s, %s), halt." %
         (atom_quote(to_pl.name), atom_quote(from_pl.name))
         ],
        bufsize=0, # unbuffered for now at least
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True)

    # to start reading this safely....?
    # popen.stdout.setblocking(False)

    (stdoutdata, stderrdata) = popen.communicate()
    if stdoutdata: 
        # since this doesn't seem to ever happen, I guess we can
        # use this for the results feed
        error.notify(error.UnexpectedOutputFromSubprocess(
                     "\n===stdout===\n"+stdoutdata+"=========="))
    if stderrdata:
        error.notify(error.UnexpectedOutputFromSubprocess(
                     "\n===stderr===\n"+stderrdata+"=========="))
    if popen.returncode != 0:
        error.notify(error.ErrorReturnFromSubprocess("Return code: "+
                                                     str(popen.returncode)))
    result = read_solutions(from_pl)
    return result

def test():
    import xml_in_etree

    tc = 'Frames'
               
    kb = xml_in_etree.Plugin().parse_file('tc/%s/%s-premise.rif' % (tc, tc))
    conclusion = xml_in_etree.Plugin().parse_file('tc/%s/%s-conclusion.rif' % (tc, tc))
    pattern = query.from_conclusion(conclusion)
                    
    result = run_query(kb, pattern)
    pass_count = 0
    fail_count = 0
    if result:
        n = 1
        for r in result:
            print "Result %d: %s" % (n, r)
            n += 1
        pass_count += 1
    else:
        print "Failed."
        fail_count += 1

def test2():
    
    error.sink = sys.stdout

    pass_count = 0
    fail_count = 0
    n=1
    for test, prem, conc in test_cases.Core_PET_AST():

        print '\n\n\n\n\nTest %d: %s' % (n, test)
        n+=1
        pattern = query.from_conclusion(conc)

        #prem.factory.nsmap.bind("", "http://www.w3.org/2007/rif#")
        try:
            result = run_query(prem, pattern, msg="From test "+test)
        except error.Error, e:
            error.notify(e)
            continue 

        if result:
            n = 1
            for r in result:
                print "Result %d: %s" % (n, r)
                n += 1
            print "PASSED"
            pass_count += 1
        else:
            global filenames
            print "Failed.   Files are:\n  %s\n  %s" % filenames
            fail_count += 1

    print "\n\nPassed %d of %d (failed %d).\n" % (pass_count, n-1, fail_count)

class SysTestPlugin (plugin.Plugin):
   """Run the RIF Test Suite through the prolog subsystem."""

   id="run_prolog_tests"

   options = [
       ]


   def __init__(self, **kwargs):
       pass

   def system_test(self):
       test2()
       # should return true if passed
  
plugin.register(SysTestPlugin)

if __name__=="__main__":
    test2()                    
