#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

"""

import sys

from rdfnode import NodeFactory
import plugin
from cStringIO import StringIO


class OutPlugin (plugin.OutputPlugin):
   """Current AST out via rdfnode+rdflib."""

   id="rdflib_out"

   spec=""

   options = [
       plugin.Option('format', 'Format parameter to rdflib',
                     default="xml"),
       ]


   def __init__(self, **kwargs):
       for option in self.options:
           kwargs.setdefault(option.name, option.default)
       self.__dict__.update(kwargs)

   def serialize(self, doc, output_stream):
       nf = NodeFactory()
       doc = nf.deepcopy(doc)
       nf.graph.serialize(destination=output_stream, format=self.format)
  
plugin.register(OutPlugin)


if __name__ == "__main__":
    pass
