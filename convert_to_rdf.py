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

def utf8(s):
    if isinstance(s, unicode):
        return s.encode('utf-8')
    else:
        return s

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


def do_element(tree, prefix=""):
    """Recursively traverse the input XML tree, printing
    the resulting RDF/XML."""

    (ns,local) = ns_split(tree.tag)

    attrs = ""

    if tree.tag == rif.id:
        return

    if tree.get("ordered") == "yes":
        attrs += ' rdf:parseType="Collection"'
    else:
        # Workaround syntax error in the current test suite
        if tree.tag == rif.slot :
            attrs += ' rdf:parseType="Collection"'

    id_element = tree.find(rif.id)
    if id_element is not None:
        # oddly, the id is required to be a rif:iri.   A rif:local
        # would make a lot of sense, too, for when you want metadata
        # without making up an IRI.
        iri = id_element.find(rif.Const).text
        attrs += ' rdf:about=%s' % quoteattr(iri)

    if tree.tag == rif.location:
        print prefix + "<location>%s</location>" % utf8(escape(tree.text))
        return

    if tree.tag == rif.profile:
        print prefix + "<profile>%s</profile>" % utf8(escape(tree.text))
        return

    # @@@ what about Lists ?

    print prefix + "<"+local+attrs+">"

    if tree.tag == rif.meta:
        handle_meta(tree)
        # but still process it normally, as well.

    if tree.tag == rif.Var:
        print prefix+indent+"<name>%s</name>" % utf8(escape(tree.text))
        # @@@ what about the metadata?
    elif tree.tag == rif.Const:
        t = tree.get("type")
        text = tree.text
        if text is None:   # etree does this?!
            text = ""
        if t == 'http://www.w3.org/1999/02/22-rdf-syntax-ns#PlainLiteral':
            (val, lang) = text.rsplit('@', 1)
            if lang == "":
                print prefix+'    <value>%s</value>' % utf8(escape(val))
            else:
                print prefix+'    <value xml:lang=%s>%s</value>' % (
                    utf8(quoteattr(lang)), utf8(escape(val)) )
        elif t == rifxmlns + "iri":
            print prefix+('    <value rdf:resource=%s />' % 
                          utf8(quoteattr(text)))
        elif t == rifxmlns + "local":
            print prefix+('    <value><Local><name>%s</name></Local></value>' % 
                          utf8(escape(text)))
        else:
            print prefix+'    <value rdf:datatype=%s>%s</value>' % (
                utf8(quoteattr(tree.get("type"))),
                utf8(escape(text))
                )
    else:
        for child in tree.getchildren():
            do_element(child, prefix+indent)

    print prefix + "</"+local+">"

def handle_meta(tree):
    # queue up any metadata that we can say in RDF to be emitted as
    # rdf...?   Not implemented yet.
    return
                    

def do_document(doc):
    print '<rdf:RDF xmlns="%s"' % rifrdfns
    print '         xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"'
    print '         >'
    do_element(doc, indent)
    print '</rdf:RDF>'

def main():
    doc = etree.fromstring(sys.stdin.read())
    if doc.tag != rif.Document:
        raise RuntimeError, "Root element is not rif:Document"
    do_document(doc)

if __name__ == "__main__":
    main()
