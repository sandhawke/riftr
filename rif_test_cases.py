#!/usr/bin/env python2.5
#      -*-mode: python -*-    -*- coding: utf-8 -*-

"""



"""
__version__="unknown"


import rdflib

import mps_in.py

wiki = 'http://tablegate.org/RDFLink?SubjectLink=http%3A//www.w3.org/2005/rules/wiki/'
tcf = 'http://tablegate.org/RDFLink?SubjectLink=http%3A//www.w3.org/2005/rules/wiki/Test_Case_Format#'
rdfs = "http://www.w3.org/2000/01/rdf-schema#"

def pull(graph, subject, label):
    return str(graph.value(subject, rdflib.URIRef(tcf+label)))

class Test_Case (object):

    def extract_self(self, graph, subject):
        self.dialect = pull(graph, subject, "Dialect")
        self.label =   str(graph.value(subject, rdflib.URIRef(rdfs+"label")))

        n = graph.value(subject, rdflib.URIRef(tcf+"Premise"))
        self.premise = MultiDoc()
        self.premise.extract_self(graph, n)

        n = graph.value(subject, rdflib.URIRef(tcf+"Conclusion"))
        self.conclusion = MultiDoc()
        self.conclusion.extract_self(graph, n)

class MultiDoc (object):

    def extract_self(self, graph, subject):
        self.ps = str(graph.value(subject, rdflib.URIRef(tcf+"Presentation_Syntax")))

    def __repr__(self):
        return "PS="+`self.ps`

test_cases = {}

def load():

    graph = rdflib.ConjunctiveGraph()
    
    graph.load('/home/sandro/spry-var-www/src/all_test_cases.rdf')

    
    for (s,p,o) in graph:
        if str(p) == tcf+"Test_Type":
            t = Test_Case()
            assert str(o).startswith(wiki)
            t.type = str(o)[len(wiki):]
            t.extract_self(graph, s)
            test_cases{t.label} = t

def to_xml(t):

    


