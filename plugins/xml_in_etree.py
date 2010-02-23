#!/usr/bin/env python
# -*-mode: python -*-  -*- coding: utf-8 -*-
"""

By Sandro Hawke, sandro@w3.org, Jan 28 2010.

TODO: formalize syntax errors    cf xx.UnexpectedContent

"""

import sys
import xml.etree.cElementTree as etree
import xml.parsers.expat

import datanode
import plugin
import error

from xmlns import RIF, split, iri_from_tag

rifrdfns = "http://www.w3.org/2007/rifr#"
rifxmlns = "http://www.w3.org/2007/rif#"

class Parser (object):

    def __init__(self):
        self.ast = datanode.NodeFactory()
        self.ast.nsmap.bind("", rifxmlns)

    # The XML syntax for RIF is "striped": as you recurse into the
    # element, the tags are name-of-class, name-of-property, name-of-class,
    # name-of-property, etc.   So this is implemented as recursion
    # back and forth between decode_instance and decode_property.

    def decode_instance(self, element):
        """Given an xml element which represents an instance of a
        syntactic element (such as <Document> or <Atom> or <Var>),
        return an datanode.Instance with the same data.
        """
        instance = self.ast.Instance(iri_from_tag(element.tag))

        if element.tag == RIF.List:
            # rif:List just directly contains more instances; we treat it
            # as if it had an implicit inner element:  <items ordered="yes">
            #
            # and yes, it is forbidden from having <id> or <meta> (!!?!)
            instance.items = self.ast.Sequence()
            text = element.text or ""
            for child in element.getchildren():
                assert_white(text)
                text = child.tail or ""
                instance.items.the.append(self.decode_instance(child))
            assert_white(text)
            return instance
        
        text = element.text or ""
        for child in element.getchildren():
            assert_white(text)
            text = child.tail or ""
            self.decode_property(child, instance)

        if element.tag == RIF.Var:
            instance.name = self.ast.PlainLiteral(text+"@")
        elif element.tag == RIF.Const:
            instance.value = self.ast.DataValue(text, element.get("type"))
        else:
            assert_white(text)

        return instance

    def decode_property(self, element, instance):
        """Given an xml element which represents a property (such as
        <id> or <declare> or <op>, and an self.ast.Instance, set the
        appropriate property value on that instance.
        """

        children = [x for x in element.getchildren()]
        if children or element.get("ordered") == "yes":
            assert_white(element.text)
            values = []
            for child in element.getchildren():
                assert_white(child.tail)
                values.append(self.decode_instance(child))

            if element.get("ordered") == "yes":
                value = self.ast.Sequence(values)
            else:
                if len(values) == 1:
                    value = values[0]
                else:
                    raise RuntimeError, "Multiple instances inside a property"
        else:
            value = self.ast.PlainLiteral(element.text+"@")

        prop = iri_from_tag(element.tag)
        getattr(instance, prop).add(value)


def assert_white(text):
    if text is not None and text.strip() != "":
        raise RuntimeError, "unexpected character content: %s" % repr(text)

class Plugin (plugin.InputPlugin):
   """RIF XML Syntax Input (etree version)"""

   id=__name__
   spec="http://www.w3.org/TR/rif-bld#XML_Serialization_Syntax_for_RIF-BLD"
   
   def parse(self, s):
       p = Parser()
       try:
           root = etree.fromstring(s)
       except xml.parsers.expat.ExpatError, e:
           raise error.SyntaxError(e.lineno, e.offset, s, e.message)
       doc = p.decode_instance(root)
       return doc

plugin.register(Plugin)

if __name__ == "__main__":
    import xml_out

    docnode = Plugin().parse(sys.stdin.read())
    xml_out.Plugin().serialize(docnode, sys.stdout)
    
