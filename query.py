#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""


"""

import datanode

rifns = "http://www.w3.org/2007/rif#"
def from_conclusion(node):
    """Turn a test-case conclusion into a proper Query,
    with no variables.
    """
    ast = node._factory
    q = ast.Instance(rifns+"Query")
    setattr(q, rifns+"variables", ast.Sequence())
    setattr(q, rifns+"pattern", node)
    return q




