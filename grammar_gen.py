#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-

import sys
import re

group = {
    "star" : [],
    "plus" : [],
    "opt" : [],
}

token_for = {
    ';' : 'SEMI',
    '->': 'ARROW',
    '=>': 'IMPLIES',
    '(*': 'LMETA',
    '*)': 'RMETA',
    '"': 'DQUOTE',
    '"^^': 'DQUOTEHATHAT',
    '##': 'HASHHASH',
    '#': 'HASH',
    'InstanceOf': 'KW_InstanceOf',
    'SubclassOf': 'KW_SubclassOf',

    # total hack doing this here...
    '(': 'lparen',
    'hack-space-lparen': 'SPACE_LPAREN',
    'hack-nospace-lparen': 'NOSPACE_LPAREN',

    ')': 'RPAREN',
    ':-': 'COLONDASH',
    '=': 'EQUALS',
    '?': 'QUESTION',
    'If': 'KW_If',
    'Then': 'KW_Then',
    'True': 'KW_True',
    'False': 'KW_False',
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
    'Alias': 'KW_Alias',
    'Local': 'KW_Local',
    'Include': 'KW_Include',
    '[': 'LBRACKET',
    ']': 'RBRACKET',
    '{': 'LBRACE',
    '}': 'RBRACE',
    '<': 'LT',
    '<=': 'LE',
    '>': 'GT',
    '>=': 'GE',
    '+': 'PLUS',
    '-': 'MINUS',
    '*': 'STAR',
    '/': 'SLASH',
    ',': 'COMMA',
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
        raise RuntimeError, "define a token for %s" % `s`
        key = "tk%d" % tcount
        tcount += 1
        token_for[s] = key
        return key

lit = re.compile("'([^']*)'")

def handle(s, actions=[]):
    if s.strip() == "": return
    s = lit.sub(tok, s)
    (key, rest) = s.split(' ', 1)
    lines = rest.split("\n")
    if len(lines) > 1:
        count = 1
        for line in lines:
            single_production(key, count, after_delim(line), actions)
            count += 1
    else:
        single_production(key, 0, after_delim(s), actions)
    print
    print

def after_delim(s):
    try:
        return s[s.index("|")+1:]
    except ValueError:
        return s[s.index(":")+1:]
    
def single_production(key, count, prods, actions):
    try:
        (prods, comment) = prods.split("#", 1)
        comment = "# " + comment
    except ValueError:
        comment = ""

    pterms = prods.split()
    new_pterms = []
    for term in pterms:

        new = term

        for op in ("star", "plus", "opt"):
            if term.endswith("_"+op):
                base = term[0:-(1+len(op))]
                if base not in group[op]:
                    group[op].append(base)

        for (chr, op)  in ( ("*", "star"),
                            ("+", "plus"), 
                            ("?", "opt") ) :
            if term.endswith(chr):
                base = term[0:-1]
                new = base + "_"+ op
                if base not in group[op]:
                    group[op].append(base)

        new_pterms.append(new)
    if pterms != new_pterms:
        #print >>sys.stderr, "CHANGED:"
        #print >>sys.stderr, pterms
        #print >>sys.stderr, new_pterms
        prods = " " + " ".join(new_pterms)

    try:
        action = actions[count-1]
    except:
        action = general_action(new_pterms)

    if count:
        count_text = "_"+str(count)
    else:
        count_text = ""
    print ("def p_%s%s(t):\n   '''%s :%s '''%s\n   %s" %
           (key, count_text, key, prods, comment, action))    

def general_action(terms):
    if len(terms) == 0:
        return "pass"
    if len(terms) == 1:
        return "t[0] = t[1]"
    cls = ''
    args = []
    for i in range(0, len(terms)):
        term = terms[i]
        if term[0].islower() and term != 'lparen':
            args.append("t[%d]" % (i+1))
        elif term[0].lower().islower():
            if not cls:
                cls = term
                if cls.startswith("KW_"):
                    cls = cls[3:]
    return "t[0] = ['%s', %s]" % (cls, ",".join(args))

p = []
for line in sys.stdin:
    line = line.strip()
    if line.startswith("#"):
        print line
        continue
    if line == "":
        if len(p) == 0:
            print
            continue
        handle("\n".join(p))
        p = []
        continue
    p.append(line)
    

print
print "#########################################################"
print
print "# GENERATED CODE FOR _star, _plus, and _opt PRODUCTIONS"
print
print

for x in group['star']:
    print
    print "# GENERATED CODE FOR '_star' (REPEAT 0+) PRODUCTION"
    handle("%s_star : %s_star %s \n    | EMPTY" % (x,x,x),
           actions=["t[0] = t[1] + [t[2]]",
                    "t[0] = []"
                    ]
           )

for x in group['plus']:
    print
    print "# GENERATED CODE FOR '_plus' (REPEAT 1+) PRODUCTION"
    handle("%s_plus : %s_plus %s \n    | %s" % (x,x,x,x),
           actions=["t[0] = t[1] + [t[2]]",
                    "t[0] = [t[1]]"
                    ]
           )

for x in group['opt']:
    print
    print "# GENERATED CODE FOR '_opt' (occurs 0 or 1) PRODUCTION"
    handle("%s_opt : %s \n    | EMPTY" % (x, x),
           actions=["t[0] = t[1]",
                    "t[0] = t[1]"
                    ]
           )

handle("EMPTY : %prec EMPTY ",
       actions=["t[0] = None"])

#handle("EMPTY :     %prec PRECFLAG1",
#       actions=["t[0] = None"])

#  (used at first, with new grammar)
# print "Tokens: ", token_for

if False:

    print "tokens = ("
    for (key, value) in sorted(token_for.items()):
        print "   %-16s,  # stands for text '%s'" % (`value`, key)
    print "   )"

    print " "
    print "# For the lexer..."
    print " "
    for (key, value) in sorted(token_for.items()):
        print "t_%-16s = r%s" % (value, `key`)
