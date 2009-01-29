#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-

import sys
import re

token_for = {
    '->': 'ARROW',
    '(*': 'LMETA',
    '*)': 'RMETA',
    '"': 'DQUOTE',
    '"^^': 'DQUOTEHATHAT',
    '##': 'HASHHASH',
    '#': 'HASH',
    '(': 'LPAREN',
    ')': 'RPAREN',
    ':-': 'COLONDASH',
    '=': 'EQUALS',
    '?': 'QUESTION',
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
    '[': 'LBRACKET',
    ']': 'RBRACKET',
}


tcount = 0

def tok(match):
    ''' Replace each single-quoted-strings with a new token '''
    global token_for
    global tcount

    s = match.group(1)

    try:
        return token_for[s]
    except KeyError:
        key = "tk%d" % tcount
        tcount += 1
        token_for[s] = key
        return key

lit = re.compile("'([^']*)'")

def handle(s):
    (key, rest) = s.split(' ', 1)
    s = lit.sub(tok, s)
    print "def p_%s(t):\n   '''%s '''\n   pass\n\n" % (key, s)

p = []
for line in sys.stdin:
    line = line.strip()
    if line.startswith("#"):
        continue
    if line == "":
        handle("\n".join(p))
        p = []
        continue
    p.append(line)
    

print
print "# Kleene star (*) expansion productions"
for x in sorted(('Prefix', 'Import', 'RULE_or_Group', 'Frame',
          'Name_arrow_TERM', 'ATOMIC', 'FORMULA', 'TERM', 'Var',
          'TERM_arrow_TERM')):
    handle("%s_star : %s_star %s \n    |" % (x,x,x))

print
print "# Kleene plus (+) expansion productions"
for x in ('Var',):
    handle("%s_plus : %s_plus %s \n    | %s" % (x,x,x,x))

print
print "# Kleene opt (?) expansion productions"
for x in sorted(('IRIMETA', 'IRICONST', 'Base', 'Group', 'PROFILE', 
                 'Frame_or_AndFrame')):
    handle("%s_opt : %s \n    |" % (x, x))

#  (used at first, with new grammar)
# print "Tokens: ", token_for

print "tokens = ("
for (key, value) in sorted(token_for.items()):
    print "   %-16s,  # stands for text '%s'" % (`value`, key)
print "   )"

print " "
print "# For the lexer..."
print " "
for (key, value) in sorted(token_for.items()):
    print "t_%-16s = r%s" % (value, `key`)
