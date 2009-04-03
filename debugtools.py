#! /usr/bin/env python
"""

My spiffy trace/debug routine....   :-)

"""
__version__ = """$Id$"""

import sys


tags = set()

indent = 0

def debug(tag, *obj):
    """Output a debugging line, if debugging for this tag is turned
    on.   Also does nest-indenting.   If the tag ends with "(" then
    succeeding lines are indented.  If it ends with ")" then this is
    the last line at this indent level."""

    global indent
    global tags

    indentChange = 0
    if tag.endswith("("):
        indentChange = 1
        tag = tag[0:-1]
    if tag.endswith(")"):
        indentChange = -1
        tag = tag[0:-1]
    if len(obj) > 0:
        if tag in tags or "all" in tags:
            # sys.stderr.write("(indent %04d)" % indent)
            sys.stderr.write("%-7s " %(tag+":"))
            sys.stderr.write(".  " * indent)
            sys.stderr.write(" ".join([my_repr(x) for x in obj]) + "\n")
    indent += indentChange

def my_repr(x):
    """
    Like repr() but make sure everything is utf-8, and dictionaries are
    given a stable ordering.
    """
    if isinstance(x,dict):
        x = dict_repr(x)
    if isinstance(x, unicode):
        x = x.encode("utf-8")
        assert isinstance(x, str)
    if isinstance(x, str):
        if x != x.strip():
            x = '"' + x.replace('"', "\\\"") + '"'
        return x

    x = repr(x)
    return my_repr(x)

def dict_repr(d):
    """stable serialization of dict"""

    pairs = []
    keys = [my_repr(k) for k in d.keys()]
    for k in sorted(keys):
        pairs.append(k+": "+my_repr(d[k]))
    return "{"+", ".join(pairs)+"}"
    
