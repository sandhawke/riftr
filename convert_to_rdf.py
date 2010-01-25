#!/usr/bin/env python
# -*-mode: python -*-  -*- coding: utf-8 -*-
"""

Convert a RIF XML document (from stdin) into a RIF-in-RDF/XML document
(stdout).  Assumes input is schema-valid RIF.  Should work for all
dialects.

By Sandro Hawke, sandro@w3.org, Jan 24 2010.


Copyright © 2010 World Wide Web Consortium, (Massachusetts Institute
of Technology, European Research Consortium for Informatics and
Mathematics, Keio University). All Rights Reserved. This work is
distributed under the W3C® Software License [1] in the hope that it
will be useful, but WITHOUT ANY WARRANTY; without even the implied
warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

[1] http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231

"""

import sys
import xml.etree.cElementTree as etree
from xml.sax.saxutils import quoteattr, escape

indent = "  "

#
# Namespace Handling
# 

rifrdfns = "http://www.w3.org/2007/rifr#"
rifxmlns = "http://www.w3.org/2007/rif#"

class RIFNS (object):
    """
    For conveniences, lets us write rif.foo as shorthand for
    "{"+rifxmlns+"}"+"foo".
    """
    def __getattr__(self, term):
        return "{" + rifxmlns + "}" + term

rif = RIFNS()

def ns_split(term):
    """
    Take apart an ElementTree namespaced name, returning the namespace
    and a localpart.
    """

    (ns, local) = term.split("}")
    assert ns[0] == "{"
    ns = ns[1:]
    return ns, local


def do_element(tree, rif_locals, prefix=""):
    """Recursively traverse the input XML tree, printing
    the resulting RDF/XML."""

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
        attrs += ' rdf:about=%s' % quoteattr(iri)

    print prefix + "<"+local+attrs+">"

    if tree.tag == rif.meta:
        handle_meta(tree)
        # but still process it normally, as well.

    if tree.tag == rif.Var:
        print prefix+indent+"<name>%s</name>" % escape(tree.text)
    elif tree.tag == rif.Const:
        t = tree.get("type")
        if t == 'http://www.w3.org/1999/02/22-rdf-syntax-ns#PlainLiteral':
            (val, lang) = tree.text.rsplit('@', 1)
            if lang == "":
                print prefix+'    <value>%s</value>' % escape(val)
            else:
                print prefix+'    <value xml:lang=%s>%s</value>' % (
                    quoteattr(lang), escape(val) )
        elif t == rifxmlns + "iri":
            print prefix+('    <value rdf:resource=%s />' % 
                          quoteattr(tree.text))
        elif t == rifxmlns + "local":
            print prefix+('    <value rdf:nodeID=%s />' % 
                          quoteattr(nodeid(rif_locals, tree.text)))

        else:
            print prefix+'    <value rdf:datatype=%s>%s</value>' % (
                quoteattr(tree.get("type")),
                escape(tree.text)
                )
    else:
        for child in tree.getchildren():
            do_element(child, rif_locals,prefix+indent)

    print prefix + "</"+local+">"

def handle_meta(tree):
    # queue up any metadata that we can say in RDF to be emitted as
    # rdf...?   Not implemented yet.
    return
                    
def nodeid(rif_locals, label):
    """Return a node-id for the this rif:local, using rif_locals to
    keep track and re-use them."""
    return rif_locals.setdefault(label, "local_%d" % len(rif_locals))

def finish_locals(rif_locals):
    for (key, value) in rif_locals.items():
        print indent+"<Local rdf:nodeID=%s rdfs:label=%s />" % (
            quoteattr(value), 
            quoteattr(key) )

def main():

    doc = etree.fromstring(sys.stdin.read())

    if doc.tag != rif.Document:
        raise Exception, "Root element is not rif:Document"

    print '<rdf:RDF xmlns="%s"' % rifrdfns
    print '         xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"'
    #print '         xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"'
    print '         >'
    rif_locals = {}
    do_element(doc, rif_locals,indent)
    finish_locals(rif_locals)
    print '</rdf:RDF>'


if __name__ == "__main__":
    main()
