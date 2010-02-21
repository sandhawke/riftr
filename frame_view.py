#!/usr/bin/env python
# -*-mode: python -*-  -*- coding: utf-8 -*-
"""

Transform to/from frameview

"""

import sys


from datanode import NodeFactory
from nodecentric import RDF_TYPE
import plugin
import error

from xmlns import RIF, split, iri_from_tag

rifxmlns = "http://www.w3.org/2007/rif#"
rifrdfns = "http://www.w3.org/2007/rifr#"

class Property (object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    # typ : 
    #     multi -- however many values there are, repeat the property
    #     list -- use ordered="yes"
    #     olist -- like list, but omit from the XML it if empty
    #     optional -- like multi, but there can be only one.  That fact
    #                 doesn't matter much; we still need to map it to a
    #                 list, so that we'll know when it's missing.
    #     required -- for this, we don't need to map it to a list.
    #                 finally, the value can simply be there.

rifxprops = { }
rifrprops = { }

def add_prop(ptag, xtag, typ, rtag=None, cls=None):
    xname = rifxmlns+xtag
    rname = rifrdfns+xtag
    parent = rifxmlns+ptag
    prop = Property(xname=xname,
                    rname=rname,
                    parent=parent,
                    typ=typ,
                    cls=cls)

    rifxprops.setdefault(parent, []).append(prop)

    # it's okay to have multiple xprops for the same rprop,
    # as long as ONE of the properties tells us the class.
    rifrprops.setdefault(rname, []).append(prop)

# looking at absyn/bld.asn...; this should go in the spec.
#
# (note that "id" & "meta" are handled differently)
#
add_prop("Document", "directive", "multi")
add_prop("Document", "payload", "optional")
add_prop("Group", "sentence", "multi")
add_prop("Forall", "declare", "multi", "univar")
add_prop("Forall", "formula", "required", "formula")
add_prop("Implies", "if", "required")
add_prop("Implies", "then", "required")
add_prop("And", "formula", "multi", "allTrue")
add_prop("Or", "formula", "multi", "anyTrue")
add_prop("Exists", "declare", "multi", "exivar")
add_prop("Exists", "formula", "required", "formula")
add_prop("Atom", "args", "olist", cls="Atom_Ordered")
add_prop("Atom", "slot", "olist", cls="Atom_Named")

add_prop("Var", "name", "required")
add_prop("Const", "value", "required")
add_prop("Frame", "object", "required")
add_prop("Frame", "slot", "special_slot_handler")
  

def to_frame_view(node):
    new = node._factory.Instance()
    classes = set()
    for prop in rifxprops[getattr(node, RDF_TYPE).the.lexrep]:
        try:
            cls = prop.cls
            if cls is not None:
                classes.add(cls)
        except AttributeError:
            pass

        if prop.typ == "multi" or prop.typ == "optional":
            items = node._factory.Sequence()
            for item in getattr(node, prop.xname).values:
                items.append(item)
            setattr(new, prop.rname, items)
            if prop.typ == "optional" and len(items.items) > 1:
                raise RuntimeError, "multiple values given to single valued property"                
        elif prop.typ == "olist":
            if hasattr(node, prop.xname):
                setattr(new, prop.rname, getattr(node, prop.xname).the)
            else:
                setattr(new, prop.rname, node._factory.Sequence())
        elif prop.typ == "list":
            if hasattr(node, prop.xname):
                setattr(new, prop.rname, getattr(node, prop.xname).the)
            else:
                raise RuntimeError, "require list property is missing"
        elif prop.typ == "required":
            setattr(new, prop.rname, getattr(node, prop.xname).the)
        elif prop.typ == "special_slot_handler":
            items = node._factory.Sequence()
            for pair in getattr(node, prop.xname).values:
                (key, value) = pair.items
                pair_node = node._factory.Instance()
                setattr(pair_node, rifrdfns+"slotKey", key)
                setattr(pair_node, rifrdfns+"slotValue", value)
                items.append(pair_node)
            setattr(new, prop.rname, items)
        else:
            raise RuntimeError, 'unimplemented property type: '+prop.typ

    if len(classes) == 1:
        setattr(new, RDF_TYPE, node._factory.StringValue(classes.pop()))
    elif len(classes) == 0:
        # setattr(new, RDF_TYPE, node.rdf_type.the)    WRONG NAMESPACE
        otype = node.rdf_type.the.lexrep
        ntype = otype.replace(rifxmlns, rifrdfns)
        print otype, ntype
        assert otype != ntype
        setattr(new, RDF_TYPE, node._factory.StringValue(ntype))
    else:
        raise RuntimeError, "Conflicting classes: "+`classes`

    return new
        

def from_frame_view(node):
    new = node._factory.Instance()
    # "parent" is basically an rdf_type, but we need to have exactly
    # one for the non-frame view, so we treat it differently.
    # (the tree view?  the 2007 view?  what to call it?)
    possible_parents = None
    for rprop in node.properties:
        parents = set()  # all the different parents for maybe matching props
        for prop in rifrprops[rprop]:
            parents.add(prop.parent)
        if possible_parents is None:
            possible_parents = parents
        else:
            possible_parents = possible_parents.intersection(parents)
    if len(possible_parents) != 1:
        raise RuntimeError, "Possible parents: "+`possible_parents`
    new._primary_type = possible_parents.pop()
    for prop in rifxprops[new._primary_type]:
        # if there is no value, then the rdf graph isn't a wellformed RIF struct
        value = getattr(node, prop.rname).the
        if prop.typ == "multi" or prop.typ == "optional":
            for item in value.items:
                getattr(new, prop.xname).add(item)
        elif prop.typ == "olist":
            assert value.is_sequence
            if len(value.items) == 0:
                pass
            else:
                setattr(new, prop.xname, value)
        elif prop.typ == "list":
            setattr(new, prop.xname, value)
        elif prop.typ == "required":
            setattr(new, prop.xname, getattr(node, prop.rname).the)
        else:
            raise RuntimeError, 'unimplemented property type: '+prop.typ


    return new

class ConvertToFrameView (plugin.TransformPlugin):
    "Convert from Old/2007/XML Style to Frame View"
    id = "to_frame_view"
    spec = "http://www.w3.org/2005/rules/wiki/Frame_View"
    options = [ ] 
       #plugin.Option('oper', 'IRI/Qname of the operator to unnest',
       #              default="rif:And"),



    def transform(self, root):
        return root.map_replace(to_frame_view)


class ConvertFromFrameView (plugin.TransformPlugin):
    "Convert from Frame View (RDF Triples) into Old/2007/XML Style"
    id = "from_frame_view"
    spec = "http://www.w3.org/2005/rules/wiki/Frame_View"
    options = [ ] 
       #plugin.Option('oper', 'IRI/Qname of the operator to unnest',
       #              default="rif:And"),


    def transform(self, root):
        return root.map_replace(from_frame_view)

plugin.register(ConvertFromFrameView)
plugin.register(ConvertToFrameView)
