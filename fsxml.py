#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

A serialization of RDF graphs that's particularly elegant for graphs
of the sort we get from mapping RIF to an RDF graph:

    - tree structured, from one root, or at least reachable from 
      some root
      (otherwise we need an fs:Document wrapper)
    - exactly one rdf:type per instance
      (otherwise we need explicit rdf:type arcs)
    - lists have 0,2,3... items, no adjacent plain literals, no
      per-item, xml:lank, no access by reference
      (otherwise they need <li>


Basic rules:

    * start with a root instance (node); the tag is the class name
    * for each triple with that node as the subject, emit one
      child element, tag is property name
      ...



[ code starting with convert_from_rdf.py ]


"""
__version__="unknown"

import sys
import xml.sax.saxutils as saxutils

import rdflib
import rdflib.Namespace
import rdflib.RDF as RDF
import rdflib.RDFS as RDFS
import rdflib.URIRef as URIRef
import rdflib.BNode as BNode

import rdf_roots
import qname


#class Writer (object) :

#    def __init__

indent = "  "
rdfns = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"

rifrdfns = "http://www.w3.org/2007/rifr#"
rifxmlns = "http://www.w3.org/2007/rif#"
fxns = "http://www.w3.org/2010/fsxml#"
fxli = fxns+"li"
fxid = fxns+"id"

nsmap = qname.Map()
nsmap.defaults = [qname.common]
nsmap.bind('fx', fxns)



def main():

    graph = rdflib.ConjunctiveGraph()
    graph.parse(sys.stdin, "application/rdf+xml")

    if len(sys.argv) == 2:
        roots = [ URIRef(sys.argv[1]) ]
    else:
        roots = rdf_roots.find_roots(graph)

    attr = xmlns_text(graph)

    out = sys.stdout
    done = {}
    if len(roots) > 1:
        out.write("<%s%s>\n" % (localize(fxns+"Graph"), attr))   # needs xmlns stuff, of course
        for node in roots:    
            to_xml(out, graph, node, done, prefix=indent)
        out.write("</%s>\n" % localize(fxns+"Graph"))
    else:
        to_xml(out, graph, roots[0], done, attr_extra=attr)

def xmlns_text(graph):
    """Figure our what xmlns text we need to add to the root element

    """

    has_rdf_type = set()

    # pre-populate the nsmap
    for s,p,o in graph:
        if p == RDF.type:
            if s not in has_rdf_type:
                has_rdf_type.add(s)
                p = None   # DONT COUNT the firstthe rdf:type arc
        for term in s,p,o:
            if isinstance(term, URIRef):
                localize(term)
            try:
                dt = term.datatype
            except:
                continue
            localize(dt)
    # and build the 
    attrs = []
    for short in nsmap.shortNames():
        val = saxutils.quoteattr(nsmap.getLong(short))
        if short:
            attrs.append(''' xmlns:%s=%s''' % (short, val))
        else:
            attrs.append(''' xmlns=%s''' % val)
    if attrs:
        return "\n    "+"\n    ".join(attrs)
    else:
        return ""


def localize(node):
    """ Temp Hack version of qname handling...
    """
    
    s = unicode(node)
    try:
        return nsmap.qname(s)
    except qname.Unsplitable:
        # uuuuuh, not allowed in some contexts....  CATCH THAT.   (BUG)
        return "<"+s+">"
    
node_count = 0
def to_xml(out, graph, node, done, prefix="", attr_extra=""):

    types = [ x for x in graph.objects(node, RDF.type) ]
    if len(types) == 0:
        cls = fxns+"Item"
    elif len(types) == 1:
        cls = types[0]
    else:
        # it'd be good to sort on some clever key, but without
        # that, we still want to be deterministic.
        cls = sorted(types)[0]

    attrs = ""

    if node in done:
        print "Returning to node %s, id %s" % (node, done[node])
        raise Exception
    id = None
    if isinstance(node, URIRef):
        id = node
    elif isinstance(node, BNode):
        if multiple_inbound(node, graph):
            id = "_:n%04"+str(node_count)
            node_count += 1
    if id:
        id = saxutils.quoteattr(localize(id))
        done[node] = id
        attrs += ' %s=%s' % (localize(fxid), id)
            
    attrs += attr_extra

    out.write(prefix+"<"+localize(cls)+attrs+">\n")
    

    unique_POs = set()
    for x in graph.predicate_objects(node):
        if x == (RDF.type, cls):
            continue
        unique_POs.add(x)
    for p,o in sorted(unique_POs):
        do_property(out, graph, node, p, o, done, prefix+indent)

    out.write(prefix+"</"+localize(cls)+">\n")

def multiple_inbound(node, graph):
    count = 0
    for s in graph.subject_predicates(node):
        count += 1
        if count >= 2:
            return True
    return False

def one_in_none_out(node, graph):
    count = 0
    for x in graph.subject_predicates(node):
        count += 1
        if count >= 2:
            return False
    if count == 0:
        return False
    for x in graph.predicate_objects(node):
        return False
    return True

def need_li(items, done, graph):
    """Do we need an <li> wrapper for the items in this list?

    """
    if len(items) == 1:
        return True #  singleton list needs to be wrapped

    previous_was_bare = False
    for value in items:
        if value in done:  
            return True #  <li ref="...." />
        if multiple_inbound(value, graph):
            return True # MIGHT become "done" during earlier items
        if isinstance(value, rdflib.Literal):
            if value.language:
                return True  #  <li xml:lang>...</li>
            if not value.datatype:
                if previous_was_bare:
                    return True # <li>hello</li><li>world</li>
                previous_was_bare = True
                continue
        previous_was_bare = False
    return False

def do_property(out, graph, node, p, value, done, prefix):

    if (value == RDF.nil or 
        graph.value(value, RDF.first, None, False, True)):
        items = [ x for x in graph.items(value) ]

        out.write(prefix+"<"+localize(p)+'>\n')
        if need_li(items, done, graph): 
            for i in items:
                do_property(out, graph, None, fxli, i, done, prefix+indent)
        else:
            for i in items:
                to_xml(out, graph, i, done, prefix+indent)
        out.write(prefix+"</"+localize(p)+">\n")
    elif isinstance(value, rdflib.Literal):
        if value.datatype:
            out.write(prefix+"<"+localize(p)+">")
            out.write("<"+localize(value.datatype)+">")
            out.write(saxutils.escape(unicode(value)).encode('utf-8'))
            out.write("</"+localize(value.datatype)+">")
            out.write("</"+localize(p)+">\n")
        else:
            if value.language:
                lang_attr = " xml:lang="+saxutils.quoteattr(value.language)
            else:
                lang_attr = ""
            out.write(prefix+"<"+localize(p)+lang_attr+">")
            out.write(saxutils.escape(unicode(value)).encode('utf-8'))
            out.write("</"+localize(p)+">\n")
    else:

        if value in done:
            ref = done[value]
        elif isinstance(value, URIRef) and one_in_none_out(value, graph):
            ref = saxutils.quoteattr(localize(value))
        else:
            ref = None

        if ref:
            out.write(prefix+"<"+localize(p)+" ref="+ref+" />\n")
        else:
            out.write(prefix+"<"+localize(p)+">\n")
            to_xml(out, graph, value, done, prefix+indent)
            out.write(prefix+"</"+localize(p)+">\n")


if __name__ == "__main__":
    main()
