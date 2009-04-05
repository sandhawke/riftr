#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

Rewrite an AST so that nest And's are just one And


"""

import plugin

from debugtools import debug
import AST2
import qname

rifns = qname.common.rif

class Plugin (plugin.TransformPlugin):
   """Rewrite so that and(a,and(b,c)) is just and(a,b,c), etc"""

   id=__name__
   options = [
       plugin.Option('oper', 'IRI/Qname of the operator to unnest',
                     default="rif:And"),
       plugin.Option('prop', 'IRI/Qname of value property of that operator',
                     default="rif:formula"),
       ]


   def __init__(self, oper='rif:And', prop='rif:formula'):
       self.oper = qname.common.uri(oper)
       self.prop = qname.common.uri(prop)
       debug('unnest', 'oper: ', self.oper)
       debug('unnest', 'prop: ', self.prop)

   def transform(self, instance):
       instance.map_replace(self.replace)
       return instance

   def replace(self, inst):

       if inst.has_primary_type(self.oper):

           debug('unnest(', 'found oper match', self.oper)
           new = []
           multi = getattr(inst, self.prop)
           for child in multi.values:
               debug('unnest', 'child type:', child.primary_type)
               if child.has_primary_type(self.oper):
                   debug('unnest', '...  oper match', self.oper)
                   new.extend(getattr(child, self.prop).values)
               else:
                   new.append(child)
           multi.replace_values(new)
           debug('unnest)')

       return inst

plugin.register(Plugin)


