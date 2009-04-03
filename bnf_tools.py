#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""


Do this stuff with some sort of rules...?

(XSTL?  RIF?  ...)

"""

import re
import copy
import htmlentitydefs

import AST
import plugin


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
                # not a good idea to just use it, bare, because it's
                # likely to conflict with some non-terminals
                name = "kw_"+text
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
        t = ""
        for (text, name) in self.token_name.items():
            if is_word(text):
                r += "reserved['%-15s = '%s'\n" % (text+"']", name)
            else:
                s += "t_%-15s = re.escape(%s)\n" % (name, `text`)
                t += "tokens.append('%s')\n" % name
        result = ""
        result += r
        result += "\n"
        result += s
        result += "\n"
        result += t
        result += "\n"
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
     '|': 'vbar',
     '{': 'rbrace', 
     '.': 'dot', 
     ';': 'semi', 
     ',': 'comma', 
     '?': 'question', 
     '<': 'lt', 
     '>': 'gt', 
     '%': 'percent',
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
    # print "     '%s': '', " % char
    char_names[char] = n
    return char_names[char]

################################################################    

def is_type(node, type):
    
    return getattr(node, "_type", (None, None))[1] == type

def convert_to_yacc_form(root):

    additions = []
    root = AST.map(convert_plus, root, additions)
    root = AST.map(convert_star, root, additions)
    root = AST.map(convert_optional, root, additions)
    for p in additions:
        root.productions.append(p)

    root = AST.map(convert_Alt_to_AltN, root)
    root = AST.map(convert_AltN_to_branches, root)


    # disallow nested Alt

class Plugin (plugin.TransformPlugin) :
    """Convert (arbitrary) grammars to yacc-style grammars.  Kind of like converting logical formula to Conjunctive Normal Form.

    """
    id = "to_yacc"

    def transform(self, root):
        convert_to_yacc_form(root)
        return root

plugin.register(Plugin)

def convert_plus(node, additions):
    
    if is_type(node, 'Plus'):
        name = "_plus_gen_%d" % len(additions)
        e = AST.Node(('', 'Alt'), 
                     left=copy.deepcopy(node.expr),
                     right=AST.Node(('', 'Seq'),
                                    left=AST.Node(('','Reference'),
                                                  name=name),
                                    right=copy.deepcopy(node.expr)
                                    )
                     )
        
        additions.append(AST.Node(('', 'Production'), name=name, expr=e))
        node = AST.Node(('', 'Reference'), name=name)
    return node

def convert_star(node, additions):
    
    if is_type(node, 'Star'):
        name = "_star_gen_%d" % len(additions)
        e = AST.Node(('', 'Alt'), 
                     left=AST.Node(('','Reference'), name='EMPTY'),
                     right=AST.Node(('', 'Seq'),
                                    left=AST.Node(('','Reference'),
                                                  name=name),
                                    right=copy.deepcopy(node.expr)
                                    )
                     )
        
        additions.append(AST.Node(('', 'Production'), name=name, expr=e))
        node = AST.Node(('', 'Reference'), name=name)
    return node


def convert_optional(node, additions):
    
    if is_type(node, 'Optional'):
        name = "_optional_gen_%d" % len(additions)
        e = AST.Node(('', 'Alt'), 
                     left=AST.Node(('','Reference'), name='EMPTY'),
                     right=copy.deepcopy(node.expr)
                     )
        
        additions.append(AST.Node(('', 'Production'), name=name, expr=e))
        node = AST.Node(('', 'Reference'), name=name)
    return node


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

        


