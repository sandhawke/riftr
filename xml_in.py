#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

Parse the RIF XML Syntax to AST2


"""

import sys
import xml.dom.minidom
import xml.parsers.expat

import AST2
import rif
import plugin
import error
import xmlextras as xx

from debugtools import debug
import debugtools
#debugtools.tags.add("ps_out")
#debugtools.tags.add("reconstruct")
debugtools.tags.add("xml_in")
debugtools.tags.add("ast2")

RIFNS = u"http://www.w3.org/2007/rif#"

def ns_join(ns, term):
    """ 
    Keep this indirect, in case we want to change how we handle namespaces.
    """

    if ns.endswith("#"):
        return ns+term
    else:
        return ns+"#"+term

class Parser:

    def __init__(self, schema):
        self.root = None
        self.schema = schema    # we might use the schema...?

    def value_of_element(self, node):
        assert node.nodeType == node.ELEMENT_NODE

        ns = node.namespaceURI
        local = node.localName
        debug('xml_in(', "value of a", `local`, `ns`)

        if (ns == RIFNS and local == u"Const"):
            datatype = node.getAttribute('type')
            lexrep = xx.nodeContents(node)    # this is so wrong.... markup should cause an error!
            v = AST2.DataValue(lexrep, datatype)
            debug('xml_in)', "It's a data value: ", v)
            return v

        if (ns == RIFNS and local == u"Var"):
            name = xx.nodeContents(node)
            v = AST2.Instance(ns_join(ns, local))
            getattr(v, ns_join(RIFNS, 'name')).add(name)
            return v

        ins = AST2.Instance(ns_join(ns, local))
        debug('xml_in', "instance:", ins)
        
        for child in node.childNodes:
            if child.nodeType == child.ELEMENT_NODE:
                
                ordered=False

                # xml-attributes as property values
                nnmap = node.attributes
                for i in range(0, nnmap.length):
                    xmlattr = nnmap.item(i)
                    if (xmlattr.prefix == "" and xmlattr.localName == "ordered"):
                        if xmlattr.value == "yes":
                            ordered=True
                            debug('xml_in', "ordered")
                    else:
                        if xmlattr.prefix == "":
                            ns = child.namespaceURI # not typical for XML
                        else:
                            ns = xmlattr.namespaceURI
                        prop = ns_join(ns, xmlattr.localName)
                        debug('xml_in', "attribute:", prop)
                        getattr(ins, prop).add(AST2.string(xmlattr.value))

                # child elements as property values
                prop = ns_join(child.namespaceURI, child.localName)
                debug('xml_in', "property", prop)
                if ordered:
                    s = AST2.Sequence()
                    for value in self.values_inside_element(child):
                        s.append(value)
                    getattr(ins, prop).add(s)
                else:
                    for value in self.values_inside_element(child):
                        getattr(ins, prop).add(value)
 
            elif xx.white(child):
                pass
            else:
                raise RuntimeError("unexpected content")

        debug('xml_in)')
        return ins
        
    def values_inside_element(self, node):
        
        # it's EITHER just text, OR it's a sequence of elements (with whitespace ignored)
        try:
            text = xx.nodeText(node)
            yield AST2.string(text)
            return
        except xx.UnexpectedContent:
            pass
        
        for child in node.childNodes:
            if xx.white(child):
                pass
            elif child.nodeType == child.ELEMENT_NODE:
                yield self.value_of_element(child)
            else:
                raise xx.UnexpectedContent


class Plugin (plugin.InputPlugin):
   """RIF XML Syntax Input"""

   id=__name__
   spec="http://www.w3.org/TR/2008/WD-rif-bld-20080730/#XML_Serialization_Syntax_for_RIF-BLD"
   
   def parse(self, s):
       p = Parser(rif.bld_schema)
       try:
           p.root = xml.dom.minidom.parseString(s)
       except xml.parsers.expat.ExpatError, e:
           raise error.SyntaxError(e.lineno, e.offset, str, e.message)
       doc = p.value_of_element(p.root.documentElement)
       return doc

plugin.register(Plugin)

if __name__ == "__main__":
    
    import sys

    s = sys.stdin.read()
    p = Parser(rif.bld_schema)
    p.root = xml.dom.minidom.parseString(s)
    doc = p.value_of_element(p.root.documentElement)
    print doc

