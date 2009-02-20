#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

TODO:
   runtime --debug
   runtime --start_symbol


"""

import ply.yacc as yacc
import ply.lex as lex

import rif
import error
import mps_lex
import plugin
import AST

RIFNS = "http://www.w3.org/2007/rif#"
RDFNS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
XSDNS = "http://www.w3.org/2001/XMLSchema#"

#def node(type, **kwargs):
#   cls = getattr(rif, type)
#   return cls(**kwargs)

def node(type, **kwargs):
    return AST.Node( (RIFNS, type), **kwargs)

def iri(part1, part2=""):
   """node('IRI', RIFNS+"local"
   """
   return node('IRI', text=(part1+part2))

RIF_IRI= iri(RIFNS, "iri")

tokens = mps_lex.tokens

precedence = (

    # Stop warning me about shift/reduce conflicts on the
    # empty production -- it can't matter which way they are
    # resolved....

    # Logical operators
    ('left', 'KW_Then', 'KW_If'),
    ('nonassoc', 'COLONDASH'),
    ('nonassoc', 'IMPLIES'),
    ('left', 'KW_Or'),
    ('left', 'KW_And'),
    ('right', 'KW_Neg'),
    ('right', 'KW_Naf'),

    # term->formula operators -- shouldn't really occur in
    # practice, but we don't want the parser to complain
    ('nonassoc', 'EQUALS'),
    ('nonassoc', 'LT', 'LE', 'GT', 'GE'),
    ('nonassoc', 'HASH', 'KW_InstanceOf'),
    ('nonassoc', 'HASHHASH', 'KW_SubclassOf'),

    # Arithmetic Operators
    ('left', 'PLUS', 'MINUS'),
    ('left', 'STAR', 'SLASH'),
#    ('right', 'UMINUS'),            # Unary minus operator


    # Not operators, but %prec tags on rules
    ('left', 'EMPTY'),     # shouldn't affect anything
    ('left', 'DECL'),      # shouldn't affect anything
    ('left', 'META'),      # well, where should this be?

)

def default_action(t):
    print "===="
    for i in t:
        print type(i)
    if len(t) == 0:
        return
    elif len(t) == 1:
        t[0] = t[1]
    else:
        t[0] = [x for x in t[1:]]
    #raise RuntimeError('not implemented')

################################################################
#CUT1
################################################################


################################################################
#CUT2
################################################################

def p_error(t):
   if t is None:
      raise error.ParserError(0, 0)
   else:
      raise error.ParserError(t.lineno, t.lexpos)


# Build the grammar

parser = yacc.yacc(outputdir="mps_ply_generated")
#parser = yacc.yacc()
parser.my_base = None
parser.prefix_map = rif.PrefixMap()
#print 'parser generation done'
#print 

def parse(str):

   try:
      result = parser.parse(str, debug=1, lexer=mps_lex.lexer)
      # strictly speaking, neither of these is part of the resulting
      # abstract document, but we do want to keep them and pass them 
      # along, for user happiness (ie nice qnames).
      ####result._base = parser.my_base
      ####result._prefix_map = parser.prefix_map
      return result
   except error.ParserError, e:
      e.input_text = str
      raise e
   except lex.LexError, e:
      raise error.LexerError(ps_lex.lexer.lineno,
                             len(str) - len(e.text),
                             input_text = str)

class Plugin (plugin.InputPlugin):
   """RIF Presentation Syntax"""

   id="mps_in"
   spec='http://www.w3.org/TR/2008/WD-rif-bld-20080730/#EBNF_Grammar_for_the_Presentation_Syntax_of_RIF-BLD'

   def parse(self, str):
      return parse(str)

plugin.register(Plugin)

if __name__ == "__main__":

   import sys
   s = sys.stdin.read()
   result = None
   try:
      result = parse(s)
   except error.SyntaxError, e:
      print 
      print "syntax error, line %d, col %d, %s" % (e.line, e.col, getattr(e, 'msg', 'no msg'))
      print e.illustrate_position()

   if result:
      print `result`


   #>>> with open('/tmp/workfile', 'r') as f:
   #...     read_data = f.read()
   #
   #>>> for line in f:
   #        print line,
