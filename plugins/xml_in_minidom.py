#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

Parse the RIF XML Syntax to self.ast

This seems massively complicated; revisit it...???


BUG:  Doesn't handle the current <List> Syntax used in the test
      suite, but that syntax was changed at a recent meeting....
      So...   okay.
      
      mps syntax?

"""

import sys
import xml.dom.minidom
import xml.parsers.expat

from datanode import NodeFactory
import rif
import plugin
import error
import xmlextras as xx

from debugtools import debug
import debugtools
#debugtools.tags.add("ps_out")
#debugtools.tags.add("reconstruct")
#debugtools.tags.add("xml_in")
#debugtools.tags.add("ast2")

RIFNS = u"http://www.w3.org/2007/rif#"

def ns_join(ns, term):
    """ 
    Keep this indirect, in case we want to change how we handle namespaces.
    """

    if not ns:
        return term

    if ns.endswith("#"):
        return ns+term
    else:
        return ns+"#"+term

class Parser:

    def __init__(self, schema, factory=None):
        self.root = None
        self.schema = schema    # we might use the schema...?
        self.ast = factory or NodeFactory()

    def value_of_element(self, node):
        assert node.nodeType == node.ELEMENT_NODE

        ns = node.namespaceURI
        local = node.localName
        debug('xml_in(', "value_of_element", local, 'ns:',ns)

        if (ns == RIFNS and local == u"Const"):
            datatype = node.getAttribute('type')
            lexrep = xx.nodeContents(node)    # this is so wrong.... markup should cause an error!
            
            # WAS:  v = self.ast.DataValue(lexrep, datatype)
            v  = self.ast.Instance(ns_join(ns, local))
            vv = self.ast.DataValue(lexrep, datatype)
            setattr(v, RIFNS+'value', vv)
            
            debug('xml_in)', "It's a data value:", v)
            return v

        if (ns == RIFNS and local == u"Var"):
            name = xx.nodeContents(node)
            v = self.ast.Instance(ns_join(ns, local))
            setattr(v, RIFNS+'name', self.ast.StringValue(name))
            debug('xml_in)', "It's a variable:", v)
            return v

        ins = self.ast.Instance(ns_join(ns, local))
        debug('xml_in', "instance=", str(ins))

        # xml-attributes as property values
        # (not in RIF, per se, but it seems reasonable to do...)
        nnmap = node.attributes
        for i in range(0, nnmap.length):
            xmlattr = nnmap.item(i)
            if xmlattr.prefix == "":
                ns = "" # node.namespaceURI # not typical for XML
            else:
                if xmlattr.prefix and xmlattr.prefix.startswith("xmlns"):
                    # I guess we could/should remember the shortnames?
                    continue 
                ns = xmlattr.namespaceURI
            prop = ns_join(ns, xmlattr.localName)
            debug('xml_in', "attribute:", prop)
            if prop == 'http://www.w3.org/2000/xmlns/#xmlns':
                # I guess we could/should remember the shortnames?
                continue
            setattr(ins, prop, self.ast.StringValue(xmlattr.value))

        # child elements as property values        
        for child in node.childNodes:
            if child.nodeType == child.ELEMENT_NODE:
                prop = ns_join(child.namespaceURI, child.localName)
                debug('xml_in', "property", prop)
                if child.getAttribute("ordered") == "yes":
                    debug('xml_in', 'ordered')
                    s = self.ast.Sequence()
                    for value in self.values_inside_element(child):
                        s.append(value)
                    setattr(ins, prop, s)
                else:
                    for value in self.values_inside_element(child):
                        setattr(ins, prop, value)
 
            elif xx.white(child):
                pass
            else:
                raise RuntimeError("unexpected content: "+node.toxml()+" in "+node.parentNode.toxml())

        debug('xml_in)', 'done reading', ins)
        return ins
        
    def values_inside_element(self, node):

        debug('xml_in(', "getting values inside", node.tagName)
        
        # it's EITHER just text, OR it's a sequence of elements (with whitespace ignored)
        try:
            text = xx.nodeText(node)
            result = self.ast.StringValue(text)
            debug('xml_in', "value_inside:", result)
            yield result
            debug('xml_in)')
            return
        except xx.UnexpectedContent:
            pass
        
        for child in node.childNodes:
            if xx.white(child):
                pass
            elif child.nodeType == child.ELEMENT_NODE:
                result = self.value_of_element(child)
                debug('xml_in', "value_inside:", result)
                yield result
            elif child.nodeType == child.TEXT_NODE:
                # uh oh... multiple non-white text node children???
                # that means there's markup in this, I think.....
                result = self.ast.StringValue(child.data)
                debug('xml_in', 'dubious mixed content', result)
                yield result
            else:
                raise xx.UnexpectedContent

        debug('xml_in)')

class Plugin (plugin.InputPlugin):
   """RIF XML Syntax Input"""

   id=__name__
   spec="http://www.w3.org/TR/2008/WD-rif-bld-20080730/#XML_Serialization_Syntax_for_RIF-BLD"
   
   def parse(self, s):
       p = Parser(rif.bld_schema)
       try:
           p.root = xml.dom.minidom.parseString(s)
       except xml.parsers.expat.ExpatError, e:
           raise error.SyntaxError(e.lineno, e.offset, s, e.message)
       doc = p.value_of_element(p.root.documentElement)
       return doc

plugin.register(Plugin)

if __name__ == "__main__":
    import xml_out

    docnode = Plugin().parse(sys.stdin.read())
    xml_out.Plugin().serialize(docnode, sys.stdout)
    
