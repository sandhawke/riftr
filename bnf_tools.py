#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""


Do this stuff with some sort of rules...?

(XSTL?  RIF?  ...)

"""

import re
import htmlentitydefs

import AST2
import plugin

NS = "http://www.w3.org/2009/02/blindfold/ns#"

def deepcopy(n):
    return n.deepcopy()

################################################################

class TokenSet:

    def __init__(self):
        self.token_name = {}
        self.count = 0

    def ingest(self, grammar):
        """Run through a grammar, converting the literals into token
        references, and build up this TokenSet.
        """
        return grammar.map_replace(str_to_tok, self)

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
    
    if node.has_type("Literal"):
        name = tokens.get_name(node.text.the.lexrep)
        node = AST2.Instance(("Reference"), name=AST2.string(name))
    
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


def convert_to_yacc_form(root):

    save = AST2.default_namespace
    AST2.default_namespace = NS

    additions = []
    root = root.map_replace(convert_plus, additions)
    root = root.map_replace(convert_star, additions)
    root = root.map_replace(convert_optional, additions)
    #root.productions=AST2.Sequence()
    for p in additions:
        root.productions.the.append(p)

    root = root.map_replace(convert_Alt_to_AltN)
    root = root.map_replace(convert_AltN_to_branches)

    # disallow nested Alt

    save = AST2.default_namespace


class Plugin (plugin.TransformPlugin) :
    """Convert (arbitrary) grammars to yacc-style grammars.  Kind of like converting logical formula to Conjunctive Normal Form.

    """
    id = "to_yacc"

    def transform(self, root):
        convert_to_yacc_form(root)
        return root

plugin.register(Plugin)

def convert_plus(node, additions):
    
    if node.has_type('Plus'):
        name = AST2.string("_plus_gen%d" % len(additions))
        e = AST2.Instance(('Alt'), 
                     left=deepcopy(node.expr.the),
                     right=AST2.Instance(('Seq'),
                                    left=AST2.Instance(('Reference'),
                                                  name=name),
                                    right=deepcopy(node.expr.the)
                                    )
                     )
        
        additions.append(AST2.Instance(('Production'), name=name, expr=e))
        node = AST2.Instance(('Reference'), name=name)
    return node

def convert_star(node, additions):
    
    if node.has_type('Star'):
        name = AST2.string("_star_gen%d" % len(additions))
        e = AST2.Instance(('Alt'), 
                     left=AST2.Instance(('Reference'), name='EMPTY'),
                     right=AST2.Instance(('Seq'),
                                    left=AST2.Instance(('Reference'),
                                                  name=name),
                                    right=deepcopy(node.expr.the)
                                    )
                     )
        
        additions.append(AST2.Instance(('Production'), name=name, expr=e))
        node = AST2.Instance(('Reference'), name=name)
    return node


def convert_optional(node, additions):
    
    if node.has_type('Optional'):
        name = AST2.string("_optional_gen%d" % len(additions))
        e = AST2.Instance(('Alt'), 
                     left=AST2.Instance(('Reference'), name=AST2.string('EMPTY')),
                     right=deepcopy(node.expr.the)
                     )
        
        additions.append(AST2.Instance(('Production'), name=name, expr=e))
        node = AST2.Instance(('Reference'), name=name)
    return node


def convert_Alt_to_AltN(node):

    if node.has_type("Alt"):
        exprs = AST2.Sequence()
        for side in (node.left.the, node.right.the):
            if side.has_type("AltN"):
                exprs.extend(side.exprs.the.items)
            else:
                exprs.append(side)
        return AST2.Instance(('AltN'), exprs=exprs)
    else:
        return node

def convert_AltN_to_branches(node):

    if node.has_type("Production"):
        if node.expr.the.has_type('AltN'):
            node.branches = node.expr.the.exprs.the
        else:
            node.branches = AST2.Sequence([node.expr.the])
    return node

        


