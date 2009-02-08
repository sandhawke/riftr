#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

Base Class (general tools) for classes which serialize in particular languages.

Not RIF specific, but making some simplifying assumptions (like that
module names don't matter.)    Could use names like do_rif_Document where
"rif" is the module name, to solve this.

"""

import sys

from debugtools import debug
import debugtools
#debugtools.tags.add('all')

import AST

class General:

    def __init__(self, stream=sys.stdout, indent_factor=4):
        self.stream = stream
        self.indent = 0
        self.indent_factor = int(indent_factor)
        self.build_domap()
        self.br_level = 1
        self.xml_stack = []
        self.at_left_margin = True
        self.at_lend= False

    def flush(self):
        # in case we used etree ...?
        pass

    def build_domap(self):
        self.domap = { }
        prefix = "do_"
        for f in dir(self):
            debug('build_domap', 'candidate:', f)
            if f.startswith(prefix):
                name = f[len(prefix):]
                self.domap[name] = getattr(self, f)
                debug('build_domap', 'added:', name)

    def OLD_do(self, *objList):
        
        # we could use inspect.getclasstree to do some kind of
        # inheritance here....    

        for obj in objList:
            typename = type(obj).__name__
            try:
                doer = self.domap[typename]
            except KeyError:
                try:
                    doer = self.default_do
                except AttributeError:
                    raise RuntimeError("No serialization defined for your %s, %s" % (typename, `obj`))
            doer(obj)

    def do(self, *objList):
        
        for obj in objList:
            if isinstance(obj, AST.Node):
                typename = obj._type[1]
            else:
                typename = type(obj).__name__
            debug('serializer', 'typename', typename)
            # use schema.py to find superclasses?
            try:
                doer = self.domap[typename]
                debug('serializer', 'doer', doer)
            except KeyError:
                try:
                    doer = self.default_do
                except AttributeError:
                    raise RuntimeError("No serialization defined for your %s, %s" % (typename, `obj`))
            doer(obj)
        
    def out(self, *args):

        if self.at_lend:
            self.at_lend = False
            self.br()

        for arg in args:
            self.stream.write(arg)
            self.at_left_margin = False

    def lend(self, level=2):
        if level >= self.br_level:
            self.at_lend = True

    def br(self):
        "Go to a new line at this point"
        if self.at_left_margin:
            return
        self.out(self.newline)
        self.at_left_margin = True

    def brsp(self, text=" ", level=2):
        """output a space, but this is an okay place to go to a new line if
           that's useful"""
        if level >= self.br_level:
            self.br()
        else:
            self.out(text)

    def brsp_good(self, text=" "):
        "This is a good place to go to a new line"
        self.brsp(text, level=1)

    def brsp_poor(self, text=" "):
        "This is a poor (but still not erroneous) place to go to a new line"
        self.brsp(text, level=3)
        

    @property
    def newline(self):
        return "\n" + " " * (self.indent * self.indent_factor)

    def xml_begin(self, tag, attrs=None, one_line=False):
        if not one_line: self.lend(2)
        self.out("<"+tag+">")
        self.xml_stack.append(tag)
        self.indent += 1
        #self.lend(2)

    # maybe don't go to a new line, when there's only one
    # sub-element, a la  <Var><name> ... ?
    # hard to detect here.
        
    def xml_end(self, one_line=False):
        self.indent -= 1
        #self.lend(2)
        tag = self.xml_stack.pop()
        self.out("</"+tag+">")
        if not one_line: self.lend(2)


