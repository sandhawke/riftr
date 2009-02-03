#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

http://docs.python.org/library/xml.etree.elementtree.html

"""

import sys
import xml.etree.cElementTree as ET
import inspect

import rif

import webdata

from debugtools import debug
import debugtools
debugtools.tags.add("inspect")
debugtools.tags.add("reconstruct")
debugtools.tags.add("xml_in")

class Parser:

    def __init__(self):
        self.root = None
        self.view = webdata.View()
        self.view.scanAllModules()

    def instance_from_XML(self, e):
        debug('xml_in(', 'instance_from_XML, node.tag=', e.tag)

        pvs = []
        for child in e.getchildren():
            (prop, val) = self.propval_from_XML(child)
            if prop.startswith(RIF_PREFIX):
                prop = prop[len(RIF_PREFIX):]
            elif prop.startswith("{"):
                raise RuntimeError("unknown namespace used: %s" % prop)
            debug('xml_in', 'prop=', prop, 'val=', val)
            pvs.append( (prop, val) )

        if pvs:
            if e.text.strip() == "":
                pass  # white text ignored
            else:
                raise RuntimeError("text and child elements, mixed!")
            id = webdata.ID(e.tag)
            debug('xml_in', 'ID=', id)
            try:
                pyclass = self.view.classForID[id]
            except KeyError:
                raise RuntimeError("No python class for element tag %s" 
                                   %`e.tag`)
            debug('xml_in', 'python class=', pyclass)
            value = webdata.reconstruct(pyclass, pvs)
        else:
            value = e.text
            
        return value
        debug('xml_in)')

    def propval_from_XML(self, e):
        
        ordered = False
        for (name, value) in e.items():
            if name=="ordered" and value=="yes":
                ordered = True
            else:
                raise RuntimeError('unexpected attribute: %s=%s' % (`name`, `value`))

        if ordered:
            value = []
            for child in e.getchildren():
                value.append(self.instance_from_XML(child))
        else:
            sole_child = None
            for c in e.getchildren():
                if sole_child is None:
                    sole_child = c
                    assert sole_child is not None
                else:
                    raise RuntimeError('unexepected additional child %s' % `c`)

            if sole_child is None:
                value = e.text
            else:
                value = self.instance_from_XML(sole_child)

        return (e.tag, value)

        
if __name__ == "__main__":
    
    import sys

    s = sys.stdin.read()
    p = Parser()
    p.root = ET.fromstring(s)
    doc = p.instance_from_XML(p.root)
    print "Document:", doc

