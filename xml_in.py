#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

http://docs.python.org/library/xml.etree.elementtree.html

"""

import sys
import xml.etree.cElementTree as ET
import inspect

import rif

from debugtools import debug
import debugtools
debugtools.tags.add("ps_out")
#debugtools.tags.add("reconstruct")
#debugtools.tags.add("xml_in")

class Parser:

    def __init__(self, schema):
        self.root = None
        self.schema = schema

    def get_class_props(self, tag):
        
        for (cls, props) in self.schema.items():
            try:
                clsid = "{%s}%s" % (cls.xml_ns, cls.__name__)
            except AttributeError:
                pass
            if clsid == tag:
                return (cls, props)
        raise RuntimeError('unknown tag: %s' % tag)

    def reconstruct(self, tag, pvList):

        debug('reconstruct', 'tag=', tag, 'pvList=', pvList)

        (cls,props) = self.get_class_props(tag)
        obj = cls()  # don't use __init__ arguments....

        values = {}
        for (xml_name,v) in pvList:
            values.setdefault(xml_name, []).append(v)
        debug('reconstruct', 'values=', values)

        for prop in props:
            if prop.list_valued:
                value = values.get(prop.xml_name, [])
                for v in value:
                    self.range_check(v, prop)
            else:
                count = len(values.get(prop.xml_name, []))
                if prop.required and count < 1:
                    raise RuntimeError('No value provided for required property %s', prop)
                if count > 1:
                    raise RuntimeError('Property %s is supposed to be single-valued but has values %s, %s, ...'% (prop, values[prop.xml_name][0], values[prop.xml_name][1]))
                value = values[prop.xml_name][0]
                self.range_check(value, prop)

            setattr(obj, prop.python_name, value)

                        
                    
        return obj

                            
    def range_check(self, value, property):
        range = property.range
        if range is None:
            return 
        if isinstance(value, range):
            return
        raise RuntimeError('Value out of range / bad type for property %s, %s is not a %s' %
                           (property, value, range))
        

    def instance_from_XML(self, e):
        debug('xml_in(', 'instance_from_XML, node.tag=', e.tag)

        pvs = []

        type_value = None
        for (name, value) in e.items():
            if name=="type":
                # Special case for Consts, which are weird
                if e.tag == "{http://www.w3.org/2007/rif#}Const":
                    result = rif.Const()
                    result.datatype = value
                    result.lexrep = e.text

                    debug('xml_in)', 'returning', result)            
                    return result
                else:
                    raise RuntimeError('type attribute on non-Const')
            else:
                raise RuntimeError('unexpected attribute: %s=%s' % (`name`, `value`))

        for child in e.getchildren():
            for (prop, val) in self.propval_from_XML(child):
                debug('xml_in', 'prop=', prop, 'val=', val)
                pvs.append( (prop, val) )

        if pvs:
            if e.text.strip() == "":
                pass  # white text ignored
            else:
                raise RuntimeError("text and child elements, mixed!")
            value = self.reconstruct(e.tag, pvs)
        else:

            # special case for Vars, which are weird
            if e.tag == "{http://www.w3.org/2007/rif#}Var":
                result = rif.Var()
                result.name = e.text
                debug('xml_in)', 'returning', result)            
                return result

            #value = e.text
            raise RuntimeError("unexpected text content: %s" % e.text)

        debug('xml_in)', 'returning', value)            
        return value


    def propval_from_XML(self, e):

        # special case for "slots", which are weird...
        if e.tag == "{http://www.w3.org/2007/rif#}slot":
            (key, value) = e.getchildren()
            result = rif.Slot()
            result.key = self.instance_from_XML(key)
            result.value = self.instance_from_XML(value)
            # check range?
            debug('xml_in)', 'returning', result)            
            return [ (e.tag, result) ]

        ordered = False
        for (name, value) in e.items():
            if name=="ordered" and value=="yes":
                ordered = True
            else:
                raise RuntimeError('unexpected attribute: %s=%s' % (`name`, `value`))

        if ordered:
            result = []
            for child in e.getchildren():
                result.append( (e.tag, self.instance_from_XML(child))  )
            return result
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

            return [ (e.tag, value) ]

        
if __name__ == "__main__":
    
    import sys

    s = sys.stdin.read()
    p = Parser(rif.bld_schema)
    p.root = ET.fromstring(s)
    doc = p.instance_from_XML(p.root)
    print rif.as_ps(doc)

