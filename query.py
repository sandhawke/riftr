#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""


"""

import datanode

def from_conclusion(node):
    """Turn a test-case conclusion into a proper Query,
    with no variables.
    """
    ast = datanode.NodeFactory()
    ast.nsmap.bind("", "http://www.w3.org/2007/rif#")
    q = ast.Instance("Query")
    q.variables = ast.Sequence()
    q.pattern = node
    return q




