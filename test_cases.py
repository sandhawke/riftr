#!/usr/bin/env python
# -*-mode: python -*-  -*- coding: utf-8 -*-
"""

Support for running against the RIF test cases (and maybe other
test cases)

  ./results
  ./test-reporting
  ./repistory/rx/
  classification
  classifications
  bld/
  Core/
"""


import sys
import xml.etree.cElementTree as etree
import os

import rdflib 
from rdflib import RDF

import xml_in
import xml_in_etree
import xml_out
import error

test_dir = '/home/sandro/5/rules/test/'
class_dir = test_dir+'classification/'
tc_dir = test_dir+'repository/tc/'

def read_list(code):
    """

    >>> print read_list('Type=NegativeSyntaxTest')
    ['Core_NonSafeness', 'Core_NonSafeness_2', 'No_free_variables']


    """
    with open(class_dir+code+".txt") as f:
        tests = [line.strip() for line in f.readlines()]
    return tests
        
bad_xml = [
    #'Named_Argument_Uniterms_non-polymorphic-premise.rif',   # slot <Name>
    #'Unordered_Relations-premise.rif',    # slot <Name>
    #'OpenLists-premise.rif', # no ordered on args
]


def PET_filenames():
    for test in read_list('Type=PositiveEntailmentTest'):
        yield (test, 
               tc_dir+test+"/"+test+"-premise.rif",
               tc_dir+test+"/"+test+"-conclusion.rif")

def load(filename):
    parser = xml_in_etree.Plugin()
    result = parser.parse_file(filename)

    #note("error parsing %s: %s" % (filename, str(e)))
    #result = ""
        
    #print >>sys.stderr, filename+":", e.message
    #print >>sys.stderr, e.illustrate_position()
    #sys.exit(1)

    return result

def PET_AST():
    for test, prem, conc in PET_filenames():
        try:
            premise_node = load(prem)
            conclusion_node = load(conc)
            yield test, premise_node, conclusion_node
        except:
            print >>sys.stderr, 'error loading XML for test', test

