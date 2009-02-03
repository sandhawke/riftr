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


def page(input=None):
    global page

    startPage("RIF (Highly Experimental) Demonstration Page")	
    page << h.h2("RIF (Highly Experimental) Demonstration Page")
    page << h.p("This page currently only does translations between RIF XML and RIF PS, but the idea is to have various non-RIF languages supported as well")

    form = h.form(method="GET", class_="f")	
    form << h.p("Input Text") 
    if input is None:
        input = """Document(
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
    form << h.textarea(input,
                       cols="80", rows="10", name="input")
    form <<  h.input(type="submit", name="Go",
                     value="Go")
    page << form

    p << h.h2('Translates to...')

    output = translate(input)

    p << h.pre(output)

    print page
    # cgi.print_environ()    

def translate(input):

    return input.replace(" ", "_")

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
    page(input)
    #if input is None or input == "":
    #    prompt()
    #else:
    #    #ensure_safety(input)
    #    run(input)



# http://www.w3.org/RDF/Validator/
