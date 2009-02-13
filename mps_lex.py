#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

Lexer for MPS...

(Copied from ps_lex; now modifying...)

"""

import re
import ply.lex as lex

def k(x):
    return x.lower()

reserved = {
    k('true'): 'KW_True',
    k('false'): 'KW_False',
    k('if'): 'KW_If',
    k('then'): 'KW_Then',
    k('And'): 'KW_And',
    k('Base'): 'KW_Base',
    k('Document'): 'KW_Document',
    k('Exists'): 'KW_Exists',
    k('External'): 'KW_External',
#    k('ExternalF'): 'KW_ExternalF',
    k('Forall'): 'KW_Forall',
    k('Group'): 'KW_Group',
    k('Import'): 'KW_Import',
    k('Or'): 'KW_Or',
    k('Prefix'): 'KW_Prefix',
    k('Alias'): 'KW_Alias',
    k('Local'): 'KW_Local',
    k('Include'): 'KW_Include',
#    k('Atom'): 'KW_Atom',   # just messing around
#    k('metasep'): 'METASEP',   # just messing around   -- saves two conflicts
}

ops = [
   'HASH'          ,  # stands for text '#'
   'HASHHASH'      ,  # stands for text '##'
   'ARROW'         ,  # stands for text '->'
   'COLONDASH'     ,  # stands for text ':-'
   'EQUALS'        ,  # stands for text '='
   #'QUESTION'      ,  # stands for text '?'

   # NOT IN BLD, but ...?
   'LT',
   'PLUS',
   'MINUS',
 #  'LE',
 #  'GT',
 #  'GE',
   ]

delims = [
   'COMMA'         ,
   'SPACE_LPAREN'  ,  # stands for text '(' after whitespace
   'NOSPACE_LPAREN',  # stands for text '(' after no whitespace
   'LMETA'         ,  # stands for text '(*'
   'RPAREN'        ,  # stands for text ')'
   'RMETA'         ,  # stands for text '*)'
   'LBRACKET'      ,  # stands for text '['
   'RBRACKET'      ,  # stands for text ']'
#   'LBRACE'      ,  # stands for text '['
#   'RBRACE'      ,  # stands for text ']'
]

ids = ['ANGLEBRACKIRI', 'BARE_IRI',
       'STRING_HAT_HAT',
       'STRING', 'INTEGER', 'DECIMAL',
       'NAME_ARROW', 'LOCAL', 'VARNAME',
       'BARE_WORD']

tokens = ids + delims + ops + reserved.values()

def t_BARE_IRI(t):
    # This does double-duty as an IRI and a CURIE; the difference is
    # whether the part before the colon has been declared as a prefix.
    #
    # The syntax is slightly more restrictive than IRI, because we
    # exclude our delimiters (and maybe some operators?).  If you want
    # to use an IRI with these chars in it, just use ANGLEBRACKIRI.
    #
    r'[a-zA-Z_][-a-zA-Z_0-9]*:[^][ \n\t<>()]*'
    return t

def t_NAME_ARROW(t):
    # This lets argument names be barewords, with no parser confusion.
    #
    # Take this out and just make arrow be an operator producing a 
    # Named_Argument if the names become quoted strings / constants.
    r'[a-zA-Z_][-a-zA-Z_0-9]*[ \t\x0c]*->'
    t.value = t.value[0:-2].strip()
    return t

def t_LOCAL(t):
    r'_[-a-zA-Z_0-9]*'
    return t

def t_BARE_WORD(t):
    r'\??[a-zA-Z_][-a-zA-Z_0-9]*'
    if t.value[0] == "?":
        t.value = t.value[1:]
        if t.lexer.recognize_keywords:
            # really means: if the variable must have been already declared
            for scope in t.lexer.scopes:
                if t.value in scope:
                    t.type='VARNAME'
                    return t
            raise lex.LexError('undeclared variable %s used' % t.value)
            # ... else let it be returned as a BARE_WORD to be declared
            # (we don't check that it's being declared as a VARIABLE.)
    if t.lexer.recognize_keywords:
        # change the type to be the appropriate keyword if it's matched,
        # otherwise set it (leave it as) BARE_WORD
        t.type = reserved.get(t.value.lower(),'BARE_WORD') 
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
    r'"([^"]|\"|\n)*"'
    t.value = t.value[1:-1]
    t = t.replace(r'\"', '"')
    t = t.replace(r'\n', '\n')
    return t

def t_INTEGER(t):
    r'\d+'
    return t

def t_DECIMAL(t):
    r'\d+\.\d+'
    return t

# Fancy handling of parens

def test_LPAREN():
    r"""
    >>> show_types("(")
    NOSPACE_LPAREN
    >>> show_types(" (")
    SPACE_LPAREN
    >>> show_types("\n(")
    SPACE_LPAREN
    >>> show_types("0(")
    INTEGER NOSPACE_LPAREN
    >>> show_types("0 (")
    INTEGER SPACE_LPAREN
    >>> show_types("0\t(")
    INTEGER SPACE_LPAREN

    """
    pass


def t_SPACE_LPAREN(t):
    r'[ \t\n\r\f\v]\('
    return t

def t_SPACE(t):
    r'[ \t\n\r\f\v]+'
    pass    # no return value, token discared

def t_NOSPACE_LPAREN(t):
    r'\('
    return t

# alas, this didn't work
#t_SPACE_LPAREN     = r'?<![ \t\n\r\f\v]>\('

#t_DQUOTE           = r'"'
#t_DQUOTEHATHAT     = r'"^^'
t_HASH             = r'\#'
t_HASHHASH         = r'\#\#'
t_COMMA            = r','
t_LMETA            = r'\(\*'
t_RPAREN           = r'\)'
t_RMETA            = r'\*\)'
t_ARROW            = r'->'
t_COLONDASH        = r':-'
t_EQUALS           = r'='
#t_QUESTION         = r'\?'
t_LBRACKET         = r'\['
t_RBRACKET         = r'\]'
#t_LBRACE         = r'\{'
#t_RBRACE         = r'\}'
t_PLUS             = r'\+'
t_MINUS            = r'\-'
t_LT               = r'<'
#t_LE = r'<='
#t_GT = r'>'
#t_GE = r'>='


##
##  sorta standard stuff
##

def t_comment(t):
    r'/\*(.|\n)*?\*/'
    t.lexer.lineno += t.value.count('\n')

def t_error(t):
    pass

#    print "Illegal character %s" % repr(t.value[0])
#    # t.lexer.skip(1)
#    pass
    
foo = 0

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
    BARE_WORD

    >>> token_list("aNd")
    [LexToken(KW_And,'aNd',1,0)]

    >>> lexer.recognize_keywords = False

    >>> token_list("aNd")
    [LexToken(BARE_WORD,'aNd',1,0)]

    >>> token_list("?foo")
    [LexToken(BARE_WORD,'foo',1,0)]

    """
    import sys

    if len(sys.argv) == 1:
        return
    
    # if we have ANY argument, read stdin....!
    input_text = sys.stdin.read()
    for tok in token_list(input_text):
        print tok
   
if __name__ == "__main__":
    import doctest, sys
    doctest.testmod(sys.modules[__name__])

    demo()
