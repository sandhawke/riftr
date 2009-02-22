#!/usr/bin/env python2.5
# -*-mode: python -*-    -*- coding: utf-8 -*-
'''
This is either a PLY LEX/YACC grammar file created by ply_out.py, or
(if it's called ply_template.py) it's the template file used to help create
those files....

'''


import re

import ply.yacc
import ply.lex

import AST
import plugin
import error

tokens = []

reserved = {}

# GENERATED LEX CODE BEGINS HERE
# GENERATED LEX CODE ENDS HERE

tokens.extend(reserved.values())


def t_ID(t):
   r'[a-zA-Z_][a-zA-Z_0-9]*'
   t.type = reserved.get(t.value,'ID')
   return t

def t_COMMENT(t):
   r'\#.*'
   pass
   # No return value. Token discarded

# Define a rule so we can track line numbers
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# A string containing ignored characters (spaces and tabs)
t_ignore  = ' 	'

# Error handling rule
def t_error(t):
    print "Illegal character '%s'" % t.value[0]
    t.lexer.skip(1)

# Build the lexer
lexer = ply.lex.lex(debug=0)



precedence = [ ]

# GENERATED YACC CODE BEGINS HERE
# GENERATED YACC CODE ENDS HERE



def p_error(t):
   if t is None:
      raise error.ParserError(0, 0)
   else:
      raise error.ParserError(t.lineno, t.lexpos)


# Build the grammar

parser = ply.yacc.yacc(outputdir="blindfold_ply_generated")
#parser = yacc.yacc()
parser.my_base = None
#parser.prefix_map = rif.PrefixMap()
#print 'parser generation done'
#print 

def parse(str):

   try:
      result = parser.parse(str, debug=1, lexer=lexer)
      # strictly speaking, neither of these is part of the resulting
      # abstract document, but we do want to keep them and pass them 
      # along, for user happiness (ie nice qnames).
      ####result._base = parser.my_base
      ####result._prefix_map = parser.prefix_map
      return result
   except error.ParserError, e:
      e.input_text = str
      raise e
   except ply.lex.LexError, e:
      raise error.LexerError(lexer.lineno,
                             len(str) - len(e.text),
                             input_text = str)

class Plugin (plugin.InputPlugin):
   """Undocument Syntax"""

   id=__name__
   # spec

   def parse(self, str):
      return parse(str)

# Let's not have it registering itself...    Someone else can do this
# if it's really necessary.
#plugin.register(Plugin)

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

