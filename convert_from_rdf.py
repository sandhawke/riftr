#!/usr/bin/env python
# -*-mode: python -*-  -*- coding: utf-8 -*-
"""
Convert a RIF-in-RDF document (stdin) to a RIF document (stdout).

Self-standing for now.  Could/should use AST2 and xml_out, maybe?

"""
__version__="unknown"

import sys
import xml.sax.saxutils as saxutils
import rdflib
import rdflib.Namespace
import rdflib.RDF as RDF
import rdflib.RDFS as RDFS
import rdflib.URIRef as URIRef

indent = "  "
rdfns = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
rifrdfns = "http://www.w3.org/2007/rifr#"
rifxmlns = "http://www.w3.org/2007/rif#"

RIF = rdflib.Namespace(rifrdfns)

def main():

    graph = rdflib.ConjunctiveGraph()
    graph.parse(sys.stdin, "application/rdf+xml")

    if len(sys.argv) == 2:
        doc = URIRef(sys.argv[1])
    else:
        docs = graph.subjects(RDF.type, RIF.Document)
        docs = [x for x in docs]  # give us a real array, not a generator
        if len(docs) == 1:
            doc = docs[0]
        elif len(docs) > 1:
            print >>sys.stderr, "Input contains multiple rif:Document nodes"
            print >>sys.stderr, indent+",".join([repr(x) for x in docs])
            print >>sys.stderr, "Name one on the command line  to select it"
            sys.exit(1)
        elif len(docs) < 1:
            print >>sys.stderr, "Input contains to rif:Document nodes"
            sys.exit(1)

    out = sys.stdout
    to_rif(out, graph, doc, root=True)

def localize(node):
    s = str(node)
    if s.startswith(rifrdfns):
        return s[len(rifrdfns):]
    else:
        return "***"+s
    
def irimeta(out, graph, node, prefix, multiline):
    """Output any IRIMETA information"""

    multiline=True
    if isinstance(node, rdflib.URIRef):
        if multiline:
            out.write(prefix+indent)
        out.write("<id><Const type=%s>%s</Const></id>" % (
                saxutils.quoteattr(rifxmlns+"iri"),
                saxutils.escape(unicode(node))
                ))
        if multiline:
            out.write("\n")
    
    meta = graph.value(node, RIF.meta)
    if meta is not None:
        if multiline:
            out.write(prefix+indent)
        else:
            out.write("\n" + prefix+indent)
        out.write("<meta>\n")
        to_rif(out, graph, meta, prefix+indent+indent)
        if multiline:
            out.write(prefix+indent)
        out.write("</meta>")
        if multiline:
            out.write("\n")

def to_rif(out, graph, node, prefix="", root=False):

    cls = graph.value(node, RDF.type)

    if cls == RIF.Var:
        varname = graph.value(node, RIF.name)
        out.write(prefix+"<Var>")
        irimeta(out, graph, node, prefix, True)
        out.write(saxutils.escape(varname)+"</Var>\n")
        return

    if cls == RIF.Const:
        #print "CONST"
        #for s, p, o in graph:
        #    if s == node:
        #        print "PV:   ",p,o
        #        for ss,pp,oo in graph:
        #            if ss == o:
        #                print "          ",pp, oo
        #
        value = graph.value(node, RIF.value)
        #print "VALUE", `value`, value
        #if isinstance(value, rdflib.BNode):
        #    datatype = rifxmlns + "local"
        #    lexrep = graph.value(value, RIF.name)
        #    if lexrep is None:
        #        lexrep = "**MISSING**"
        if isinstance(value, rdflib.URIRef):
            datatype = rifxmlns + "iri"
            lexrep = unicode(value)
        elif isinstance(value, rdflib.Literal):
            if value.datatype is None:
                if value.language is None:
                    lang=""
                else:
                    lang = value.language
                datatype = rdfns + "PlainLiteral"
                lexrep = unicode(value) + "@" + lang
            else:
                datatype = value.datatype
                lexrep = unicode(value)
        else:
            raise RuntimeError, value
        out.write(prefix+"<Const type=%s>" % saxutils.quoteattr(datatype))
        irimeta(out, graph, node, prefix, True)
        out.write(saxutils.escape(lexrep).encode("utf-8"))
        out.write("</Const>\n")
        return

    if cls == RIF.List:
        out.write(prefix+"<List>")
        irimeta(out, graph, node, prefix, True)
        items = graph.value(node, RIF.items)
        for i in graph.items(items):
            to_rif(out, graph, i, prefix+indent)
        out.write("</List>\n")
        return
        
    attrs = ""
    if root:
        attrs += ' xmlns="http://www.w3.org/2007/rif#"'

    out.write(prefix+"<"+localize(cls)+attrs+">\n")
    irimeta(out, graph, node, prefix, False)

    unique_properties = set()
    for x in graph.predicates(node):
        unique_properties.add(x)
    for p in sorted(unique_properties):
        if p == RIF.id or p == RIF.meta: 
            continue
        do_property(out, graph, node, p, prefix+indent)

    out.write(prefix+"</"+localize(cls)+">\n")

def do_property(out, graph, node, p, prefix):

    if p == RDF.type:
        return

    for value in sorted(graph.objects(node, p)):

        if (value == RDF.nil or 
            graph.value(value, RDF.first, None, False, True)):
            out.write(prefix+"<"+localize(p)+' ordered="yes">\n')
            for i in graph.items(value):
                to_rif(out, graph, i, prefix+indent)
            out.write(prefix+"</"+localize(p)+">\n")
        elif isinstance(value, rdflib.Literal):
            # needed for location & profile
            assert value.datatype == None
            assert value.language == None
            out.write(prefix+"<"+localize(p)+">")
            out.write(saxutils.escape(unicode(value)))
            out.write("</"+localize(p)+">\n")
        else:
            out.write(prefix+"<"+localize(p)+">\n")
            to_rif(out, graph, value, prefix+indent)
            out.write("</"+localize(p)+">\n")

if __name__ == "__main__":
    main()
