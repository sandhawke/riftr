#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

Knows nothing of RIF.

"""

import sys
import json

import nodewriter
import nodecentric
import qname
import plugin

class Plugin (plugin.OutputPlugin):
   """JSON out (requires svp)."""

   id=__name__

   def __init__(self, **kwargs):
       pass

   def serialize(self, doc, output_stream):
       nsmap = qname.Map()
       # once to figure out most common
       obj = nodecentric.as_dict_list(doc, nsmap, True)
       try:
           nsmap.bind("", nsmap.most_common)
       except ValueError: pass
       # then again, with the right nsmap
       obj = nodecentric.as_dict_list(doc, nsmap, True)
       obj["__ns"] = nsmap._long
       json.dump(obj, output_stream, indent=4, sort_keys=True)
       
  
