"""

use pattern and AST2 together...
     
"""

import sys

import qname
import pattern
import AST2

from debugtools import debug
import debugtools
#debugtools.tags.add("val")

xsns = "http://www.w3.org/2001/XMLSchema"
rdfns = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
rdfsns = "http://www.w3.org/2000/01/rdf-schema#"


class Checker (object):

   def __init__(self, **kwargs):
      self.nsmap = qname.Map([qname.common])
      self.__dict__.update(kwargs)
      self.good = 0
      self.bad = 0

   def fail(self, path, msg):
      print >>sys.stderr, path, msg
      self.bad += 1

   def name(self, iri):
      return self.nsmap.qname(iri, '_')

   def check(self, node, pat, path=None):

      if path is None:
         path = self.name(pat.iri)

      debug("val(", path, repr(node)[0:20], pat)

      if isinstance(pat, pattern.Class):
         if not isinstance(node, AST2.Instance):
            self.fail(path, "expecting a node (not %s)" %node)
            debug("val)")    
            return
         npat = None
         debug("val(", "checking bloodline")
         for (rank, p) in pat.bloodline():
            debug("val", rank, self.name(p.iri))
            # we should actually be matching on slots, I think, but
            # name is good enough for now....
            if p.iri == node.primary_type:
               npat = p
               debug("val", "that's it!")
               break
         debug("val)")
         if npat is None:
            self.fail(path, "expecting a %s got a %s" %
                      (self.name(pat.iri), self.name(node.primary_type)))
            debug("val)")    
            return
         self.good += 1
         debug("val(", "doing slots", [self.name(x.propertyIRI) for x in npat.slots])
         for slot in npat.slots:
            ppath = path+"."+self.name(slot.propertyIRI)
            cardinality = 0
            for value in getattr(node, slot.propertyIRI).values:
               debug("val", "slot", self.name(slot.propertyIRI),"value", (str(value)+" "*20)[0:20])
               if cardinality > 0:
                  pppath = ppath + ".value%d" % (cardinality+1)
               else:
                  pppath = ppath
               cardinality += 1
               if slot.isList:
                  if not isinstance(value, AST2.Sequence):
                     fail(pppath, "expecting list value")
                     continue
                  posn = 0
                  for item in value.items:
                     self.check(item, slot.valueType, pppath+"[%d]"%posn)
                     posn += 1
               else:
                  self.check(value, slot.valueType, pppath)
            if slot.minCardinality is not None:
               if cardinality < slot.minCardinality:
                  self.fail(ppath, "below minOccur (%d found)" % cardinality)
            if slot.maxCardinality is not None:
               if cardinality > slot.maxCardinality:
                  self.fail(ppath, "above maxOccur (%d found)" % cardinality)
         debug("val)", "done with slots")
      elif isinstance(pat, pattern.Datatype):
         if not isinstance(node, AST2.BaseDataValue):
            self.fail(path, "expecting a data value (not node)")
            debug("val)")    
            return
         debug("val", "it's a data value")
         if not node.value_fits(pat.iri):
            self.fail(path, "wanted %s literal, got %s" %
                      (self.name(pat.iri), node))
            return
         self.good += 1
      else:
         raise RuntimeError("wtf is class?  "+repr(pat))
      debug("val)")    

def test_1():
   import xml_in_etree

   g=pattern.Grammar()
   g.load("absyn_test/books.asn")
   book = g._classes[0]
   #for c in g._classes[0].reachable():
   #   print c
   #with open("/tmp/bld.bnf", "w") as out:
   #pattern.BNF_Writer().serialize(book)

   with open("absyn_test/books_data_1.xml") as bookdata:
      root = xml_in_etree.Plugin().parse(bookdata.read())

   Checker().check(root, book)

def test(xml_file, asn_file):
   import xml_in_etree

   g=pattern.Grammar()
   g.load(asn_file)
   root_pattern = g._classes[0]

   with open(xml_file) as xml_stream:
      root_node = xml_in_etree.Plugin().parse(xml_stream.read())

   with open(",validate.bnf", "w") as out:
      pattern.BNF_Writer(output_stream=out).serialize(root_pattern)

   c = Checker()
   c.nsmap.bind("", "http://www.w3.org/2007/rif#")
   c.check(root_node, root_pattern)
   print c.good,"good nodes", c.bad, "errors"


if __name__ == "__main__":
    import doctest, sys
    doctest.testmod(sys.modules[__name__])
    
    #test_1()
    test('absyn_test/frames.xml', 'absyn_test/bld.asn')


