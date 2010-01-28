#!/usr/bin/env python
# -*-mode: python -*-  -*- coding: utf-8 -*-

import sys
import xml.etree.cElementTree as etree
import os

import rdflib 
from rdflib import RDF

import xml_in
import xml_in_etree
import error

count = 0

bad = [
    #'Named_Argument_Uniterms_non-polymorphic-premise.rif',   # slot <Name>
    #'Unordered_Relations-premise.rif',    # slot <Name>
    #'OpenLists-premise.rif', # no ordered on args
]

good = []

def note(text):
    ff=open("bad-parser", "a")
    ff.write(text)
    ff.write("\n")
    ff.close()

def load(module, filename):
    parser = module.Plugin()
    try:
        result = parser.parse_file(filename)
    except Exception, e:
        note("error parsing %s: %s" % (filename, str(e)))
        result = ""
        
        #print >>sys.stderr, filename+":", e.message
        #print >>sys.stderr, e.illustrate_position()
        #sys.exit(1)
    return result

def loop(filename):
    global count

    count += 1
    old = load(xml_in, filename)
    new = load(xml_in_etree, filename)

    same = (old == new)
    same2 = (new == old)
    assert same == same2
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
                loop(f)

    note('done, %d good' % len(good))
    print "%d good" % len(good)

if __name__ == "__main__":
    main()
