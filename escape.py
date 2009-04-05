#!/usr/bin/env python2.5
#-*-mode: python -*- -*- coding: utf-8 -*-
"""

Stuff for converting between strings containing lots of funky
characters and strings containing few funky characters.  This is
sometimes called "quoting", sometime "escaping", sometimes "encoding",
etc.

"""
__version__="$Id$"

import re

import debugtools 
from debugtools import debug

import error

def alnumEscape(str):
    """
    Turn any string into an alphanumeric (plus _) string, by turning
    illegal chars in __hex_.  For the common case, we turn a single
    space (but only the first in a sequence of spaces) into a single
    underscore.  I believe this is a reverseable 1-1 mapping, but I
    could be wrong.
    
    >>> print alnumEscape("Hello")
    Hello
    >>> print alnumEscape("Hello World")
    Hello_World
    >>> print alnumEscape("Hello  World")
    Hello___20_World
    >>> print alnumEscape("Hello, World!")
    Hello__2c__World__21_
    >>> print alnumEscape("Hello,_World!")
    Hello__2c___5f_World__21_
    >>> print alnumEscape("Markus Krötzsch")
    Markus_Kr__c3___b6_tzsch
    
    """
    result = ""
    spaceRun = False
    for char in str:
        if char.isalnum():
            result += char
            spaceRun = False
        elif char == " ":
            if spaceRun:
                result += "__%x_"%ord(char)
            else:
                result += "_"
                spaceRun = True
        else:
            result += "__%x_"%ord(char)
    return result

xPat = re.compile(r"""__([abcdef0-9]+)_""")
def alnumUnescape(str):
    """

    >>> alnumUnescape(alnumEscape("Hello, World!"))
    'Hello, World!'
    >>> p = 'Markus Krötzsch'
    >>> p == alnumUnescape(alnumEscape(p))
    True
    
    """
    result = []
    delim = False
    for part in xPat.split(str):
        if delim:
            result.append(chr(int(part, 16)))
        else:
            result.append(part.replace("_", " "))
        delim = not delim
    return "".join(result)

# from http://effbot.org/zone/re-sub.htm#unescape-html (renamed)
#
import re, htmlentitydefs

##
# Removes HTML or XML character references and entities from a text string.
#
# @param text The HTML (or XML) source text.
# @return The plain text, as a Unicode string, if necessary.

def entity_unescape(text):
    r"""
    Does both XML and HTML.    Hrmmm.    

    Will the XML parser do the XML ones for us?

    >>> entity_unescape("a=&quot;&lt;b&gt;&quot;")
    u'a="<b>"'

    >>> entity_unescape("a=&apos;&nbsp;&apos;")
    u"a='\xa0'"

    """
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                if text[1:-1] == "amp":
                   text = "&"
                elif text[1:-1] == "gt":
                   text = ">"
                elif text[1:-1] == "lt":
                   text = "<"
                elif text[1:-1] == "apos":
                   text = "'"
                else:
                    text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)

if __name__ == "__main__":
    import doctest, sys
    doctest.testmod(sys.modules[__name__])


