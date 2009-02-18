#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

Lexer for blindfold

(Copied from mps_lex; now modifying...)

"""

import re
import ply.lex as lex

def k(x):
    return x.lower()

reserved = {
#    k('Document'): 'KW_Document',

}

ops = [
#   'COLONCOLON',
#   'COLON',
   'VERTICALBAR',
   'PLUS',
   'STAR',
   'QUESTION',

   ]

delims = [
   'LPAREN'  , 
   'RPAREN'        ,  # stands for text ')'
   'LBRACE'      ,  # stands for text '['
   'RBRACE'      ,  # stands for text ']'
]

t_ignore  = ' \t'

#t_COLON            = r':'
#t_COLONCOLON       = r'::'
t_VERTICALBAR      = r'\|'
t_LPAREN           = r'\('
t_RPAREN           = r'\)'
t_LBRACE           = r'\{'
t_RBRACE           = r'\}'
t_PLUS             = r'\+'
t_STAR             = r'\*'
t_QUESTION         = r'\?'

weird = ['LINE_COMMENT', 'C_COMMENT']

ids = ['STRING', 'WORD', 'WORD_COLON', 'WORD_COLON_COLON', 'PREC']

tokens = ids + delims + ops + weird + reserved.values()

def t_WORD_COLON_COLON(t):
    r'[a-zA-Z_]:?[-a-zA-Z_0-9]*[ \t\n]*::'
    t.lexer.lineno += t.value.count('\n')
    t.value = t.value[:-2].strip()
    return t

def t_WORD_COLON(t):
    r'[a-zA-Z_][-a-zA-Z_0-9]*[ \t\n]*:'
    t.lexer.lineno += t.value.count('\n')
    t.value = t.value[:-1].strip()
    return t

def t_PREC(t):
    r'%prec'
    return t

def t_WORD(t):
    r'[a-zA-Z_][-a-zA-Z_0-9]*'
    return t

def t_STRING(t):
    r'''(("([^"]|\\"|\n)*")|('([^']|\\'|\n)*'))'''
    t.value = t.value[1:-1]
    t.value = t.value.replace(r'\"', '"')
    t.value = t.value.replace(r"\'", "'")
    t.value = t.value.replace(r'\n', '\n')
    t.lexer.lineno += t.value.count('\n')
    return t

##
##  sorta standard stuff
##

def t_LINE_COMMENT(t):
    r'\#[^\n]*\n'
    t.lexer.lineno += t.value.count('\n')
    pass

def t_C_COMMENT(t):
    r'/\*(.|\n)*?\*/'
    t.lexer.lineno += t.value.count('\n')
    pass

def t_error(t):
    pass

def t_NEWLINE(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")
    
#lexer = lex.lex(optimize=1)
lexer = lex.lex(outputdir="ps_ply_generated")
lexer.recognize_keywords = True
lexer.scopes = []    # stack of collections of variable names

def round_trip(s, type):
    try:
        t = token_list(s)
        #print "Tokens:", t
    except ply.lex.LexError, e:
        return False
    #print t[0].__dict__
    if (len(t) == 1 and 
        t[0].type == type and
        t[0].value == s
        ):
        return True
    return False

def token_list(s):
    lexer.input(s)
    tokens = []
    while True:
        tok = lex.token()
        if not tok: break      # No more input
        tokens.append(tok)
    return tokens

def show_types(s):
    for t in token_list(s):
        print t.type,

def demo():
    """
    
    >>> show_types("foo")
    WORD


    """
    import sys

    if len(sys.argv) == 1:
        return
    
    # if we have ANY argument, read stdin....!
    lexer.recognize_keywords = True
    input_text = sys.stdin.read()
    for tok in token_list(input_text):
        print tok
   
if __name__ == "__main__":
    import doctest, sys
    doctest.testmod(sys.modules[__name__])

    demo()
