"""

use pattern and AST2 together...
     
"""

import sys

import qname
import pattern
import AST2

xsns = "http://www.w3.org/2001/XMLSchema"
rdfns = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
rdfsns = "http://www.w3.org/2000/01/rdf-schema#"


class Checker (object):

   def __init__(self, **kwargs):
      self.nsmap = qname.Map([qname.common])
      self.__dict__.update(kwargs)

   def fail(self, path, msg):
      print >>sys.stderr, path, msg

   def name(self, iri):
      return self.nsmap.qname(iri, '_')

   def check(self, node, pat, path=None):
      
      if path is None:
         path = self.name(pat.iri)
      
      if isinstance(pat, pattern.Class):
         if not isinstance(node, AST2.Instance):
            self.fail(path, "expecting a node (note data value)")
         for slot in pat.slots:
            ppath = path+"."+self.name(slot.propertyIRI)
            cardinality = 0
            for value in getattr(node, slot.propertyIRI).values:
               if cardinality > 0:
                  pppath = ppath + ".val(%d)" % cardinality
               else:
                  pppath = ppath
               cardinality += 1
               if slot.isList:
                  if not isintance(value, AST2.Sequence):
                     fail(pppath, "expecting list value")
                  posn = 0
                  for item in value:
                     self.check(item, slot.valueType, pppath+"[%d]"%posn)
                     posn += 1
               else:
                  self.check(value, slot.valueType, pppath)
            if slot.minCardinality is not None:
               if cardinality < slot.minCardinality:
                  self.fail(ppath, "below minCardinality")
            if slot.maxCardinality is not None:
               if cardinality > slot.maxCardinality:
                  self.fail(ppath, "above maxOccurs")

         for s in pat.allSuperclasses():
            node.type = s.iri
            # maybe pick the lowest non-abstract one as the Primary?
            # maybe make this part optional?
            #  [ it's a bit like the PSVI, changing the AST2 in 
            #    validating it. ]

      elif isinstance(pat, pattern.Datatype):
         if not isinstance(node, AST2.BaseDataValue):
            self.fail(path, "expecting a data value (not node)")
         if not node.value_fits(pat.iri):
            self.fail(path, "wanted %s literal, got %s" %
                      (self.name(pat.iri), node))
      else:
         raise RuntimeError("wtf is class?  "+repr(pat))
      

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

if __name__ == "__main__":
    import doctest, sys
    doctest.testmod(sys.modules[__name__])
    
    test_1()


