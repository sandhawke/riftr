#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

Rewrite an AST so that any calls to buildin functions are occur in a
calculate/assign predicate.

Is this really easier than XSLT?   Hrm...   It's pretty messy...

"""

import plugin

from debugtools import debug
from datanode import NodeFactory
import qname

rifns = qname.common.rif

class Plugin (plugin.TransformPlugin):
   """Rewrite so that any calls to external functions now occur in a
calculate/assign predicate.   Needed for Prolog.
   """

   id=__name__
   options = [
       plugin.Option('calc_pred', 'IRI/Qname of the calculate/assign predicate to use',
                     default="pred:calc"),
       ]


   def __init__(self, calc_pred=None, factory=None):
       self.factory = factory or NodeFactory()
       self.calc_pred = (calc_pred or 
                         self.factory.obtainDataValue(qname.common.uri(calc_pred),
                                              rifns+"iri"))
       self.v_count = 0

   def transform(self, instance):

       instance.map_replace(self.replace_atomic)
       return instance

   def replace_atomic(self, atom):
       '''Replace any atoms containing external-exprs with an And
       of the atom re-written and a call to calc'''

       if not (atom.has_type(rifns+"Atom") or
               atom.has_type(rifns+"Equal")):
           return atom

       debug('f2p(', 'found an atom')
       harvest = []
       atom.map_replace(lambda x: self.replace_external(x, harvest))
       
       if harvest:
           parent = self.factory.Instance(rifns+"And")
           for (var, expr) in harvest:
               calc = self.factory.Instance(rifns+"Atom")
               setattr(calc, rifns+"op", self.calc_pred)
               setattr(calc, rifns+"args", self.factory.Sequence(items=[var, expr]))
               setattr(parent, rifns+"formula", calc)
           getattr(parent, rifns+"formula").clear()
           setattr(parent, rifns+"formula", atom)
           debug('f2p)', 'replaced it')
           return parent
       else:
           debug('f2p)', 'left it alone')
           return atom
               
   def replace_external(self, external, harvest):
       '''If the instance is a rif.External, then replace it with a new variable
       and append them both to harvest'''

       debug('f2p', 'looking for external, found a', external._primary_type)
       if not external.has_type(rifns+"External"):
           return external

       debug('f2p', 'got external!', external)
       var = self.factory.Instance(rifns+"Var")
       # TODO: put the variable name up in quantifier!!! (and make sure
       # it's unique...)
       # (we'll have to do that with a trick like 'harvest' on Forall, I guess)
       setattr(var, rifns+"name", self.factory.StringValue("genvar%d" % self.v_count))
       self.v_count += 1
       harvest.append( (var, getattr(external, rifns+"content").the) )
       debug('f2p(', 'found an external; replaced with', var)
       return var
  

plugin.register(Plugin)


