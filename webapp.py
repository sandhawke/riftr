#!/usr/bin/env python2.5
#      -*-mode: python -*-    -*- coding: utf-8 -*-

"""

This is crufty old code that has been repurposed many times, and not
carefully.  Sorry.

"""

import time
import sys
import os
import xml.etree.cElementTree as ET
from cStringIO import StringIO

import html as h

#sys.path.insert(0,"/usr/share/python-support/python-ply/")
#import ply.yacc as yacc
#import ply.lex as lex

import plugin
import ps_parse
import ps_lex
import xml_in
import bld_xml_out
import rif
import error

#
# GLOBAL VARIABLES
#
# (This is a CGI, we can do this kind of stuff.  Heh.  Maybe someday
# we'll turn this into a class called, um, ... Page? )
#
page = None

def startPage(title):
    global page
    if page == None:

        print "Content-Type: text/html; charset=utf-8\n"
        page = h.Document()
        page.head.append(h.title(title))
        page.head << h.stylelink("http://validator.w3.org/base.css")


def main_page(args):
    global page

    startPage("Highly Experimental RIF Demonstration Page")	
    page << h.h2("Highly Experimental RIF Demonstration Page")
    page << h.p("This page currently only does translations between RIF XML and RIF PS, but the idea is to have various non-RIF languages supported as well")

    form = h.form(method="GET", class_="f")	
    
    form << h.h3("Step 1: Select Input Processor") 
    select_input_processor(form, args)

    form << h.h3("Step 2: Provide Input") 
    select_input(form, args)

    form << h.h3("Step 3: Select Output Processor") 
    select_output_processor(form, args)

    form << h.h3("Step 4: Begin Processing") 

    form << h.br()
    form <<  h.input(type="submit",  name="action", value="Generate Output Below")
    form <<  h.Raw("&nbsp;")
    form <<  h.Raw("&nbsp;")
    form <<  h.Raw("&nbsp;")
    form <<  h.Raw("&nbsp;")
    form <<  h.Raw("&nbsp;")
    form <<  h.input(type="submit",  name="action", value="Generate Output on New Page")
    page << form

    if 0:
        page << h.h3('Translates to...')

        input = input.replace("\r\n", "\n")
        action=args.getfirst("action") 
        if action:
            (notes, output) = translate(input, action)
        else:
            notes = "select a processing option"
            output = ""

        if notes:
            page << h.h4('Processor Message:')
            page << h.pre(notes, style="padding:0.5em; border: 2px solid red;")


        if output:
            page << h.pre(output, style="padding:0.5em; border: 2px solid black;")
        else:
            page << h.p("-- No Output --")

    page << h.hr()

    page << h.p("This page/software was developed by sandro@w3.org.   It's too buggy right now to use.   Please don't even bother to report bugs.")

    print page
    # cgi.print_environ()    

def select_input_processor(div, args):
    select_processor(div, args, 'parse')

def select_output_processor(div, args):
    select_processor(div, args, 'serialize')

def select_processor(div, args, method):

    for p in plugin.registry:
        if hasattr(p, method):
            desc = []
            desc.append(p.__doc__)
            if hasattr(p, 'spec'):
                desc.append(h.span('  (See ', h.a('language specification', 
                                                href=p.spec), ")"))

            div << h.p(
                    h.input(type="radio",
                            name="input_processor",
                            value=p.id),
                    desc)

def select_input(div, args):

    input_location=args.getfirst("input_location") or ""
    div << h.p('Web Addres of Input:',
               h.input(type="text", name="input_location",
                       value=input_location))

    div << h.p('... or input text:')
    input_text=args.getfirst("input") or default_input()
    div << h.textarea(input_text,
                       cols="90", rows="10", name="input")

def translate(input, action):
    
    s = input
    notes = ""

    if action.startswith("PS to "):
        try:
            doc = ps_parse.parse(s)
        except error.SyntaxError, e:
            notes += "\nsyntax error, line %d, col %d, %s" % (e.line, e.col, e.msg) + "\n"
            notes += e.illustrate_position()
            return (notes, None)
    elif action.startswith("XML to "):
        p = xml_in.Parser(rif.bld_schema)
        p.root = ET.fromstring(s)
        doc = p.instance_from_XML(p.root)
    else:
        raise RuntimeError('not a valid source format')

    if action.endswith(" to PS"):
        return (notes, rif.as_ps(doc))
    elif action.endswith(" to XML"):
        buffer = StringIO()
        ser  = bld_xml_out.Serializer(stream=buffer)
        ser.do(doc)
        return (notes, buffer.getvalue())
    else:
        raise RuntimeError('not a valid output format')


def plugins():

    for (name, module) in sys.modules.items():
        if not module:
            continue

        try:
            info = module.plugin_info
        except AttributeError:
            continue
        
        yield (name, module, info)

        
            
def ensure_safety(uri):
    for x in ['"', "'", " "]:
        if uri.find(x) > -1:
            print "The string %s contains a %s" % (uri, x)
            raise ValueError

def cgiMain():

    import cgi
    import sys
    import os

    args = cgi.FieldStorage()
    main_page(args)
    #if input is None or input == "":
    #    prompt()
    #else:
    #    #ensure_safety(input)
    #    run(input)


def xdefault_input() :
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

def default_input():
    return """
<!-- Example 7 from RIF BLD July 2008 Draft -->
<!DOCTYPE Document [
  <!ENTITY ppl  "http://example.com/people#">
  <!ENTITY cpt  "http://example.com/concepts#">
  <!ENTITY dc   "http://purl.org/dc/terms/">
  <!ENTITY rif  "http://www.w3.org/2007/rif#">
  <!ENTITY func "http://www.w3.org/2007/rif-builtin-function#">
  <!ENTITY pred "http://www.w3.org/2007/rif-builtin-predicate#">
  <!ENTITY xs   "http://www.w3.org/2001/XMLSchema#">
]>

<Document 
    xmlns="http://www.w3.org/2007/rif#"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:xs="http://www.w3.org/2001/XMLSchema#">
  <payload>
   <Group>
    <id>
      <Const type="&rif;iri">http://sample.org</Const>
    </id>
    <meta>
      <Frame>
        <object>
          <Const type="&rif;local">pd</Const>
        </object>
        <slot ordered="yes">
          <Const type="&rif;iri">&dc;publisher</Const>
          <Const type="&rif;iri">http://www.w3.org/</Const>
        </slot>
        <slot ordered="yes">
          <Const type="&rif;iri">&dc;date</Const>
          <Const type="&xs;date">2008-04-04</Const>
        </slot>
      </Frame>
    </meta>
    <sentence>
     <Forall>
       <declare><Var>item</Var></declare>
       <declare><Var>deliverydate</Var></declare>
       <declare><Var>scheduledate</Var></declare>
       <declare><Var>diffduration</Var></declare>
       <declare><Var>diffdays</Var></declare>
       <formula>
         <Implies>
           <if>
             <And>
               <formula>
                 <Atom>
                   <op><Const type="&rif;iri">&cpt;perishable</Const></op>
                   <args ordered="yes"><Var>item</Var></args>
                 </Atom>
               </formula>
               <formula>
                 <Atom>
                   <op><Const type="&rif;iri">&cpt;delivered</Const></op>
                   <args ordered="yes">
                     <Var>item</Var>
                     <Var>deliverydate</Var>
                     <Const type="&rif;iri">&ppl;John</Const>
                   </args>
                 </Atom>
               </formula>
               <formula>
                 <Atom>
                   <op><Const type="&rif;iri">&cpt;scheduled</Const></op>
                   <args ordered="yes">
                     <Var>item</Var>
                     <Var>scheduledate</Var>
                   </args>
                 </Atom>
               </formula>
               <formula>
                 <Equal>
                   <left><Var>diffduration</Var></left>
                   <right>
                     <External>
                       <content>
                         <Expr>
                           <op><Const type="&rif;iri">&func;subtract-dateTimes</Const></op>
                           <args ordered="yes">
                             <Var>deliverydate</Var>
                             <Var>scheduledate</Var>
                           </args>
                         </Expr>
                       </content>
                     </External>
                   </right>
                 </Equal>
               </formula>
               <formula>
                 <Equal>
                   <left><Var>diffdays</Var></left>
                   <right>
                     <External>
                       <content>
                         <Expr>
                           <op><Const type="&rif;iri">&func;days-from-duration</Const></op>
                           <args ordered="yes">
                             <Var>diffduration</Var>
                           </args>
                         </Expr>
                       </content>
                     </External>
                   </right>
                 </Equal>
               </formula>
               <formula>
                 <External>
                   <content>
                     <Atom>
                       <op><Const type="&rif;iri">&pred;numeric-greater-than</Const></op>
                       <args ordered="yes">
                         <Var>diffdays</Var>
                         <Const type="&xs;integer">10</Const>
                       </args>
                     </Atom>
                   </content>
                 </External>
               </formula>
             </And>
           </if>
           <then>
             <Atom>
               <op><Const type="&rif;iri">&cpt;reject</Const></op>
               <args ordered="yes">
                 <Const type="&rif;iri">&ppl;John</Const>
                 <Var>item</Var>
               </args>
             </Atom>
           </then>
         </Implies>
       </formula>
     </Forall>
    </sentence>
    <sentence>
     <Forall>
       <declare><Var>item</Var></declare>
       <formula>
         <Implies>
           <if>
             <Atom>
               <op><Const type="&rif;iri">&cpt;unsolicited</Const></op>
               <args ordered="yes"><Var>item</Var></args>
             </Atom>
           </if>
           <then>
             <Atom>
               <op><Const type="&rif;iri">&cpt;reject</Const></op>
               <args ordered="yes">
                 <Const type="&rif;iri">&ppl;Fred</Const>
                 <Var>item</Var>
               </args>
             </Atom>
           </then>
         </Implies>
       </formula>
     </Forall>
    </sentence>
   </Group>
  </payload>
 </Document>
"""

# http://www.w3.org/RDF/Validator/
