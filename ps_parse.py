#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

TODO:
   runtime --debug
   runtime --start_symbol


"""

import sys
sys.path.insert(0,"/usr/share/python-support/python-ply/")

import ply.yacc as yacc

from objects import *

import ps_lex

tokens = ps_lex.tokens


def p_Document(t):
   '''Document  : IRIMETA_opt KW_Document LPAREN Base_opt Prefix_star Import_star Group_opt RPAREN '''
   t[0] = Document(meta=t[1], base=t[4], prefix=t[5], imports=t[6], group=t[7])

def p_Base(t):
   '''Base      : KW_Base LPAREN STRING RPAREN '''   
   pass


def p_Prefix(t):    # BUG?  BARE_IRI is like in BLD, but what about some chars?
   '''Prefix    : KW_Prefix LPAREN LOCALNAME ANGLEBRACKIRI RPAREN 
                | KW_Prefix LPAREN LOCALNAME BARE_IRI RPAREN '''
   pass


def p_Import(t):
   '''Import    : IRIMETA_opt KW_Import LPAREN ANGLEBRACKIRI PROFILE_opt RPAREN '''
   pass


def p_Group(t):
   '''Group     : IRIMETA_opt KW_Group LPAREN RULE_or_Group_star RPAREN '''
   pass

def p_RULE(t):
   '''RULE      : IRIMETA_opt KW_Forall Var_plus LPAREN CLAUSE RPAREN
                | CLAUSE '''
   pass

def p_CLAUSE(t):
   '''CLAUSE    : Implies
                | ATOMIC '''
   pass


# GRAMMAR BUG: there was an IRIMETA_opt here, but it was ambiguous with the
# one on the ATOMIC
def p_Implies(t):
   '''Implies   : ATOMIC COLONDASH FORMULA
                | IRIMETA_opt KW_And LPAREN ATOMIC_star RPAREN COLONDASH FORMULA '''
   pass


def p_PROFILE(t):
   '''PROFILE   : TERM '''
   pass


def p_FORMULA(t):
   '''FORMULA        : IRIMETA_opt KW_And LPAREN FORMULA_star RPAREN
                     | IRIMETA_opt KW_Or LPAREN FORMULA_star RPAREN
                     | IRIMETA_opt KW_Exists Var_plus LPAREN FORMULA RPAREN
                     | ATOMIC
                     | IRIMETA_opt KW_External LPAREN Atom RPAREN
                     '''
   # taken out, I think:   | IRIMETA_opt KW_External LPAREN Frame RPAREN '''
   pass


def p_ATOMIC(t):
   '''ATOMIC         : IRIMETA_opt KW_Atom Atom
                     | IRIMETA_opt Equal
                     | IRIMETA_opt Member
                     | IRIMETA_opt Subclass
                     | IRIMETA_opt Frame '''
   pass


def p_Atom(t):
   '''Atom           : UNITERM '''
   pass


def p_UNITERM(t):
   '''UNITERM        : Const LPAREN TERM_star RPAREN 
                     | Const LPAREN Name_arrow_TERM_plus RPAREN '''
   pass


def p_Equal(t):
   '''Equal          : TERM EQUALS TERM '''
   pass


def p_Member(t):
   '''Member         : TERM HASH TERM '''
   pass


def p_Subclass(t):
   '''Subclass       : TERM HASHHASH TERM '''
   pass


def p_Frame(t):
   '''Frame          : TERM LBRACKET TERM_arrow_TERM_star RBRACKET '''
   pass


def p_TERM(t):
   '''TERM           : IRIMETA_opt Const
                     | IRIMETA_opt Var
                     | IRIMETA_opt Expr
                     | IRIMETA_opt KW_External LPAREN Expr RPAREN '''
   pass


def p_Expr(t):
   '''Expr           : UNITERM '''
   pass


def p_Const(t):
   '''Const          : STRING_HAT_HAT SYMSPACE
                     | CONSTSHORT '''
   pass

# MINE
def p_CONSTSHORT(t):
   '''CONSTSHORT    : STRING
                    | NUMBER
                    | ANGLEBRACKIRI
                    | BARE_IRI
                    | CURIE  '''
   #   the ANGLEBRACKIRI/CURIE is needed for import-profiles
   #       (among other things.   it's short for the rif:iri symspace)
   pass



#def p_Name(t):
#   '''Name           : STRING
#                     | LOCALNAME '''
#   pass


def p_Var(t):
   '''Var            : QUESTION STRING 
                     | QUESTION LOCALNAME '''
   pass


def p_SYMSPACE(t):
   '''SYMSPACE       : ANGLEBRACKIRI
                     | CURIE '''
   pass

# MINE
def p_IRICONST(t):
   '''IRICONST       : ANGLEBRACKIRI
                     | CURIE '''
   pass


def p_IRIMETA_opt(t):
   '''IRIMETA_opt     : LMETA IRICONST Frame_or_AndFrame_opt RMETA 
                      | LMETA Frame_or_AndFrame_opt RMETA  
                      | 
   '''
   pass


def p_TERM_arrow_TERM(t):
   '''TERM_arrow_TERM : TERM ARROW TERM '''
   pass


def p_RULE_or_Group(t):
   '''RULE_or_Group : RULE
                    | Group '''
   pass


def p_Name_arrow_TERM(t):
   '''Name_arrow_TERM : NAME_ARROW TERM '''
   pass


def p_Frame_or_AndFrame(t):
   '''Frame_or_AndFrame : Frame
| KW_And LPAREN Frame_star RPAREN '''
   pass



# Kleene star (*) expansion productions
def p_ATOMIC_star(t):
   '''ATOMIC_star : ATOMIC_star ATOMIC 
    | '''
   pass


def p_FORMULA_star(t):
   '''FORMULA_star : FORMULA_star FORMULA 
    | '''
   pass


def p_Frame_star(t):
   '''Frame_star : Frame_star Frame 
    | '''
   pass


def p_Import_star(t):
   '''Import_star : Import_star Import 
    | '''
   pass


def p_Name_arrow_TERM_plus(t):
   '''Name_arrow_TERM_plus : Name_arrow_TERM_plus Name_arrow_TERM 
                           | Name_arrow_TERM '''
   pass


def p_Prefix_star(t):
   '''Prefix_star : Prefix_star Prefix 
    | '''
   pass


def p_RULE_or_Group_star(t):
   '''RULE_or_Group_star : RULE_or_Group_star RULE_or_Group 
                         | '''
   pass


def p_TERM_star(t):
   '''TERM_star : TERM_star TERM 
    | '''
   pass


def p_TERM_arrow_TERM_star(t):
   '''TERM_arrow_TERM_star : TERM_arrow_TERM_star TERM_arrow_TERM 
    | '''
   pass



# Kleene plus (+) expansion productions
def p_Var_plus(t):
   '''Var_plus : Var_plus Var 
    | Var '''
   pass



# Kleene opt (?) expansion productions
def p_Base_opt(t):
   '''Base_opt : Base 
    | '''
   pass


def p_Frame_or_AndFrame_opt(t):
   '''Frame_or_AndFrame_opt : Frame_or_AndFrame 
    | '''
   pass


def p_Group_opt(t):
   '''Group_opt : Group 
    | '''
   pass


#def p_IRICONST_opt(t):
#   '''IRICONST_opt : IRICONST 
#                   | '''
#  pass

#    integrate it
#def p_IRIMETA_opt(t):
#   '''IRIMETA_opt : IRIMETA 
#                  |          '''
#   pass


def p_PROFILE_opt(t):
   '''PROFILE_opt : PROFILE 
    | '''
   pass


################################################################

class SyntaxError (RuntimeError):

   def __init__(self, line, pos):
      self.line = line
      self.pos = pos

def p_error(t):
   if t is None:
      raise SyntaxError(0, 0)
   else:
      raise SyntaxError(t.lineno, t.lexpos)


# from PLY docs
def find_column(input,pos):
    i = pos
    while i > 0:
        if input[i] == '\n': break
        i -= 1
    column = (pos - i)+1
    return column

# Build the grammar

yacc.yacc()

import sys
s = sys.stdin.read()
result = None
try:
   result = yacc.parse(s, debug=1)
except SyntaxError, e:
   col = find_column(s, e.pos)
   print "syntax error, line %d, col %d" % (e.line, e.pos)
   print "==> "+s.split("\n")[e.line-1]
   print "   "+(" "*col)+"^---- near here"

if result:
   print 'Parse Tree:', result

#>>> with open('/tmp/workfile', 'r') as f:
#...     read_data = f.read()
#
#>>> for line in f:
#        print line,
