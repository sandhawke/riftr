#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""


"""

import AST2

def from_conclusion(node):
    """Turn a test-case conclusion into a proper Query,
    with no variables.
    """
    q = AST2.Instance("Query")
    q.variables = AST2.Sequence()
    q.pattern = node
    return q




