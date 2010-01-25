#!/usr/bin/env python
# -*-mode: python -*-  -*- coding: utf-8 -*-

import sys
import xml.etree.cElementTree as etree
import os

import rdflib 
from rdflib import RDF

import convert_to_rdf
import convert_from_rdf
import xml_in
import error

count = 0

bad = [
    'Named_Argument_Uniterms_non-polymorphic-premise.rif',   # slot <Name>
    'Unordered_Relations-premise.rif',    # slot <Name>
    'OpenLists-premise.rif', # no ordered on args
]
def load(filename):
    parser = xml_in.Plugin()
    try:
        result = parser.parse_file(filename)
    except error.SyntaxError, e:
        print >>sys.stderr, filename+":", e.message
        print >>sys.stderr, e.illustrate_position()
        sys.exit(1)
    return result

def loop(filename):
    inf = open(filename, "r")
    doc = etree.fromstring(inf.read())
    inf.close()

    global count
    tmpfile = "/tmp/convert_rdf_loop_%04d.rdf" % count
    tmpfile2 = "/tmp/convert_rdf_loop_%04d.rif" % count
    count += 1 
    save = sys.stdout
    sys.stdout = open(tmpfile, "w")
    convert_to_rdf.do_document(doc)
    sys.stdout.close()
    sys.stdout = save
    print "Done.   See", tmpfile

    inf = open(tmpfile, "r")
    graph = rdflib.ConjunctiveGraph()
    graph.parse(inf, "application/rdf+xml")
    inf.close()
    docs = graph.subjects(RDF.type, convert_from_rdf.RIF.Document)
    docs = [x for x in docs]
    if len(docs) == 1:
        doc = docs[0]
    else:
        raise RuntimeError
    out = open(tmpfile2, "w")
    convert_from_rdf.to_rif(out, graph, doc, root=True)
    print "Done.  See", tmpfile2
    out.close()

    old = load(filename)
    new = load(tmpfile2)
    print old == new

def main():
    
    for root, dirs, files in os.walk('/home/sandro/5/rules/test/repository/tc'):
        for filename in files:
            if filename.endswith("premise.rif"):
                if filename in bad:
                    continue
                f = root+"/"+filename
                print f
                loop(f)

if __name__ == "__main__":
    main()
