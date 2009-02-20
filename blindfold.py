#!/usr/bin/env python2.5
#      -*-mode: python -*-    -*- coding: utf-8 -*-

"""

BliNdFold (in theory) provides generalized parse() and serialize()
methods, converting between strings and ASTs, driven by an annotated
grammar.

It uses PLY for the actual parsing.  

This is another attempt at something I worked on long ago.
http://www.w3.org/2001/06/blindfold/grammar

"""
__version__="unknown"


import ply.yacc
import ply.lex

import blindfold_lex as mylex

import AST
import plugin
import error

NS = "http://www.w3.org/2009/02/blindfold/ns#"

def node(type, **kwargs):
    return AST.Node( (NS, type), **kwargs)

tokens = mylex.tokens



precedence = (
#    ('right', 'VERTICALBAR'),
    ('right', 'PREC'),
    ('right', 'SEQ'), # associativity doesn't work for %prec
    ('nonassoc', 'COLONCOLON'),
    ('left', 'PLUS', 'STAR', 'QUESTION'),
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


def p_grammar(t):
   '''grammar : production_star '''
   t[0] = node('Grammar', productions=t[1])


def p_production(t):
   '''production : WORD_COLON Aexpr action_opt '''
   t[0] = node('Production', name=t[1], expr=t[2], action=t[3])

# an expr without a vertical bar in it
#
# I'm not sure why setting the precedence on VERTICALBAR doesn't
# do this, but ... it doesn't.
def p_Aexpr_1(t):
   '''Aexpr : Aexpr VERTICALBAR expr '''
   t[0] = node('Alt', left=t[1], right=t[3])
def p_Aexpr_2(t):
   '''Aexpr : expr '''
   t[0] = t[1]

def p_expr_2(t):
   '''expr : LPAREN Aexpr RPAREN '''
   t[0] = t[2]
def p_expr_3(t):
   '''expr : expr expr %prec SEQ'''
   #items = []
   #for tt in (t[1], t[2]):
   #    try:
   #        for i in tt:
   #            items += i
   #    except:
   #        items.append(tt)
   #t[0] = AST.Sequence(items=items)
   t[0] = node('Seq', left=t[1], right=t[2])
def p_expr_4(t):
   '''expr : WORD_COLON_COLON expr %prec COLONCOLON'''
   t[0] = node('Property', property=t[1], expr=t[2])
def p_expr_5(t):
   '''expr : WORD '''
   t[0] = node('Reference', name=t[1])
def p_expr_6(t):
   '''expr : STRING '''
   t[0] = node('Literal', text=t[1])
def p_expr_7(t):
   '''expr : expr PLUS '''
   t[0] = node('Plus', expr=t[1])
def p_expr_8(t):
   '''expr : expr STAR '''
   t[0] = node('Star', expr=t[1])
def p_expr_9(t):
   '''expr : expr QUESTION '''
   t[0] = node('Optional', expr=t[1])
def p_expr_10(t):
   '''expr : expr PREC WORD '''
   t[0] = node('Precedence', expr=t[1], reference=t[3])


def p_action(t):
   '''action : LBRACE WORD_plus RBRACE '''
   t[0] = node('Action', words=t[2])




#########################################################

# GENERATED CODE FOR _star, _plus, and _opt PRODUCTIONS



# GENERATED CODE FOR '_star' (REPEAT 0+) PRODUCTION
def p_production_star_1(t):
   '''production_star : production_star production'''
   t[0] = t[1] + [t[2]]
def p_production_star_2(t):
   '''production_star : EMPTY'''
   t[0] = []



# GENERATED CODE FOR '_plus' (REPEAT 1+) PRODUCTION
def p_WORD_plus_1(t):
   '''WORD_plus : WORD_plus WORD  '''
   t[0] = t[1] + [t[2]]
def p_WORD_plus_2(t):
   '''WORD_plus : WORD '''
   t[0] = [t[1]]



# GENERATED CODE FOR '_opt' (occurs 0 or 1) PRODUCTION
def p_action_opt_1(t):
   '''action_opt : action  '''
   t[0] = t[1]
def p_action_opt_2(t):
   '''action_opt : EMPTY '''
   t[0] = t[1]


def p_EMPTY(t):
   '''EMPTY :   '''
   t[0] = None




################################################################
#CUT2
################################################################

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
      result = parser.parse(str, debug=1, lexer=mylex.lexer)
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
      raise error.LexerError(mylex.lexer.lineno,
                             len(str) - len(e.text),
                             input_text = str)

class Plugin (plugin.InputPlugin):
   """RIF Presentation Syntax"""

   id=__name__
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

