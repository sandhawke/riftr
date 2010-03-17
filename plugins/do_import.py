#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

Rewrite a tree with Import statements into one that
just includes the imported stuff.   For each profile,
include the necessary additional rulesets?


 -- ONLY does rdf-profile imports of TURTLE documents (dumb)
 -- Should factor out the RDF-to-Frames and Merge bits.

"""

from rdflib import ConjunctiveGraph, BNode, URIRef, Literal, RDF

import plugin

from debugtools import debug
import nodecentric
import qname
from datanode import NodeFactory

rifns = qname.common.rif
rdfns = qname.common.rdf

class RDFLibParseError (Exception):
   pass

class Plugin (plugin.TransformPlugin):
   """Rewrite to perform imports
   """

   id=__name__
   options = [ ]

   def __init__(self, **kwargs):
      pass

   def transform(self, instance):
      self.ast = NodeFactory()
      self.ast.nsmap.bind("", "http://www.w3.org/2007/rif#")
      self.graph = ConjunctiveGraph()
      self.profiles = set()
      self.bmap = {}

      doc = self.ast.deepcopy(instance)

      did_import = False
      for d in doc.directive.values:
         if d.has_type("Import"):
            print "IMPORT"
            print "   location: ", d.location.the.as_string
            print "   profile: ", d.profile.the.as_string
            try:
               self.graph.parse(d.location.the.as_string, format="n3")
            except Exception, e:
               raise RDFLibParseError(e)
            self.profiles.add(d.profile.the.as_string)
            did_import = True
         
      if not did_import:
         return instance

      print "  imported %d triples" % len(self.graph)

      # assume zero or one payloads
      try:
         topgroup = doc.payload.the
      except:
         topgroup = self.ast.Instance("Group")
         doc.payload = topgroup

      # add more 'sentence' properties to topgroup
      for s, p, o in self.graph:
         for ss in self.rif_terms(s):
            for pp in self.rif_terms(p):
               for oo in self.rif_terms(o):
                  f = self.ast.Instance("Frame")
                  f.object=ss
                  f.slot = self.ast.Sequence( [pp, oo] )
                  topgroup._addpv("sentence", f)

      #for profile in profiles:
      #   ...

      return doc

   def rif_terms(self, node):
      """Yield the one or [in special cases] more RIF terms which
      correspond to this RDF graph node."""

      # Literals
      if isinstance(node, Literal):
         if node.datatype is None:
            if node.language is None:
               lang=""
            else:
               lang = node.language
            datatype = rdfns + "PlainLiteral"
            lexrep = unicode(node) + "@" + lang
         else:
            datatype = node.datatype
            lexrep = unicode(node)
         result = self.ast.Instance("Const")
         result.value = self.ast.DataValue(lexrep, datatype)
         yield result
         return

      # Lists
      did_lists = False
      for l in self.list_readings(node):
         did_lists = True
         items = [ self.rif_term(i) for i in l ]
         yield self.ast.Sequence(items=items)
      if did_lists:
         return

      # Blank Nodes
      if isinstance(node, BNode):
         try:
            lexrep = self.bmap[node]
         except KeyError:
            lexrep = "node"+str(len(self.bmap))
            self.bmap[node] = lexrep
         datatype = rifns + "local"
         result = self.ast.Instance("Const")
         result.value = self.ast.DataValue(lexrep, datatype)
         yield result
         return

      # URIRef
      if isinstance(node, URIRef):
         result = self.ast.Instance("Const")
         datatype = rifns + "iri"
         lexrep = unicode(node)
         result.value = self.ast.DataValue(lexrep, datatype)
         yield result
         return

      raise RuntimeError("unexpected type rdflib node: "+`node`)

   def list_readings(self, node):
      """Yield all possible list-readings of this node, as per 
      RIF RDF and OWL Compatibility."""
      if node == RDF.nil:
         yield ()
      else:
         for first in self.graph.objects(node, RDF.first):
            for rest in self.graph.objects(node, RDF.rest):
               for rest2 in self.list_readings(rest):
                  yield (first,) + rest2


class SysTestPlugin (plugin.Plugin):
   ""

   id="run_import_tests"

   options = [    ]


   def __init__(self, **kwargs):
       pass

   def system_test(self):
       test()
       # should return true if passed
  
def test():

   import test_cases
   import plugins.xml_out

   for test in test_cases.read_list("ImportSupport=RIF-RDF_Combination"):
      if test in ("YoungParentDiscount_2", ):
         continue
      prem = test_cases.premise(test)
      conc = test_cases.conclusion(test)
      print test

      try:
         prem_tree = test_cases.load(prem)
      except:
         print "  ... can't load premise; skipping"
         continue

      p = Plugin()
      out = p.transform(prem_tree)
      
      # do something with: out
      plugins.xml_out.do(out)

if __name__=="__main__":
   test()
