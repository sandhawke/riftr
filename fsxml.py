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


class Writer (object) :

    def __init__(self, **kwargs):

        self.indent = "  "
        self.ns = "http://www.w3.org/2010/fsxml#"

        self.nsmap = qname.Map()
        self.nsmap.defaults = [qname.common]
        self.nsmap.bind('fx', self.ns)
        
        self.output_stream = None
        self.graph = None
        self.node_count = 0

        self.__dict__.update(kwargs)

    def out(self, text):
        self.output_stream.write(text)

    def serialize(self, graph, out):
        
        self.graph = graph
        self.output_stream = out

        roots = rdf_roots.find_roots(graph)

        attr = self.xmlns_text()

        self.done = {}

        if len(roots) > 1:
            self.out("<%s%s>\n" % (self.qname(self.ns+"Graph"), attr))
            for node in roots:    
                self.to_xml(node, prefix=self.indent)
            self.out("</%s>\n" % self.qname(self.ns+"Graph"))
        else:
            self.to_xml(roots[0], attr_extra=attr)

    def xmlns_text(self):
        """Figure our what xmlns text we need to add to the root element

        """

        has_rdf_type = set()

        # pre-populate the nsmap
        for s,p,o in self.graph:
            if p == RDF.type:
                if s not in has_rdf_type:
                    has_rdf_type.add(s)
                    p = None   # DONT COUNT the firstthe rdf:type arc
            for term in s,p,o:
                if isinstance(term, URIRef):
                    self.curie(term)
                try:
                    dt = term.datatype
                except:
                    continue
                if dt: 
                    self.qname(dt)
        # and build the 
        attrs = []
        for short in self.nsmap.shortNames():
            val = saxutils.quoteattr(self.nsmap.getLong(short))
            if short:
                attrs.append(''' xmlns:%s=%s''' % (short, val))
            else:
                attrs.append(''' xmlns=%s''' % val)
        if attrs:
            return "\n    "+"\n    ".join(attrs)
        else:
            return ""


    def curie(self,node):
        s = unicode(node)
        try:
            return self.nsmap.qname(s)
        except qname.Unsplitable:
            return "<"+s+">"


    def qname(self,node):
        """Use this instead of curie if it's really going into XML as a qname"""
        s = unicode(node)
        return self.nsmap.qname(s)


    def to_xml(self, node, prefix="", attr_extra=""):

        types = [ x for x in self.graph.objects(node, RDF.type) ]
        if len(types) == 0:
            cls = self.ns+"Item"
        elif len(types) == 1:
            cls = types[0]
        else:
            # it'd be good to sort on some clever key, but without
            # that, we still want to be deterministic.
            cls = sorted(types)[0]

        attrs = ""

        if node in self.done:
            print "Returning to node %s, id %s" % (node, self.done[node])
            raise Exception
        id = None
        if isinstance(node, URIRef):
            id = node
        elif isinstance(node, BNode):
            if self.multiple_inbound(node):
                id = "_:n%04"+str(self.node_count)
                self.node_count += 1
        if id:
            id = saxutils.quoteattr(self.curie(id))
            self.done[node] = id
            attrs += ' %s=%s' % (self.qname(self.ns+"id"), id)

        attrs += attr_extra

        self.out(prefix+"<"+self.qname(cls)+attrs+">\n")


        unique_POs = set()
        for x in self.graph.predicate_objects(node):
            if x == (RDF.type, cls):
                continue
            unique_POs.add(x)
        for p,o in sorted(unique_POs):
            self.do_property(node, p, o, prefix+self.indent)

        self.out(prefix+"</"+self.qname(cls)+">\n")

    def multiple_inbound(self, node):
        count = 0
        for s in self.graph.subject_predicates(node):
            count += 1
            if count >= 2:
                return True
        return False

    def one_in_none_out(self, node):
        count = 0
        for x in self.graph.subject_predicates(node):
            count += 1
            if count >= 2:
                return False
        if count == 0:
            return False
        for x in self.graph.predicate_objects(node):
            return False
        return True

    def need_li(self, items):
        """Do we need an <li> wrapper for the items in this list?

        """
        if len(items) == 1:
            return True #  singleton list needs to be wrapped

        previous_was_bare = False
        for value in items:
            if value in self.done:  
                return True #  <li ref="...." />
            if self.multiple_inbound(value):
                return True # MIGHT become "self.done" during earlier items
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

    def do_property(self, node, p, value, prefix):

        if (value == RDF.nil or 
            self.graph.value(value, RDF.first, None, False, True)):
            items = [ x for x in self.graph.items(value) ]

            self.out(prefix+"<"+self.qname(p)+'>\n')
            if self.need_li(items): 
                for i in items:
                    self.do_property(None, self.ns+"li", i, prefix+self.indent)
            else:
                for i in items:
                    self.to_xml(i, prefix+self.indent)
            self.out(prefix+"</"+self.qname(p)+">\n")
        elif isinstance(value, rdflib.Literal):
            if value.datatype:
                self.out(prefix+"<"+self.qname(p)+">")
                self.out("<"+self.qname(value.datatype)+">")
                self.out(saxutils.escape(unicode(value)).encode('utf-8'))
                self.out("</"+self.qname(value.datatype)+">")
                self.out("</"+self.qname(p)+">\n")
            else:
                if value.language:
                    lang_attr = " xml:lang="+saxutils.quoteattr(value.language)
                else:
                    lang_attr = ""
                self.out(prefix+"<"+self.qname(p)+lang_attr+">")
                self.out(saxutils.escape(unicode(value)).encode('utf-8'))
                self.out("</"+self.qname(p)+">\n")
        else:

            if value in self.done:
                ref = self.done[value]
            elif isinstance(value, URIRef) and self.one_in_none_out(value):
                ref = saxutils.quoteattr(self.curie(value))
            else:
                ref = None

            if ref:
                self.out(prefix+"<"+self.qname(p)+" ref="+ref+" />\n")
            else:
                self.out(prefix+"<"+self.qname(p)+">\n")
                self.to_xml(value, prefix+self.indent)
                self.out(prefix+"</"+self.qname(p)+">\n")


if __name__ == "__main__":
    graph = rdflib.ConjunctiveGraph()
    graph.parse(sys.stdin, "application/rdf+xml")
    w = Writer()
    w.serialize(graph, sys.stdout)

