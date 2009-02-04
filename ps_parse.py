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
import ps_lex
import plugin

RIFNS = "http://www.w3.org/2007/rif#"
RIF_IRI= rif.IRI(RIFNS+"iri")
RDFNS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
XSDNS = "http://www.w3.org/2001/XMLSchema#"

tokens = ps_lex.tokens

def p_Document(t):
   '''Document  : IRIMETA_opt KW_Document LPAREN Base_opt Prefix_star Import_star Group_opt RPAREN '''
   t[0] = rif.Document(annotation=t[1], base=t[4], prefix=t[5], imports=t[6], payload=t[7])

def p_Base(t):
   '''Base      : KW_Base LPAREN STRING RPAREN '''   
   t.parser.my_base = t[3]
   t[0] = t[3]

def p_Prefix(t):    # BUG?  BARE_IRI is like in BLD, but what about some chars?
   '''Prefix    : KW_Prefix LPAREN LOCALNAME ANGLEBRACKIRI RPAREN 
                | KW_Prefix LPAREN LOCALNAME BARE_IRI RPAREN '''
   short = t[3]
   long = t[4]
   t.parser.prefix_map.add(short, long)
   t[0] = None

def p_Import(t):
   '''Import    : IRIMETA_opt KW_Import LPAREN LOCATION PROFILE_opt RPAREN '''
   location = t[4]
   profile = t[5]
   t[0] = rif.Import(IRI(location), profile)

def p_LOCATION(t):
   '''LOCATION    : ANGLEBRACKIRI
                  | BARE_IRI
                  | EXPANDED_CURIE'''
   t[0] = t[1]

def p_Group(t):
   '''Group     : IRIMETA_opt KW_Group LPAREN RULE_or_Group_star RPAREN '''
   t[0] = rif.Group(annotation=t[1], sentence=t[4])

def p_RULE_1(t):
   '''RULE      : IRIMETA_opt KW_Forall Var_plus LPAREN CLAUSE RPAREN'''
   t[0] = rif.Forall(annotation=t[1], declare=t[3], formula=t[5])

def p_RULE_2(t):
   '''RULE      : CLAUSE '''
   t[0] = t[1]

def p_CLAUSE_1(t):
   '''CLAUSE    : Implies '''
   t[0] = t[1]

def p_CLAUSE_2(t):
   '''CLAUSE    : ATOMIC '''
   t[0] = t[1]



def p_Implies_1(t):
   '''Implies   :  ATOMIC COLONDASH FORMULA'''
   t[0] = rif.Implies(then=t[1], if_=t[3])

def p_Implies_2(t):
   # is the metadata on the AND or the Rule?
   # ...remove IRIMETA_opt
   '''Implies   : KW_And LPAREN ATOMIC_star RPAREN COLONDASH FORMULA '''
   t[0] = rif.Implies(then=rif.And(formula=t[3]), if_=t[6])


def p_PROFILE(t):
   '''PROFILE   : TERM '''
   t[0] = t[1]

def p_FORMULA_1(t):
   '''FORMULA        :  IRIMETA_opt KW_And LPAREN FORMULA_star RPAREN'''
   t[0] = rif.And(annotation=t[1], formula=t[4])
def p_FORMULA_2(t):
   '''FORMULA        :  IRIMETA_opt KW_Or LPAREN FORMULA_star RPAREN'''
   t[0] = rif.Or(annotation=t[1], formula=t[4])
def p_FORMULA_3(t):
   '''FORMULA        :  IRIMETA_opt KW_Exists Var_plus LPAREN FORMULA RPAREN'''
   t[0] = rif.Exists(annotation=t[1], declare=t[3], formula=t[5])
def p_FORMULA_4(t):
   '''FORMULA        :  ATOMIC'''
   t[0] = t[1]
def p_FORMULA_5(t):
   '''FORMULA        :  IRIMETA_opt KW_External LPAREN Atom RPAREN'''
   t[0] = rif.ExternalAtom(annotation=t[1], content=t[4])

#   -- being removed from Spec
#def p_FORMULA_5(t):
#   '''FORMULA        :  IRIMETA_opt KW_External LPAREN Frame RPAREN'''
#   t[0] = rif.


def p_ATOMIC(t):
   '''ATOMIC         : IRIMETA_opt Atom
                     | IRIMETA_opt Equal
                     | IRIMETA_opt Member
                     | IRIMETA_opt Subclass
                     | IRIMETA_opt Frame 
                     '''
   t[0] = t[2]
   t[0].meta = t[1]   #  I think...?   What if it has metadata from inside?

def p_Atom_1(t):
   # was UNITERM
   '''Atom           : Const LPAREN TERM_star RPAREN'''
   t[0] = rif.Atom(op=t[1], args=t[3])

def p_Atom_2(t):
   # was UNITERM
   '''Atom           : Const LPAREN Name_arrow_TERM_plus RPAREN '''
   t[0] = rif.NamedArgsAtom(op=t[1], slot=t[3])

# put in-line
#def p_UNITERM(t):
#   '''UNITERM        : Const LPAREN TERM_star RPAREN 
#                     | Const LPAREN Name_arrow_TERM_plus RPAREN '''
#   pass


def p_Equal(t):
   '''Equal          : TERM EQUALS TERM '''
   t[0] = rif.Equal(left=t[1], right=t[3])


def p_Member(t):
   '''Member         : TERM HASH TERM '''
   t[0] = rif.Member(instance=t[1], class_=t[3])


def p_Subclass(t):
   '''Subclass       : TERM HASHHASH TERM '''
   t[0] = rif.Subclass(sub=t[1], super=t[3])


def p_Frame(t):
   '''Frame          : TERM LBRACKET TERM_arrow_TERM_star RBRACKET '''
   t[0] = rif.Frame(object=t[1], slot=t[3])

def p_TERM_1(t):
   '''TERM           : IRIMETA_opt Const
                     | IRIMETA_opt Var
                     | IRIMETA_opt Expr '''
   t[0] = t[2]
   t[0].meta = t[1]   #  I think...?   What if it has metadata from inside?
   
def p_TERM_2(t):
   '''TERM           : IRIMETA_opt KW_External LPAREN Expr RPAREN '''
   t[0] = rif.ExternalExpr(annotation=t[1], content=t[4])

# was UNITERM
def p_Expr_1(t):
   '''Expr           : Const LPAREN TERM_star RPAREN '''
   t[0] = rif.Expr(op=t[1], args=t[3])

def p_Expr_2(t):
   '''Expr           : Const LPAREN Name_arrow_TERM_plus RPAREN '''
   t[0] = rif.NamedArgsExpr(op=t[1], slot=t[3])

def p_Const_1(t):
   '''Const          : CONSTSHORT '''
   t[0] = t[1]

def p_Const_2(t):
   '''Const          : STRING_HAT_HAT SYMSPACE '''
   t[0] = rif.Const(lexrep=t[1], datatype=rif.IRI(t[2]))

# MINE
def p_CONSTSHORT_1(t):
   '''CONSTSHORT    : STRING'''
   t[0] = rif.Const(datatype=rif.IRI(XSDNS+"string"), lexrep=t[1])
def p_CONSTSHORT_2(t):
   '''CONSTSHORT    : INTEGER'''
   t[0] = rif.Const(datatype=rif.IRI(XSDNS+"integer"), lexrep=t[1])
def p_CONSTSHORT_3(t):
   '''CONSTSHORT    : DECIMAL'''
   t[0] = rif.Const(datatype=rif.IRI(XSDNS+"decimal"), lexrep=t[1])
def p_CONSTSHORT_4(t):
   '''CONSTSHORT    : ANGLEBRACKIRI
                    | BARE_IRI
                    | EXPANDED_CURIE'''
   t[0] = rif.Const(datatype=RIF_IRI, lexrep=t[1])


def p_Var(t):
   '''Var            : QUESTION STRING 
                     | QUESTION LOCALNAME '''
   t[0] = rif.Var(name=t[2])



def p_SYMSPACE(t):
   '''SYMSPACE       : ANGLEBRACKIRI
                     | EXPANDED_CURIE '''
   t[0] = t[1]


# And "EXPANDED_CURIE" has the same parse-value as the
# ANGLEBRACKIRI you could use in the same place, namely
# just the IRI as a string.
def p_EXPANDED_CURIE(t):
   '''EXPANDED_CURIE : CURIE'''
   (prefix, local_part) = t[1]
   try:
      long = t.parser.prefix_map.get_long(prefix)
   except KeyError:
      raise error.ParserError(t.lexer.lineno, t.lexer.lexpos,
          message=("QName prefix %s used but not declared" % `prefix`))
   t[0] = long + local_part 

def p_IRICONST_1(t):
   '''IRICONST       : ANGLEBRACKIRI
                     | EXPANDED_CURIE'''
   t[0] = rif.Const(datatype=RIF_IRI, lexrep=t[1])
def p_IRICONST_2(t):
   '''IRICONST       : STRING_HAT_HAT SYMSPACE'''
   t[0] = rif.Const(datatype=rif.IRI(t[2]), lexrep=t[1])
   require_iri(t)

def require_iri(t):
   if t[0].datatype == RIF_IRI:
      pass
   else:
      raise error.ParserError(t.lexer.lineno, t.lexer.lexpos, 
           message="Non-IRI Const given where only IRI Const is allowed; datatype=%s" % `t[0].datatype.text`)

def p_IRIMETA_opt_1(t):
   '''IRIMETA_opt     : LMETA RMETA '''
   pass
def p_IRIMETA_opt_2(t):
   '''IRIMETA_opt     : LMETA IRICONST RMETA '''
   t[0] = rif.Annotation(iri=t[2], sentence=None)
def p_IRIMETA_opt_3(t):
   '''IRIMETA_opt     : LMETA IRICONST KW_And LPAREN Frame_star RPAREN RMETA '''
   t[0] = rif.Annotation(iri=t[2], sentence=rif.And(formula=t[5]))
# These next two are tricky; we need both of them to work around the
# ambiguity here.
def p_IRIMETA_opt_4(t):
   '''IRIMETA_opt     : LMETA IRICONST LBRACKET TERM_arrow_TERM_star RBRACKET RMETA '''
   t[0] = rif.Annotation(sentence=rif.Frame(object=t[2], slot=t[4]))
def p_IRIMETA_opt_5(t):
   '''IRIMETA_opt     : LMETA TERM LBRACKET TERM_arrow_TERM_star RBRACKET RMETA '''
   t[0] = rif.Annotation(sentence=rif.Frame(object=t[2], slot=t[4]))
def p_IRIMETA_opt_6(t):
   '''IRIMETA_opt     : LMETA IRICONST TERM LBRACKET TERM_arrow_TERM_star RBRACKET  RMETA'''
   t[0] = rif.Annotation(iri=t[2], sentence=rif.Frame(object=t[3], slot=t[5]))

# This rule produces all our shift/reduce conflicts.   Sigh.
# Because there are several places you could put meta, there are
# several different ways to have it be missing -- to use this rule.
# These should be totally harmless.
def p_IRIMETA_opt_7(t):
   '''IRIMETA_opt    :  '''
   pass


def p_TERM_arrow_TERM(t):
   '''TERM_arrow_TERM : TERM ARROW TERM '''
   t[0] = rif.Slot(key=t[1], value=t[3])


def p_RULE_or_Group(t):
   '''RULE_or_Group : RULE
                    | Group '''
   t[0] = t[1]


def p_Name_arrow_TERM(t):
   '''Name_arrow_TERM : NAME_ARROW TERM '''
   t[0] = rif.Slot(key=t[1], value=t[3])


#def p_Frame_or_AndFrame_1(t):
#   '''Frame_or_AndFrame : Frame'''
#   t[0] = t[1]
#
#def p_Frame_or_AndFrame_2(t):
#   '''Frame_or_AndFrame : KW_And LPAREN Frame_star RPAREN '''
#   t[0] = rif.And(formula=t[3])


# Kleene star (*) expansion productions
def build_list(t):
   """Used at the action for our standard "star" productions
   """
   if (len(t)>1):
      t[0] = t[1] + [t[2]]
   else:
      t[0] = []


def p_ATOMIC_star(t):
   '''ATOMIC_star : ATOMIC_star ATOMIC 
    | '''
   build_list(t)

def p_FORMULA_star(t):
   '''FORMULA_star : FORMULA_star FORMULA 
    | '''
   build_list(t)


def p_Frame_star(t):
   '''Frame_star : Frame_star Frame 
    | '''
   build_list(t)

def p_Import_star(t):
   '''Import_star : Import_star Import 
                  | '''
   build_list(t)

def p_Name_arrow_TERM_plus(t):
   '''Name_arrow_TERM_plus : Name_arrow_TERM_plus Name_arrow_TERM 
                           | Name_arrow_TERM '''
   build_list(t)


def p_Prefix_star(t):
   '''Prefix_star : Prefix_star Prefix 
                  | '''
   build_list(t)

def p_RULE_or_Group_star(t):
   '''RULE_or_Group_star : RULE_or_Group_star RULE_or_Group 
                         | '''
   build_list(t)


def p_TERM_star(t):
   '''TERM_star : TERM_star TERM 
    | '''
   build_list(t)


def p_TERM_arrow_TERM_star(t):
   '''TERM_arrow_TERM_star : TERM_arrow_TERM_star TERM_arrow_TERM 
    | '''
   build_list(t)


# Kleene plus (+) expansion productions
def p_Var_plus(t):
   '''Var_plus : Var_plus Var 
    | Var '''
   if (len(t)>2):
      t[0] = t[1] + [t[2]]
   else:
      t[0] = [t[1]]


# Kleene opt (?) expansion productions
def p_Base_opt(t):
   '''Base_opt : Base 
    | '''
   if (len(t)>1):
      t[0] = t[1]

#def p_Frame_or_AndFrame_opt(t):
#   '''Frame_or_AndFrame_opt : Frame_or_AndFrame 
#    | '''
#   if (len(t)>1):
#      t[0] = t[1]

def p_Group_opt(t):
   '''Group_opt : Group 
    | '''
   if (len(t)>1):
      t[0] = t[1]

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
   if len(t)>1:
      t[0] = t[1]
   


################################################################

def p_error(t):
   if t is None:
      raise error.ParserError(0, 0)
   else:
      raise error.ParserError(t.lineno, t.lexpos)


# from PLY docs
def find_column(input,pos):
    i = pos
    while i > 0:
        if input[i] == '\n': break
        i -= 1
    column = (pos - i)+1
    return column

# Build the grammar

parser = yacc.yacc(outputdir="ps_ply_generated")
parser.my_base = None
parser.prefix_map = rif.PrefixMap()

def parse(str):

   try:
      result = parser.parse(str, debug=0, lexer=ps_lex.lexer)
      # strictly speaking, neither of these is part of the resulting
      # abstract document, but we do want to keep them and pass them 
      # along, for user happiness (ie nice qnames).
      result._base = parser.my_base
      result._prefix_map = parser.prefix_map
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

   id="ps"
   spec='http://www.w3.org/TR/2008/WD-rif-bld-20080730/#EBNF_Grammar_for_the_Presentation_Syntax_of_RIF-BLD'

   def parse(self, str):
      return parse(str)

plugin.register(Plugin())


if __name__ == "__main__":

   import sys
   s = sys.stdin.read()
   result = None
   try:
      result = parse(s)
   except error.SyntaxError, e:
      print 
      print "syntax error, line %d, col %d, %s" % (e.line, e.col, e.msg)
      print e.illustrate_position()

   if result:
      print result.as_ps()


   #>>> with open('/tmp/workfile', 'r') as f:
   #...     read_data = f.read()
   #
   #>>> for line in f:
   #        print line,
