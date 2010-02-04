#!/usr/bin/env python
# -*-mode: python -*-  -*- coding: utf-8 -*-
"""

Tools for working with XML (and sometimes RDF) namespaces.

"""

def split(term):
    if term[0] == "{":
        (ns, local) = term.split("}")
        ns = ns[1:]
    else:
        (ns, local) = term.split("#")
    return ns, local

def iri_from_tag(tag):
    (ns, local) = split(tag)
    if ns.endswith("/") or ns.endswith("#"):
        return ns+local
    else:
        return ns+"#"+local

class XML_Namespace (object):

    def __init__(self, name):
        self.name = name

    def __getattr__(self, local):
        return "{"+self.name+"}"+local

RIF  = XML_Namespace("http://www.w3.org/2007/rif#")

# do we want to return a string, or a rdflib.URIRef?
# but I don't think we want to depend on rdflib here.
# RIFR = RDF_Namespace("http://www.w3.org/2007/rifr#")

