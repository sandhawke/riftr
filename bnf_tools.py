#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

Should this be a transformative plugin
      --bnfmod or some such?

Do this stuff with some sort of rules...?

(XSTL?  RIF?  ...

"""

import re
import htmlentitydefs

import AST


################################################################

class TokenSet:

    def __init__(self):
        self.token_name = {}
        self.count = 0

    def ingest(self, grammar):
        """Run through a grammar, converting the literals into token
        references, and build up this TokenSet.
        """
        return AST.map(str_to_tok, grammar, self)

    def get_name(self, text):
        try:
            return self.token_name[text]
        except KeyError:
            if is_word(text):
                name = text
            else:
                name_parts = []
                for char in text:
                    name_parts.append(char_name(char).upper())
                name = "_".join(name_parts)
                #self.count += 1
                #name = "tok_%03d" % self.count
                assert is_word(name)
            self.token_name[text] = name
            return name

    def for_lex(self):
        s = ""
        r = ""
        tokens = []
        for (text, name) in self.token_name.items():
            if is_word(text):
                r += "reserved['%-15s = '%s'\n" % (text+"']", name)
            else:
                s += "t_%-15s = re.escape(%s)\n" % (name, `text`)
                tokens.append(name)
        result = ""
        result += r
        result += "\n"
        result += s
        result += "\n"
        result += "tokens.extend(['"+"', '".join(tokens) +"'])"
        return result

word_pat = re.compile(r'''^[a-zA-Z_][a-zA-Z_0-9]*$''')
def is_word(text):
    m = word_pat.match(text)
    return m is not None

def str_to_tok(node, tokens):
    
    if is_type(node, "Literal"):
        name = tokens.get_name(node.text)
        node = AST.Node(("", "Reference"), name=name)
    
    return node


char_names = {
     ')': 'rparen', 
     '(': 'lparen', 
     '*': 'star', 
     '/': 'slash', 
     '-': 'dash', 
     '+': 'plus', 
     '#': 'hash', 
     '=': 'equals', 
     ':': 'colon', 
     ']': 'rbracket', 
     '[': 'lbracket', 
     '}': 'lbrace', 
     '{': 'rbrace', 
     '.': 'dot', 
     ';': 'semi', 
     ',': 'comma', 
    }

def char_name(char):
    
    try:
        return htmlentitydefs.codepoint2name[ord(char)]
    except KeyError:
        pass

    if char.isalpha():
        return char
    
    if char.isdigit():
        return "DIGIT"+char
    
    try:
        return char_names[char]
    except KeyError:
        pass

    n = "chr%d" % ord(char)
    print "     '%s': '', " % char
    char_names[char] = n
    return char_names[char]

################################################################    

def is_type(node, type):
    
    return getattr(node, "_type", (None, None))[1] == type

def convert_to_yacc_form(node):

    node = AST.map(convert_Alt_to_AltN, node)
    node = AST.map(convert_AltN_to_branches, node)

    #node = node._transform(convert_Seq_to_SeqN)
    

    # disallow nested Alt

def convert_Alt_to_AltN(node):

    if is_type(node, "Alt"):
        exprs = []
        if is_type(node.left, "AltN"):
            exprs.extend(node.left.exprs)
        else:
            exprs.append(node.left)

        if is_type(node.right, "AltN"):
            exprs.extend(node.right.exprs)
        else:
            exprs.append(node.right)
        return AST.Node(('', 'AltN'), exprs=exprs)
    else:
        return node

def convert_AltN_to_branches(node):

    if is_type(node, "Production"):
        if is_type(node.expr, 'AltN'):
            node.branches = node.expr.exprs
        else:
            node.branches = [node.expr]
    return node

        


