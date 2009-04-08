#!/usr/bin/env python2.5
#      -*-mode: python -*-    -*- coding: utf-8 -*-

"""

BliNdFold (in theory) provides generalized parse() and serialize()
methods, converting between strings and ASTs, driven by an annotated
grammar.

It uses PLY for the actual parsing.  

This is another attempt at something I worked on long, long ago.
http://www.w3.org/2001/06/blindfold/grammar

"""
__version__="unknown"


import ply.yacc
import ply.lex

import blindfold_lex as mylex

from debugtools import debug

import AST2
import plugin
import error
import ply_out

NS = "http://www.w3.org/2009/02/blindfold/ns#"

def node(type, **kwargs):
    debug('blindfold', 'new node', type)
    n = AST2.Instance(NS+type)
    for (k,v) in kwargs.items():
        debug('blindfold', '...', k, '=', v)
        if v is None:
            continue
        if isinstance(v, basestring):
            v = AST2.string(v)
        debug('blindfold', '... setattr', n, NS+k, v)
        setattr(n, NS+k, v)
    return n

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
        t[0] = AST2.Sequence(items=[x for x in t[1:]])
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
   t[0] = t[1] + AST2.Sequence(items=[t[2]])
def p_production_star_2(t):
   '''production_star : EMPTY'''
   t[0] = AST2.Sequence(items=[])



# GENERATED CODE FOR '_plus' (REPEAT 1+) PRODUCTION
def p_WORD_plus_1(t):
   '''WORD_plus : WORD_plus WORD  '''
   t[0] = t[1] + AST2.Sequence(items=[t[2]])
def p_WORD_plus_2(t):
   '''WORD_plus : WORD '''
   t[0] = AST2.Sequence(items=[t[1]])



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

def parse(input_text):

   parts = input_text.split('\n%%\n')
   if len(parts) == 1:
       lex_extra = ""
       yacc_extra = ""
   elif len(parts) == 3:
       (input_text, lex_extra, yacc_extra) = parts
   else:
       raise RuntimeError, "unexpected number of %% parts: %d"%len(parts)

   try:
      result = parser.parse(input_text, debug=1, lexer=mylex.lexer)
      # strictly speaking, neither of these is part of the resulting
      # abstract document, but we do want to keep them and pass them 
      # along, for user happiness (ie nice qnames).
      ####result._base = parser.my_base
      ####result._prefix_map = parser.prefix_map
      result.lex_extra = AST2.string(lex_extra)
      result.yacc_extra = AST2.string(yacc_extra)
      return result
   except error.ParserError, e:
      e.input_text = input_text
      raise e
   except ply.lex.LexError, e:
      raise error.LexerError(mylex.lexer.lineno,
                             len(input_text) - len(e.text),
                             input_text = input_text)

class Plugin (plugin.InputPlugin):
   """Read in an annotated BNF grammar"""

   id='blindfold_in'

   def parse(self, input_text):
      return parse(input_text)

plugin.register(Plugin)


class Plugin2 (plugin.InputPlugin):
   """Read in data using the provided annotated BNF grammar"""

   id='blindfold'
   
   options = [
       plugin.Option('grammar', 'Location of the grammar to use to guide parsing', 
                     ),
       ]

   def __init__(self, grammar):
       self.grammar_location=grammar

   def parse(self, input_text):
       
       # We don't yet have smarts to prevent repeated generation.  Caching
       # of .pyc files will be important to have, some day soon.

       # parse the grammar
       grammar_stream = open(self.grammar_location, "r")
       grammar_text = grammar_stream.read()
       grammar = parse(grammar_text)

       # generate the python code
       module_name = "bnf_out_1"
       python_code_file = module_name+".py"
       out_stream = open(python_code_file, "w")
       generator = ply_out.Plugin()
       generator.serialize(grammar, out_stream)
       out_stream.close()

       # load and use the resulting python code
       module = __import__(module_name)
       return module.parse(input_text)

plugin.register(Plugin2)




if __name__ == "__main__":

   import sys
   s = sys.stdin.read()
   result = None
   try:
      result = parse(input_text)
   except error.SyntaxError, e:
      print 
      print "syntax error, line %d, col %d, %s" % (e.line, e.col, getattr(e, 'msg', 'no msg'))
      print e.illustrate_position()

   if result:
      print `result`

