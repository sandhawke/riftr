#!/usr/bin/env python
# -*-mode: python -*-  -*- coding: utf-8 -*-
"""


"""

import sys


import datanode
import plugin
import error

from xmlns import RIF, split, iri_from_tag

rifxmlns = "http://www.w3.org/2007/rif#"

class Parser (object):

    def __init__(self):
        self.ast = datanode.NodeFactory()
        self.ast.nsmap.bind("", rifxmlns)

    def parse(self, source):
        graph = ConjunctiveGraph()
        graph.parse(source, format='n3')
        for s, p, o in graph:
            
            if unicode(p) == LOG+implies:
                raise RuntimeError
            elif unicode(p) == OWL+sameAs:
                raise RuntimeError
            else:
                add a frame to some group....

                (using rif7 or rif10 encoding?)


class Plugin (plugin.InputPlugin):
   """Notation3 (n3) Rules

   """

   id=__name__
   spec="http://www.w3.org/TR/rif-bld#XML_Serialization_Syntax_for_RIF-BLD"
   
   def parse(self, string):
       p = Parser()
       tree =  p.parse(StringIO(string))
       return tree

plugin.register(Plugin)

if __name__ == "__main__":
    import xml_out
    from rdflib.Graph import QuotedGraph
    from rdflib.Graph import ConjunctiveGraph as C
    c = C().parse('anna.n3', format='n3')
    for s,p,o in c:
        print 
        print "s", s, type(s), isinstance(s, QuotedGraph)
        if isinstance(s, QuotedGraph):
            for ss,pp,oo in s:
                print "    ss", ss, type(ss)
                print "    pp", pp, type(pp)
                print "    oo", oo, type(oo)
        print "p", p, type(p)
        print "o", o, type(o)
        if isinstance(o, QuotedGraph):
            for t in o:
                print "    ", t

    #docnode = Plugin().parse(sys.stdin.read())
    #xml_out.Plugin().serialize(docnode, sys.stdout)
    
