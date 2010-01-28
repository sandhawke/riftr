#!/usr/bin/env python
# -*-mode: python -*-  -*- coding: utf-8 -*-

import sys
import xml.etree.cElementTree as etree
import os

import rdflib 
from rdflib import RDF

#import convert_to_rdf
import xml_in_etree
import convert_from_rdf
import rdfxml_out
#import xml_in
import error

count = 0

bad = [
    'Named_Argument_Uniterms_non-polymorphic-premise.rif',   # slot <Name>
    'Unordered_Relations-premise.rif',    # slot <Name>
    'OpenLists-premise.rif', # no ordered on args
]

good = []

def note(text):
    ff=open("bad-loops-2", "a")
    ff.write(text)
    ff.write("\n")
    ff.close()

def load(filename):
    parser = xml_in_etree.Plugin()
    try:
        result = parser.parse_file(filename)
    except Exception, e:
        note("error parsing %s: %s" % (filename, str(e)))
        result = None
        
        #print >>sys.stderr, filename+":", e.message
        #print >>sys.stderr, e.illustrate_position()
        #sys.exit(1)
    return result

def loop(filename):
    #inf = open(filename, "r")
    #doc = etree.fromstring(inf.read())
    #inf.close()


    global count
    tmpfile = "/tmp/convert_rdf_loop_%04d.rdf" % count
    tmpfile2 = "/tmp/convert_rdf_loop_%04d.rif" % count
    count += 1 
    f1 = open(tmpfile, "w")
    doc = load(filename)
    rdfxml_out.Plugin().serialize(doc, f1)
    f1.close()
    print "Done.   See", tmpfile

    inf = open(tmpfile, "r")
    graph = rdflib.ConjunctiveGraph()
    try:
        graph.parse(inf, "application/rdf+xml")
    except Exception, e:
        note("error parsing %s: %s" % (filename, str(e)))
        
    inf.close()
    docs = graph.subjects(RDF.type, convert_from_rdf.RIF.Document)
    docs = [x for x in docs]
    if len(docs) == 1:
        doc = docs[0]
    else:
        raise RuntimeError, "Found %d rifr:Documents in graph" % len(docs)
    out = open(tmpfile2, "w")
    convert_from_rdf.to_rif(out, graph, doc, root=True)
    print "Done.  See", tmpfile2
    out.close()

    old = load(filename)
    new = load(tmpfile2)
    same = (old == new)
    same2 = (new == old)
    assert same == same2
    print same
    if same:
        good.append(filename)
        print "%3d. good: %s" % (count-1, filename.rsplit("/",1)[1])
    else:
        note("%s %d" % (filename, count-1))
        print "%3d. bad:  %s" % (count-1, filename.rsplit("/",1)[1])

def main():

    note('')             
    note('restart')             
    
    for root, dirs, files in os.walk('/home/sandro/5/rules/test/repository/tc'):
        for filename in files:
            if filename.endswith("premise.rif"):
                if filename in bad:
                    continue
                f = root+"/"+filename
                print f
                loop(f)

    note('done, %d good' % len(good))
    print "%d good" % len(good)

if __name__ == "__main__":
    main()
