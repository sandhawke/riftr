#!/usr/bin/env python
# -*-mode: python -*-  -*- coding: utf-8 -*-
"""

Convert a RIF XML document (from stdin) into a RIF-in-RDF/XML document
(stdout).  Assumes input is schema-valid RIF.  Should work for all
dialects.

"""

import sys
import xml.etree.cElementTree as etree
import xml.sax.saxutils as saxutils

#
# Namespace Handling
# 

rifrdfns = "http://www.w3.org/2007/rif#"
rifxmlns = "http://www.w3.org/2007/rif#"

class RIFNS (object):
    def __getattr__(self, term):
        return "{" + rifxmlns + "}" + term

rif = RIFNS()

def ns_split(term):
    (ns, local) = term.split("}")
    assert ns[0] == "{"
    ns = ns[1:]
    return ns, local

#
# Recursively traverse the XML tree, changing it as necessary
# from RIF XML to RIF-in-RDF/XML
#
# This code assumes the RIF input is schema-valid.  No input
# validation is done.
#
def do_element(tree, rif_locals, prefix=""):

    (ns,local) = ns_split(tree.tag)

    attrs = ""

    if tree.tag == rif.id:
        return

    if tree.get("ordered") == "yes":
        attrs += ' rdf:parseType="Collection"'

    id_element = tree.find(rif.id)
    if id_element is not None:
        # oddly, the id is required to be a rif:iri.   A rif:local
        # would make a lot of sense, too, for when you want metadata
        # without making up an IRI.
        iri = id_element.find(rif.Const).text
        attrs += ' rdf:about=%s' % saxutils.quoteattr(iri)

    print prefix + "<"+local+attrs+">"

    if tree.tag == rif.meta:
        handle_meta(tree)
        # but still process it normally, as well.

    if tree.tag == rif.Var:
        print prefix+"    <rdfs:label>%s</rdfs:label>" % saxutils.escape(tree.text)
    elif tree.tag == rif.Const:
        t = tree.get("type")
        # do we need special handling for rif:local or rif:iri, or do we
        # just pretend they are RDF datatypes for this purpose?

        if t == 'http://www.w3.org/1999/02/22-rdf-syntax-ns#PlainLiteral':
            (val, lang) = tree.text.rsplit('@', 1)
            if lang == "":
                print prefix+'    <rdf:value>%s</rdf:value>' % saxutils.escape(val)
            else:
                print prefix+'    <rdf:value xml:lang=%s>%s</rdf:value>' % (
                    saxutils.quoteattr(lang), saxutils.escape(val) )
        elif t == rifxmlns + "iri":
            print prefix+('    <rdf:value rdf:resource=%s />' % 
                          saxutils.quoteattr(tree.text))
        elif t == rifxmlns + "local":
            print prefix+('    <rdf:value rdf:nodeID=%s />' % 
                          saxutils.quoteattr(nodeid(rif_locals, tree.text)))

        else:
            print prefix+'    <rdf:value rdf:datatype=%s>%s</rdf:value>' % (
                saxutils.quoteattr(tree.get("type")),
                saxutils.escape(tree.text)
                )
    else:
        for child in tree.getchildren():
            do_element(child, rif_locals,prefix+"    ")

    print prefix + "</"+local+">"

def handle_meta(tree):
    # queue up any metadata that we can say in RDF to be emitted as
    # rdf
    return
                    
    for frame in tree.findall(rif.Frame):
        obj = frame.find(rif.object)   # node-id for local?
        # ...
        for slot in frame.findall(rif.slot):
            (prop, value) = slot.getchildren()

def nodeid(rif_locals, label):
    """Return a node-id for the this rif:local, using rif_locals to
    keep track and re-use them."""
    return rif_locals.setdefault(label, "local_%d" % len(rif_locals))

def finish_locals(rif_locals):
    for (key, value) in rif_locals.items():
        print "    <Local rdf:nodeID=%s rdfs:label=%s />" % (
            saxutils.quoteattr(value), 
            saxutils.quoteattr(key) )

def main():

    doc = etree.fromstring(sys.stdin.read())

    if doc.tag != rif.Document:
        raise Exception, "Root element is not rif:Document"

    print '<rdf:RDF xmlns="%s"' % rifrdfns
    print '         xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"'
    print '         xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"'
    print '         >'
    rif_locals = {}
    do_element(doc, rif_locals,"    ")
    finish_locals(rif_locals)
    print '</rdf:RDF>'


if __name__ == "__main__":
    main()
