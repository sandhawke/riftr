#!/usr/bin/env python
# -*-mode: python -*-  -*- coding: utf-8 -*-
"""

Implements the 22 June 2010 versions of the RIF-in-RDF mapping.

By Sandro Hawke, 16 June 2010.


Copyright © 2010 World Wide Web Consortium, (Massachusetts Institute
of Technology, European Research Consortium for Informatics and
Mathematics, Keio University). All Rights Reserved. This work is
distributed under the W3C® Software License [1] in the hope that it
will be useful, but WITHOUT ANY WARRANTY; without even the implied
warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

[1] http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231

"""

import sys
# http://docs.python.org/library/xml.etree.elementtree.html 
import xml.etree.cElementTree as etree 

rifns = "http://www.w3.org/2007/rif#"
xsdns = "http://www.w3.org/2001/XMLSchema#"

table_3 = {
    ("Document", "directive") : ("directives", 2),
    ("Group", "sentence") : ("parts", 2),
    ("Forall", "declare") : ("univars", 2),
    ("And", "formula") : ("allTrue", 2),
    ("Frame", "slot") : ("slots", 3),
    ("Atom", "slot") : ("namedargs", 3),
    ("Expr", "slot") : ("namedargs", 3),
    ("Atom", "op") : ("predicate", 1),
    ("Expr", "op") : ("function", 1),
}

#
# Classes used to represent RDF.  We could use rdflib or something,
# but we want this to be readable even if you don't know rdflib.
#

class BlankNode(object):

    counter = 0

    def __init__(self, label=None):
        if label:
            self.label = label
        else:
            self.label = "n"+str(BlankNode.counter)
            BlankNode.counter += 1

    def as_turtle(self):
        return "_:"+self.label

    # can we use [...] notation somehow?   That's hard.

class LabeledNode(object):

    def __init__(self, iri):
        self.iri = iri

    def as_turtle(self):
        return "<"+self.iri+">"

class PlainLiteral(object):

    def __init__(self, text, lang=None):
        self.text = text
        self.lang = lang

    def as_turtle(self):
        if self.lang:
            return '"'+turtle_escape(self.text)+'"@'+self.lang
        else:
            return '"'+turtle_escape(self.text)+'"'

class TypedLiteral(object):
    
    def __init__(self, lexrep, datatype):
        self.lexrep = lexrep
        self.datatype = datatype

    def as_turtle(self):
        return '"'+turtle_escape(self.lexrep)+'"^^<'+self.datatype+'>'

class RDFList(object):
    
    def __init__(self, items):
        self.items = items

    def as_turtle(self):
        return " ( "+ " ".join([x.as_turtle() for x in self.items]) + " ) "

#
# General Utility Functions
#

class Namespace(object):
    """
    For conveniences, lets us write rif.foo as shorthand for
    "{"+rifxmlns+"}"+"foo".
    """
    def __init__(self, ns):
        self.ns = ns
    def __getattr__(self, term):
        return "{" + self.ns + "}" + term

def ns_split(term):
    """
    Take apart an ElementTree namespaced name, returning the namespace
    and a localpart.
    """

    (ns, local) = term.split("}")
    assert ns[0] == "{"
    ns = ns[1:]
    return ns, local

def group_children(x):
    """Given an XML element, return a sequence of lists of its
    children, gathered by element tag.  So, for instance, if the
    children are: a b b c c c d, the result would be [a] [b b] [c c c]
    [d].

    Assumes same-tag children are together in the order, but XML
    Schema requires that, so it's a good assumption."""

    buffer = []
    prev = None
    for p in x.getchildren():
        if prev is not None and prev != p.tag:
            yield buffer
            buffer = []
        buffer.append(p)
        prev = p.tag
    yield buffer

def the_child_of(x):
    children = [e for e in x.getchildren()]
    assert(len(children) == 1)
    return children[0]

def contains_markup(x):
    children = [e for e in x.getchildren()]
    assert len(x) == len(children)   # I'm unclear what len dooes
    return len(children) > 0

def turtle_escape(s):
    # http://www.w3.org/TeamSubmission/turtle/#sec-strings
    s = s.replace("\\", "\\\\")
    s = s.replace("\n", "\\n")
    s = s.replace("\t", "\\t")
    s = s.replace("\r", "\\r")
    s = s.replace('"', '\\"')
    return s
    
#
# Parts of describe() that have been moved out into separate functions,
# just for readability.
#

rif = Namespace(rifns)

def get_focus(rifxml):
    # allow an override, eg for the document URI?   Should the document address
    # be the IRI of the document node...?
    id_child = rifxml.find(rif.id)
    if id_child is not None:
        # oddly, the id is required to be a rif:iri.   A rif:local
        # would make a lot of sense, too, for when you want metadata
        # without making up an IRI.
        id_const = id_child.find(rif.Const)
        t = id_const.get("type")
        if t == rifns+"iri":
            iri = id_const.text
            focus = LabeledNode(iri)
        else:
            error("""<id> elements must contain a <Const type="rif:iri"> element""")
    else:
        focus = BlankNode()
    return focus

def extract_meta(rifxml):
    """Optionally for a <meta> element and convert the data in it into
    triples and return them"""
    return []

def error(x, msg):
    print >>sys.stderr, "Error:", msg
    print >>sys.stderr, "Near ", etree.tostring(x)[0:60],"..."
    sys.exit(1)

#
# The main describe() function
#

def describe(rifxml):
    """Given a RIF XML document, or a part of an RIF XML document
    (where the element is a "class stripe"), return the pair <focus,
    triples>) where triples is a set of RDF triples (an RDF graph),
    and focus is the node in that graph which represents the top-level
    element in the provided XML."""

    focus = get_focus(rifxml)
    triples = []
    tag = rifxml.tag
    (ns,local) = ns_split(rifxml.tag)

    triples.extend(extract_meta(rifxml))

    # Table 1 Processing

    if tag == rif.Var:
        triples.append( (focus, rifns+"varname", PlainLiteral(rifxml.text)) )
        return (focus, triples)

    if tag == rif.Const:
        t = rifxml.get("type")
        text = rifxml.text
        if text is None:   # etree does this sometimes (!)
            text = ""

        if t == rifns + "iri":
            new = (focus, rifns+"constIRI", PlainLiteral(text))
        elif t == rifns + "local":
            new = (focus, rifns+"constName", PlainLiteral(text))
        elif t == 'http://www.w3.org/1999/02/22-rdf-syntax-ns#PlainLiteral':
            (val, lang) = text.rsplit('@', 1)
            new = (focus, rifns+"value", PlainLiteral(val, lang)) 
        else:
            new = (focus, rifns+"constName", TypedLiteral(text, t))

        triples.append(new)
        return (focus, triples)

    # Do the basic matching from Table 2
    for group in group_children(rifxml):
        group_tag = group[0].tag
        (group_ns, group_local) = ns_split(group_tag)
        if group_tag == rif.id:
            continue

        # mode 0 -- the child, when present, has the ordered=yes attribute
        # mode 1 -- the child is required to appear exactly once
        # mode 2 -- the child is optional, or it may be repeated
        # mode 3 -- just for the <slot> element

        prop = group_ns+group_local
        if group[0].get("ordered") == "yes":
            mode = 0
        else:
            mode = 1
        if group_ns == rifns:
            try:
                # Table 3 contains over-rides for property names and modes.
                # It's the only way to get Mode 2 or Mode 3
                (prop_suffix, mode) = table_3[ (local, group_local) ]
                if prop_suffix:
                    prop = group_ns+prop_suffix
            except KeyError:
                pass

        #print "   group", group_tag, mode, prop

        if mode == 0: # ORDERED=YES
            if len(group) > 1:
                error("elements with ordered='yes' must not be repeated")
            values=[]
            for child in group[0].getchildren():
                (child_focus, child_triples) = describe(child)
                values.append(child_focus)
                triples.extend(child_triples)
            value = RDFList(values)
        elif mode == 1:  # REQUIRED TO APPEAR EXACTLY ONCE
            if len(group) > 1:
                error(group[0], "only elements in listed as Mode=2 in Table 3 may be repeated")
            if contains_markup(group[0]):
                child = the_child_of(group[0])
                (value, child_triples) = describe(child)
            else:
                # eg <location>
                child_triples = [  (focus, prop, PlainLiteral(group[0].text)) ]
            triples.extend(child_triples)
        elif mode == 2:  # OPTIONAL/REPEATED -- GATHERED INTO A LIST
            values=[]
            for occurance in group:
                if contains_markup(occurance):
                    child = the_child_of(occurance)
                    (child_focus, child_triples) = describe(child)
                else:
                    # eg <profile> [optional, not repeatable]
                    child_focus = PlainLiteral(occurance.text)
                    child_triples = []
                values.append(child_focus)
                triples.extend(child_triples)
            value = RDFList(values)
        elif mode == 3:  # SLOTS -- TRANSFORMED AND GATHERED INTO LIST
            values=[]
            for occurance in group:
                assert occurance.get("ordered") == "yes"
                node = BlankNode()
                values.append(node)

                if tag == rif.Expr or tag == rif.Atom:
                    assert(len(occurance) == 2)
                    assert(occurance[0].tag == rif.Name)
                    name = occurance[0].text
                    (v, vt) = describe(occurance[1])
                    triples.extend(vt)
                    triples.append(  (node, rifns+"argname", PlainLiteral(name))  )
                    triples.append(  (node, rifns+"argvalue", v)  )
                else:
                    # in std dialects, tag == rif.Frame here
                    assert(len(occurance) == 2)
                    (k, kt) = describe(occurance[0])
                    (v, vt) = describe(occurance[1])
                    triples.extend(kt)
                    triples.extend(vt)
                    triples.append(  (node, rifns+"slotkey", k)  )
                    triples.append(  (node, rifns+"slotvalue", v)  )

            value = RDFList(values)
            
        else:
            raise Exception
                
        triples.append(  (focus, prop, value)  )

    return (focus, triples)

#
# Extract
#

def extract(graph, node):
    # ...    what about extra stuff...?
    #  limit to schema...
    raise Exception


#
# Basic command-line driver functions
#

def main():
    doc = etree.fromstring(sys.stdin.read())
    if doc.tag != rif.Document:
        error(doc, "Root element is not rif:Document.")
    (focus, triples) = describe(doc)
    print "# RIF focus is", focus.as_turtle()
    for (s,p,o) in triples:
        print s.as_turtle(), "<"+p+">", o.as_turtle(),"."


if __name__ == "__main__":
    main()
