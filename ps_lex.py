#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

Lexer for BLD, not really/totally in line with the spec...

"""

import sys
sys.path.insert(0,"/usr/share/python-support/python-ply/")

import ply.lex as lex

reserved = {
    'And': 'KW_And',
    'Base': 'KW_Base',
    'Document': 'KW_Document',
    'Exists': 'KW_Exists',
    'External': 'KW_External',
    'Forall': 'KW_Forall',
    'Group': 'KW_Group',
    'Import': 'KW_Import',
    'Or': 'KW_Or',
    'Prefix': 'KW_Prefix',
}

ops = [
   'HASH'          ,  # stands for text '#'
   'HASHHASH'      ,  # stands for text '##'
   'ARROW'         ,  # stands for text '->'
   'COLONDASH'     ,  # stands for text ':-'
   'EQUALS'        ,  # stands for text '='
   'QUESTION'      ,  # stands for text '?'

   # NOT IN BLD, but ...?
   'LT',
   'LE',
   'GT',
   'GE',
   ]

delims = [
   'LPAREN'        ,  # stands for text '('
   'LMETA'         ,  # stands for text '(*'
   'RPAREN'        ,  # stands for text ')'
   'RMETA'         ,  # stands for text '*)'
   'LBRACKET'      ,  # stands for text '['
   'RBRACKET'      ,  # stands for text ']'
]

ids = ['CURIE', 'ANGLEBRACKIRI', 
       'STRING_HAT_HAT',
       'STRING', 'NUMBER', 
       'LOCALNAME']

# ISSUE: can the LOCALNAME in XML not contain a space?

tokens = ids + delims + ops + reserved.values()

def t_CURIE(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*:[a-zA-Z_][a-zA-Z_0-9]*'
    t.value = t.value.split(":", 1)
    return t

def t_LOCALNAME(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value,'LOCALNAME')    # Check for reserved words
    return t

def t_ANGLEBRACKIRI(t):
    r'<[^<> ]*>'
    t.value = t.value[1:-1]
    return t

def t_STRING_HAT_HAT(t):
    r'"[^"]*"\^\^'
    t.value = t.value[1:-3]
    return t

def t_STRING(t):
    r'"[^"]*"'
    t.value = t.value[1:-1]
    return t

def t_NUMBER(t):
    r'\d+(\.\d+)?'
    return t

# Completely ignored characters
t_ignore           = ' \t\x0c'

#t_DQUOTE           = r'"'
#t_DQUOTEHATHAT     = r'"^^'
t_HASH             = r'\#'
t_HASHHASH         = r'\#\#'
t_LPAREN           = r'\('
t_LMETA            = r'\(\*'
t_RPAREN           = r'\)'
t_RMETA            = r'\*\)'
t_ARROW            = r'->'
t_COLONDASH        = r':-'
t_EQUALS           = r'='
t_QUESTION         = r'\?'
t_LBRACKET         = r'\['
t_RBRACKET         = r'\]'

t_LE = r'<='
t_LT = r'<'
t_GT = r'>'
t_GE = r'>='


##
##  sorta standard stuff
##

def t_comment(t):
    r'/\*(.|\n)*?\*/'
    t.lexer.lineno += t.value.count('\n')

def t_error(t):
    print "Illegal character %s" % repr(t.value[0])
    # t.lexer.skip(1)
    pass
    
foo = 0

def t_NEWLINE(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")
    
lexer = lex.lex(optimize=1)

# lexer = lex.lex(debug=1)
if __name__ == "__main__":
    lex.runmain(lexer)
