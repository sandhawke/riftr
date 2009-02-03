#!/usr/bin/env python2.5
# coding: utf-8
"""

This is crufty old code that has been repurposed many times, and not
carefully.  Sorry.

"""

import time
import sys
import os

import html as h

sys.path.insert(0,"/usr/share/python-support/python-ply/")
import ply.yacc as yacc
import ply.lex as lex

import ps_parse
import ps_lex
import xml_in
import rif

#
# GLOBAL VARIABLES
#
# (This is a CGI, we can do this kind of stuff.  Heh.  Maybe someday
# we'll turn this into a class called, um, ... Page? )
#
page = None
class State: pass
state = State()             # in the CGI sense; what we want carried
                            # from click to click via query or post
                            # parameters

mypath = "me"        # should be overrided via CGI

def startPage(title):
    global page
    if page == None:

        print "Content-Type: text/html; charset=utf-8\n"
        page = h.Document()
        page.head.append(h.title(title))
        page.head << h.stylelink("http://validator.w3.org/base.css")


def main_page(input=None, action="PS to PS"):
    global page

    startPage("RIF (Highly Experimental) Demonstration Page")	
    page << h.h2("RIF (Highly Experimental) Demonstration Page")
    page << h.p("This page currently only does translations between RIF XML and RIF PS, but the idea is to have various non-RIF languages supported as well")

    form = h.form(method="GET", class_="f")	
    form << h.h3("Input Text...") 
    if input is None:
        input = default_input()
    form << h.textarea(input,
                       cols="90", rows="20", name="input")
    form << h.br()
    form <<  h.input(type="submit",  name="action", value="PS to PS")
    form <<  h.input(type="submit",  name="action", value="PS to XML")
    form <<  h.input(type="submit",  name="action", value="XML to XML")
    form <<  h.input(type="submit",  name="action", value="XML to PS")
    page << form

    page << h.h3('Translates to...')

    output = translate(input, action)

    page << h.pre(output, style="padding:0.5em; border: 2px solid black;")

    page << h.p("This page/software was developed by sandro@w3.org.   It's too buggy right now to use.   Please don't even bother to report bugs.")

    print page
    # cgi.print_environ()    

def translate(input, action):
    
    s = input

    if action.startswith("PS to "):
        doc = ps_parse.parse(s)
    elif action.startswith("XML to "):
        p = xml_in.Parser(rif.bld_schema)
        p.root = ET.fromstring(s)
        doc = p.instance_from_XML(p.root)
    else:
        raise RuntimeError('not a valid source format')

    if action.endswith(" to PS"):
        return rif.as_ps(doc)
    elif action.endswith("XML to "):
        return bld_xml_out.do(doc)
    else:
        raise RuntimeError('not a valid output format')


def ensure_safety(uri):
    for x in ['"', "'", " "]:
        if uri.find(x) > -1:
            print "The string %s contains a %s" % (uri, x)
            raise ValueError

def cgiMain():

    import cgi
    import sys
    import os

    form = cgi.FieldStorage()
    input=form.getfirst("input")
    action=form.getfirst("action")
    main_page(input)
    #if input is None or input == "":
    #    prompt()
    #else:
    #    #ensure_safety(input)
    #    run(input)


def default_input() :
        return """Document(
  Prefix(cpt <http://example.com/concepts#>)
  Prefix(ppl <http://example.com/people#>)
  Prefix(bks <http://example.com/books#>)

  Group
  (
    Forall ?Buyer ?Item ?Seller (
        cpt:buy(?Buyer ?Item ?Seller) :- cpt:sell(?Seller ?Item ?Buyer)
    )
 
    cpt:sell(ppl:John bks:LeRif ppl:Mary)
  )
)
    """
# http://www.w3.org/RDF/Validator/
