#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

Base Class (general tools) for classes which serialize in particular languages.

Not RIF specific, but making some simplifying assumptions (like that
module names don't matter.)    Could use names like do_rif_Document where
"rif" is the module name, to solve this.

"""

import sys
from cStringIO import StringIO

from debugtools import debug
import debugtools
#debugtools.tags.add('all')

import AST

class General (object):

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

    def str_do(self, *objList):
        state = {}   # for keeping the old stream, at_lend, etc.
        state.update(self.__dict__)

        buffer = StringIO()
        self.stream = buffer
        self.do(*objList)

        self.__dict__.update(state)
        return buffer.getvalue()

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
            self.stream.write(self.newline)

        for arg in args:
            lines = arg.split("\n")
            for line in lines[:-1]:
                self.out(line)
            self.stream.write(lines[-1])
            if lines[-1]:
                self.at_left_margin = False
            
        keep = kwargs.get("keep", 0) 
        if_keep = kwargs.get("if_keep", " ") 
        if keep > 0.5:  # make this flexible later
            self.stream.write(if_keep)
        else:
            self.lend()


    def outk(self, *args):
        """Short for out(..., keep=1)"""
        self.out(*args, **{'keep':1})

    def lend(self, ignore_this_arg=None):
        """This is the end of a line.   The next time you try
        to write, do a newline/indent before anything else.  We 
        don't do it NOW because we might have multiple lends, and
        we might change the indent after this, before the text."""
        self.at_lend = True

    @property
    def newline(self):
        return "\n" + " " * (self.indent * self.indent_factor)


    ################################################################
    #    This BR stuff is deprecated.

    def br(self):
        "Go to a new line at this point"
        if self.at_left_margin:
            return
        self.stream.write(self.newline)
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


