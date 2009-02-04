#!/usr/bin/env python2.5
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

Support for Abstract Syntax Trees (ASTs)

   t[0] = rif.Subclass(sub=t[1], super=t[3])

   t[0] = AST.Node(type="{...}Subclass", sub=t[1], super=t[3])
some other kind of type?   (ns, foo) vs (foo)
   t[0] = node('Subclass', sub=t[1], super=t[3])

node can go either way...
   (current style, or AST style)

"""

import debugtools 
from debugtools import debug


class Node (object):
    """
    pretty free form!
    """
    
    def __init__(self, type, **kwargs):
        self._type = type
        self.__dict__.update(kwargs)

    def __cmp__(self, other):
        return cmp(self.__dict__, other.__dict__)

class Sequence (object):
    """
    When the value is a sequence of values, use this. 
    (when it just has multiple values, then use python list).
    """
    
    def __init__(self, items=None):
        self.items = items or []
    

# gosh, that was hard.   :-)

