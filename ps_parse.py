#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

This is (eventually to be) a parser for the the RIF Presentation Syntax.

I'm starting with the ply example parser for ANSI C, and modifying from
there.

"""

import ply.yacc as yacc


"""

- cut and paste grammar from 
  http://www.w3.org/TR/2008/WD-rif-bld-20080730/#EBNF_for_the_Rule_Language

- Change EBNF to BNF

   - replace parenthesized phrases with named phrases, as needed:
       (RULE | Group)                    RULE_or_Group
       (Name '->' TERM)                  Name_arrow_TERM
       (TERM '->' TERM)                  TERM_arrow_TERM
       (Frame | 'And' '(' Frame* ')')    Frame_or_AndFrame

   - replace Kleene operators:
        '* '      '_star '
        '? '      '_opt '
        '+ '      '_plus '

   - add Kleene operator rules (run grammar_gen.py)

- Remove parens...

- Split some disjunctive productions into multiple productions

    (just a random judgement call?)

- Trivial syntax changes

   - left align the text

   - turn "::=" into ":"

   - wrap lines in rule 

         def p_X_N(t):
            'X : ...'
            pass
     
      (where N is branch N -- if there's more than one)

      IE use:
         python grammar_gen.py  < grammar > gend

"""
def p_Document(t):
   '''Document  : IRIMETA_opt KW_Document LPAREN Base_opt Prefix_star Import_star Group_opt RPAREN '''
   pass


def p_Base(t):
   '''Base      : KW_Base LPAREN IRI RPAREN '''
   pass


def p_Prefix(t):
   '''Prefix    : KW_Prefix LPAREN Name IRI RPAREN '''
   pass


def p_Import(t):
   '''Import    : IRIMETA_opt KW_Import LPAREN IRICONST PROFILE_opt RPAREN '''
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


def p_Implies(t):
   '''Implies   : IRIMETA_opt ATOMIC  COLONDASH FORMULA
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
| IRIMETA_opt KW_External LPAREN Frame RPAREN '''
   pass


def p_ATOMIC(t):
   '''ATOMIC         : IRIMETA_opt Atom
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
| Const LPAREN Name_arrow_TERM_star RPAREN '''
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
   '''Const          : DQUOTE UNICODESTRING DQUOTEHATHAT SYMSPACE
| CONSTSHORT '''
   pass


def p_Name(t):
   '''Name           : UNICODESTRING '''
   pass


def p_Var(t):
   '''Var            : QUESTION UNICODESTRING '''
   pass


def p_SYMSPACE(t):
   '''SYMSPACE       : ANGLEBRACKIRI
| CURIE '''
   pass


def p_IRIMETA(t):
   '''IRIMETA        : LMETA IRICONST_opt Frame_or_AndFrame_opt RMETA '''
   pass


def p_TERM_arrow_TERM(t):
   '''TERM_arrow_TERM : TERM ARROW TERM '''
   pass


def p_RULE_or_Group(t):
   '''RULE_or_Group : RULE
| Group '''
   pass


def p_Name_arrow_TERM(t):
   '''Name_arrow_TERM : Name ARROW TERM '''
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


def p_Name_arrow_TERM_star(t):
   '''Name_arrow_TERM_star : Name_arrow_TERM_star Name_arrow_TERM 
    | '''
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


def p_Var_star(t):
   '''Var_star : Var_star Var 
    | '''
   pass



# Kleene plus (+) expansion productions
def p_Var_plus(t):
   '''Var_plus : Var_star Var 
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


def p_IRICONST_opt(t):
   '''IRICONST_opt : IRICONST 
    | '''
   pass


def p_IRIMETA_opt(t):
   '''IRIMETA_opt : IRIMETA 
    | '''
   pass


def p_PROFILE_opt(t):
   '''PROFILE_opt : PROFILE 
    | '''
   pass


tokens = (
   'DQUOTE'        ,  # stands for text '"'
   'DQUOTEHATHAT'  ,  # stands for text '"^^'
   'HASH'          ,  # stands for text '#'
   'HASHHASH'      ,  # stands for text '##'
   'LPAREN'        ,  # stands for text '('
   'LMETA'         ,  # stands for text '(*'
   'RPAREN'        ,  # stands for text ')'
   'RMETA'         ,  # stands for text '*)'
   'ARROW'         ,  # stands for text '->'
   'COLONDASH'     ,  # stands for text ':-'
   'EQUALS'        ,  # stands for text '='
   'QUESTION'      ,  # stands for text '?'
   'KW_And'        ,  # stands for text 'And'
   'KW_Base'       ,  # stands for text 'Base'
   'KW_Document'   ,  # stands for text 'Document'
   'KW_Exists'     ,  # stands for text 'Exists'
   'KW_External'   ,  # stands for text 'External'
   'KW_Forall'     ,  # stands for text 'Forall'
   'KW_Group'      ,  # stands for text 'Group'
   'KW_Import'     ,  # stands for text 'Import'
   'KW_Or'         ,  # stands for text 'Or'
   'KW_Prefix'     ,  # stands for text 'Prefix'
   'LBRACKET'      ,  # stands for text '['
   'RBRACKET'      ,  # stands for text ']'
   )


################################################################

def p_error(t):
    raise RuntimeError

tokens = tokens + (
    'IRI',
    'IRICONST',
    'UNICODESTRING',
    'CONSTSHORT',
    'ANGLEBRACKIRI',
    'CURIE',
)

# Build the grammar

yacc.yacc()

import sys
s = sys.stdin.read()
result = yacc.parse(s)
print 'Parse Tree:', result

#>>> with open('/tmp/workfile', 'r') as f:
#...     read_data = f.read()
#
#>>> for line in f:
#        print line,
