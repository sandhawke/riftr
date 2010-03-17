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

import plugins.xml_in_etree
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
    tests = [test for test in tests if test not in blacklist]
    return tests
        
blacklist = set([
    "Builtins_base64Binary",   # doesn't exist any more, but in manifests
    "RDF_Combination_Constant_Equivalence_Graph_Entailment", # also missing
])


bad_xml = [
    #'Named_Argument_Uniterms_non-polymorphic-premise.rif',   # slot <Name>
    #'Unordered_Relations-premise.rif',    # slot <Name>
    #'OpenLists-premise.rif', # no ordered on args
]

def filename(test, suffix):
    return tc_dir+test+"/"+test+suffix

def premise(test):
    return filename(test, "-premise.rif")

def conclusion(test):
    return filename(test, "-conclusion.rif")

def PET_filenames():
    for test in read_list('Type=PositiveEntailmentTest'):
        yield (test, premise(test), conclusion(test))

def Core_PET_filenames():
    core = set(read_list('Dialect=Core'))
    for test in read_list('Type=PositiveEntailmentTest'):
        if test in core:
            yield (test, premise(test), conclusion(test))

def Core_or_BLD_PET_filenames():
    core = set(read_list('Dialect=Core'))
    bld = set(read_list('Dialect=BLD'))
    for test in read_list('Type=PositiveEntailmentTest'):
        if test in core or test in bld:
            yield (test, premise(test), conclusion(test))

def load(filename):
    parser = plugins.xml_in_etree.Plugin()
    with open(filename) as f:
        text = f.read()

    # workaround for bug in current RIF test suite
    text = text.replace("http://example.com/example#",
                        "http://example.org/#")
        
    result = parser.parse(text)

    #note("error parsing %s: %s" % (filename, str(e)))
    #result = ""
        
    #print >>sys.stderr, filename+":", e.message
    #print >>sys.stderr, e.illustrate_position()
    #sys.exit(1)

    return result

def Core_or_BLD_PET_AST():
    for test, prem, conc in Core_or_BLD_PET_filenames():

        if test == "Unordered_Relations":
            # can't parse NAU's
            continue

        try:
            premise_node = load(prem)
            conclusion_node = load(conc)
            yield test, premise_node, conclusion_node
        except error.Error, e:
            error.notify(e)
