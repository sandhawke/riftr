#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

Base Class (general tools) for classes which serialize in particular
languages.

Not RIF specific, but making some simplifying assumptions (like that
module names don't matter.)    Could use names like do_rif_Document where
"rif" is the module name, to solve this.


TODO:
   move XML stuff to a subclass
       xmlserializer

"""

import sys
from cStringIO import StringIO

from debugtools import debug
import debugtools
#debugtools.tags.add('all')

import AST2
import qname

class General (object):

    def __init__(self, stream=sys.stdout, indent_factor=4):
        self.stream = stream
        self.indent_factor = int(indent_factor)

        self.build_domap()

        self.internal = False
        self.indent = 0
        self.br_level = 1
        self.at_left_margin = True
        self.at_lend= False

        # for XML only
        self.root = None
        self.current_element = None
        self.nsmap = qname.Map()
        self.nsmap.defaults = [qname.common]

    def build_domap(self):
        self.domap = { }
        prefix = "do_"
        for f in dir(self):
            debug('build_domap', 'candidate:', f)
            if f.startswith(prefix):
                name = f[len(prefix):]
                self.domap[name] = getattr(self, f)
                debug('build_domap', 'added:', name)

    def str_do(self, *objList):
        state = {}   # for keeping the old stream, at_lend, etc.
        state.update(self.__dict__)

        buffer = StringIO()
        self.internal = False
        self.stream = buffer
        self.do(*objList)

        self.__dict__.update(state)
        return buffer.getvalue()

    def do(self, *objList):
        
        was_internal = self.internal
        self.internal = True

        for obj in objList:

            typenames = []
            if isinstance(obj, AST2.BaseDataValue):
                typenames.append(obj.serialize_as_type)

            if isinstance(obj, AST2.Sequence):
                typenames.append("Sequence")
            elif isinstance(obj, AST2.Instance):
                # use schema.py to find superclasses?
                pt = obj.primary_type
                assert isinstance(pt, basestring)
                try:
                    (dummy, pt) = pt.split("#")
                except ValueError:
                    pass
                typenames.append(pt)
            else:
                # is there some good way to look at the python superclass
                # hierarchy...?
                typenames.append(type(obj).__name__)
            debug('serializer(', 'typenames', typenames)

            for t in typenames:
                doer = self.domap.get(t, self.default_do)
                if doer is not self.default_do:
                    break
            debug('serializer', 'doer:', doer)

            doer(obj)
            debug('serializer', 'current', self.current_element)
            debug('serializer)')
        
        
        self.internal = was_internal
        if not was_internal:
            debug('serializer', 'flushing...')
            self.flush()

    def out(self, *args, **kwargs):
        """
        Write the arguments to the output stream.

        If we are at a line-end (set by calling lend()), then move
        down to the next line (and indent by the current indent)
        before doing any output.  This is done even if there are no
        arguments.

        After output, look at the keyword argument "keep":

           if keep=1, output a space (or whatever the if_keep text is
                      set to) and stay to the same line
           if keep=0, call self.lend(), so that the next output will be
                      done on a new line.
           
        Values of keep between 0 and 1 mean that it's okay to either
        keep or not keep -- that is, this is an okay place to do a
        line break if necessary.  If line breaking is necessary, then
        places with lower keep values (closer to keep=0) will be
        used for line breaking first.

        (This variable line breaking is not yet implemented, but
        still, try to use intermediate values for keep if it's an
        okay-to-break spot.)

        It's okay to have \n inside an argument; it's treated as if
        every \n split the out() call into multiple out() calls.

        TODO:

           if max_line_length, then each line should be assembled into
           a list of strings and possible break points (each with its
           if_keep, indent, and maybe if_break text), so at the end of
           the line, we can break it as much as necessary.   

           Maybe we'll need some sort of "align" marker, for stuff like: 
                some_long_function(arg1, arg2, arg3
                                   arg4, arg5)
           where the indent is some kinda-fixed amount.   Basically,
           each of arg1...arg5 should be marked as items in a group.
           Then it's a policy decision whether 
                - group membership doesn't matter
                - all group items on new line
                - first group item in place; all others
                  line up below it
                - first group item in place; any that need
                  a new line, they line up below it.

        """

        if self.at_lend:
            self.at_lend = False
            old_indent = self.indent
            indent = kwargs.get("indent", self.indent)
            self.stream.write(self.newline)
            self.indent = old_indent

        for arg in args:
            lines = arg.split("\n")
            for line in lines[:-1]:
                self.out(line)
            self.stream.write(lines[-1])
            if lines[-1]:
                self.at_left_margin = False
            
        keep = kwargs.get("keep", 0) 
        if keep > 0.5:  # make this flexible later
            if_keep = kwargs.get("if_keep", getattr(self, "if_keep", " "))
            self.stream.write(if_keep)
        else:
            self.lend()


    def outk(self, *args):
        """Short for out(..., keep=1)"""
        self.out(*args, **{'keep':1})

    def lend(self):
        """This is the end of a line.   The next time you try
        to write, do a newline/indent before anything else.  We 
        don't do it NOW because we might have multiple lends, and
        we might change the indent after this, before the text comes."""
        self.at_lend = True
        

    @property
    def newline(self):
        return "\n" + " " * (self.indent * self.indent_factor)


    ################################################################
    #
    #   xml stuff called by subclasses
    #

    def xml_begin(self, tag, attrs={}):
        if self.current_element is None:
            new = Element(parent=None)
            self.root = new
        else:
            new = Element(parent=self.current_element)
            self.current_element.children.append(new)
        try:
            (ns, local) = tag.split("#")
        except ValueError:
            ns = None
            local = tag
        new.setTagNS(ns, local)
        for ((ns,local),v) in attrs.items():
            new.setAttributeNS(ns, local, v)
        self.current_element = new

    def xml_end(self):
        parent = self.current_element.parent
        if parent is None:
            assert self.root == self.current_element
        self.current_element = parent

    def xml_set_text(self, text):
        """Make the current node just contain the given text.  No mixed markup
        """
        self.current_element.text = text

    ################################################################
    #
    #    xml pretty-printing machinery
    #

    def flush(self):
        if self.root is not None:
            self.short_count = {}
            self.ns_add_tree(self.root)
            debug('serializer', 'short_count:',self.short_count)
            (count, best_short) = sorted(
               [(count, short) for (short, count) in self.short_count.items()]
               )[-1]
            debug('serializer', 'count, best_short =', count, best_short)
            self.nsmap.bind('', self.nsmap.getLong(best_short))
            
            self.out_xml(self.root, is_root=True)

        self.stream.write(self.newline)

    def ns_add_tree(self, element):
        ns = element.tagPair[0]
        self.ns_used(ns)
        for ((ns, local), value) in element.attr.items():
            self.ns_used(ns)
        for child in element.children:
            self.ns_add_tree(child)
            
    def ns_used(self, ns):
        if ns is not None:
            short = self.nsmap.getShort(ns)
            try:
                self.short_count[short] += 1
            except KeyError:
                self.short_count[short] = 1

    def out_xml(self, element, is_root=False):

        attrs = {}

        for ((ns, local), value) in element.attr.items():
            if ns is None:
                attrs[local] = value
            else:
                attrs[self.nsmap.getShort(ns)+":"+local] = value

        if is_root:
            self.out('<?xml version="1.0"?>')
            for short in self.nsmap.shortNames():
                long1 = self.nsmap.getLong(short)
                
                # temp hack!    I'm losing the trailing # on rifns
                if long1.endswith("/") or long1.endswith("#"):
                    long = long
                else:
                    long = long1 + "#"

                if short == "":
                    attrs["xmlns"] = long
                elif short == "xmlns":
                    pass
                else:
                    # this is iffy; we still want this ns declared
                    # if it's used for any attributes in the default ns,
                    # I think...
                    if self.nsmap.getShort(long1) != "":
                        attrs["xmlns:"+short] = long

        attr_text = ""
        for key in sorted(attrs.keys()):
            attr_text += ' %s="%s"' % (key, xml_attr_quote(attrs[key]))
            
        (ns, local) = element.tagPair
        if ns is None:
            tagName = local
        else:
            short = self.nsmap.getShort(ns)
            if short:
                tagName = self.nsmap.getShort(ns) + ":" + local
            else:
                tagName = local

        k = { "keep": 0 }
        k = { "keep": 1, "if_keep": "" }
        if element.children or element.text:
            self.out("<"+tagName+attr_text+">", **k)
            if element.text is not None:
                self.out(xml_body_quote(element.text), 
                         indent=0, keep=1, if_keep="")
                assert element.children == []
            else:
                if len(element.children) == 1:
                    self.out_xml(element.children[0])
                else:
                    self.indent += 1
                    for child in element.children:
                        self.lend()
                        self.out_xml(child)
                        self.lend()
                    self.indent -= 1
            self.out("</"+tagName+">", **k)
        else:
            self.out("<"+tagName+attr_text+" />", **k)
        

    ################################################################

        
def xml_body_quote(s):
    return s.replace("&", "&amp;").replace("<", "&lt;")

def xml_attr_quote(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace('"', "&quot;")

class Element (object) :
    """ Yes, I could use ElementTree or minidom, but for this, rolling
    my own actually seems a lot easier.   Oh well.
    """

    __slots__ = ["parent", "tagPair", "children", "text", "attr"]

    def __init__(self, parent):
        self.parent = parent
        self.children = []
        self.attr = {}
        self.text = None

    def setTagNS(self, ns, local):
        self.tagPair = (ns, local)

    def setAttributeNS(self, ns, local, value):
        self.attr[(ns, local)]=value

    
            
