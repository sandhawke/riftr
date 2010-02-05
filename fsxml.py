#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

Implements "Fully-Striped XML", another XML format for RDF Graphs.

The main advantage: it looks a lot normal XML, if one is being
explicit about all the class and role names.  In some documents
nothing from the fsxml namespace is needed.

The idea was that this would be a good XML serialization of RDF Graphs
describing RIF documents.  Unfortunately, it's a little late to be
proposing such things.

The basic structure is alternating Class and Property names, as one
goes deeper into the XML tree, with the leaves being either RDF plain
literals or datatyped values, serialized as strings wrapped in an
element whose tag is the datatype name.   For example:

<foaf:PersonalProfileDocument fx:id="data:"
     xmlns:foaf="http://xmlns.com/foaf/0.1/"
     xmlns="http://www.w3.org/People/Sandro/data#"
     xmlns:fx="http://www.w3.org/2010/fsxml#"
     xmlns:dc="http://purl.org/dc/elements/1.1/"
     xmlns:xs="http://www.w3.org/2001/XMLSchema#"
     xmlns:data="http://www.w3.org/People/Sandro/data#">
    <dc:title>Sandro's (Mostly-Professional) Profile Document</dc:title>
    <foaf:age><xs:decimal>44</xs:decimal></foaf:age>
    <foaf:maker fx:ref="Sandro_Hawke" />
    <foaf:primaryTopic fx:ref="Sandro_Hawke" />
</foaf:PersonalProfileDocument>

The elements in the fsxml (fx) namespace which are sometimes needed are:

   fx:Graph  -- a wrapper, for use when the graph has no node which can
                reach all the other nodes.

   fx:Item   -- a placeholder (like rdf:Description) for when
                no rdf:type is known

                Note: for items with more than one rdf:type, one will
                be used as the element tag and the others will appear
                as rdf:type properties.

   fx:id     -- a curie-valued attribute for stating a uri or nodeID
                for a node (like rdf:nodeID and rdf:about, but a curie)
                
                Currently a "qname" or "<uri>", but may change to a
                real curie.

   fx:ref    -- a curie-valued attribute for linking to nodes (like
                rdf:Resource)

                Currently a "qname" or "<uri>", but may change to a
                real curie.

   fx:li --     a wrapper for the elements in an rdf:List; may be omitted
                by writer in some cases where no ambiguity is created,
                such as when there are two or more items in the list,
                and certain conditions are met by any text items.
                
                Note: an empty list is serialized as a reference to
                rdf:Empty.

 ? fx:text  --  a virtual datatype for plain literals; probably never needed.

A variant on this, called "Stripe-Skipped XML" is possible, equivalent
to parseType="Resource", for use when most rdf:type information is
absent.  the id just goes on the parent (property) element, as a ref.
How is this signalled, for readers to know how to decode it?
Actually, how are they each signaled?  Do we need an attribute?  The
stripe-skipping code is less mature... in particular, it's probably
broken around lists.


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

        self.indent = "    "
        self.ns = "http://www.w3.org/2010/fsxml#"

        self.nsmap = qname.Map()
        self.nsmap.defaults = [qname.common]
        self.nsmap.bind('fx', self.ns)
        
        self.output_stream = None
        self.graph = None
        self.node_count = 0

        self.skip_types = False

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

        (rats, we're duplicating some xml machinery in serializer2.)
        """

        has_rdf_type = set()
        short_count = {}

        # pre-populate the nsmap
        for s,p,o in self.graph:
            if p == RDF.type:
                if s not in has_rdf_type:
                    has_rdf_type.add(s)
                    p = None   # DONT COUNT the firstthe rdf:type arc
            for term in s,p,o:
                if isinstance(term, URIRef):
                    c = self.curie(term)
                    short = c.split(":")[0]
                    try:
                        short_count[short] += 1
                    except:
                        short_count[short] = 1
                try:
                    dt = term.datatype
                except:
                    continue
                if dt: 
                    self.qname(dt)

        if short_count:
            (count, best_short) = sorted(
               [(count, short) for (short, count) in short_count.items()]
               )[-1]
            self.nsmap.bind('', self.nsmap.getLong(best_short))
  
        # and build the xmlns string
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
            # BUG ... actually, we CAN still split it well enough for CURIE.
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
        id = self.id(node)
        if id:
            id = saxutils.quoteattr(self.curie(id))
            self.done[node] = id
            attrs += ' %s=%s' % (self.qname(self.ns+"id"), id)

        attrs += attr_extra

        if attr_extra or not self.skip_types:
            self.out(prefix+"<"+self.qname(cls)+attrs+">\n")

        unique_POs = set()
        for x in self.graph.predicate_objects(node):
            if x == (RDF.type, cls):
                continue
            unique_POs.add(x)
        for p,o in sorted(unique_POs):
            self.do_property(node, p, o, prefix+self.indent)

        if not self.skip_types:
            self.out(prefix+"</"+self.qname(cls)+">\n")

    def multiple_inbound(self, node):
        count = 0
        for s in self.graph.subject_predicates(node):
            count += 1
            if count >= 2:
                return True
        return False

    def none_output(self, node):
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
            elif isinstance(value, URIRef) and self.none_output(value):
                ref = saxutils.quoteattr(self.curie(value))
            else:
                ref = None


            if ref:
                self.out(prefix+"<"+self.qname(p)+" "+
                         self.qname(self.ns+"ref")+"="+ref+" />\n")
            else:
                child_id = self.id(value)
                if self.skip_types and child_id:
                    # do ref AND value
                    ref = saxutils.quoteattr(self.curie(child_id))
                    self.out(prefix+"<"+self.qname(p)+" "+
                             self.qname(self.ns+"ref")+"="+ref+" />\n")
                    self.to_xml(value, prefix+self.indent)
                    self.out(prefix+"</"+self.qname(p)+">\n")
                else:
                    self.out(prefix+"<"+self.qname(p)+">\n")
                    self.to_xml(value, prefix+self.indent)
                    self.out(prefix+"</"+self.qname(p)+">\n")

    def id(self, node):
        if isinstance(node, URIRef):
            return unicode(node)
        elif isinstance(node, BNode):
            if self.multiple_inbound(node):
                self.node_count += 1
                return "_:n%04"+str(self.node_count)
        return None

if __name__ == "__main__":
    graph = rdflib.ConjunctiveGraph()
    graph.parse(sys.stdin, "application/rdf+xml")
    w = Writer(skip_types=True)
    w.serialize(graph, sys.stdout)

