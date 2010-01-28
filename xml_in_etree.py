#!/usr/bin/env python
# -*-mode: python -*-  -*- coding: utf-8 -*-
"""

By Sandro Hawke, sandro@w3.org, Jan 28 2010.

TODO: formalize syntax errors    cf xx.UnexpectedContent

"""

import sys
import xml.etree.cElementTree as etree

import AST2
import plugin

from xmlns import RIF, split, iri_from_tag

rifrdfns = "http://www.w3.org/2007/rifr#"
rifxmlns = "http://www.w3.org/2007/rif#"

AST2.default_namespace = rifxmlns


class Parser (object):

    # The XML syntax for RIF is "striped": as you recurse into the
    # element, the tags are name-of-class, name-of-property, name-of-class,
    # name-of-property, etc.   So this is implemented as recursion
    # back and forth between decode_instance and decode_property.

    def decode_instance(self, element):
        """
        ...
        """
        instance = AST2.Instance(iri_from_tag(element.tag))

        # even Var and Const need this, since they can contain <meta>
        # elements.    @@@ need RIF Approved test case for this

        text = element.text or ""
        for child in element.getchildren():
            assert_white(text)
            text = child.tail or ""
            self.decode_property(child, instance)

        if element.tag == RIF.Var:
            instance.name = AST2.StringValue(text)
        elif element.tag == RIF.Const:
            # We can't just USE the value as the Const, since it can
            # have metadata, and out DataValues (quite reasonably)
            # cannot.

            # We could just do instance.lexrep and instance.type, but
            # we'd like some tools working with the AST to have easy access
            # to the python versions, I think...
            instance.value = AST2.DataValue(text, element.get("type"))
        else:
            assert_white(text)

        return instance

    def decode_property(self, element, instance):
        """Called for each child element of an instance to glean what
        it can from that instance to set properties of the instance
        as necessary."""

        children = [x for x in element.getchildren()]
        if children or element.get("ordered") == "yes":
            assert_white(element.text)
            values = []
            for child in element.getchildren():
                assert_white(child.tail)
                values.append(self.decode_instance(child))

            if element.get("ordered") == "yes":
                value = AST2.Sequence(values)
            else:
                if len(values) == 1:
                    value = values[0]
                else:
                    raise RuntimeError, "Multiple instances inside a property"
        else:
            value = AST2.PlainLiteral(element.text+"@")

        prop = iri_from_tag(element.tag)
        setattr(instance, prop, value)


def assert_white(text):
    if text is not None and text.strip() != "":
        raise RuntimeError, "unexpected character content"

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
    
