#!/usr/bin/env python2.5
#      -*-mode: python -*-    -*- coding: utf-8 -*-

"""

This is crufty old code that has been repurposed many times, and not
carefully.  Sorry.

"""

import time
import sys
import cgi
import glob
import os.path

import html as h

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

    #for k in args.keys():
    #    page << h.p(`k`, '=', `args[k]`)

    form = h.form(method="GET", class_="f")	
    
    form << h.h3("Step 1: Select Input Processor") 
    select_input_processor(form, args)

    form << h.h3("Step 2: Provide Input") 
    select_input(form, args)

    form << h.h3("Step 3: Select Output Processor") 
    select_output_processor(form, args)

    form << h.h3("Step 4: Begin Processing") 

    form << h.br()

    output_div = h.div()
    output_done = run(output_div, args)
    page << form
    page << output_div

    if output_done:
        form <<  h.input(type="submit",  name="action", 
                         value="Update Output Below")
    else:
        form <<  h.input(type="submit",  name="action", 
                         value="Generate Output Below")

    #form <<  h.Raw("&nbsp;")
    #form <<  h.Raw("&nbsp;")
    #form <<  h.Raw("&nbsp;")
    #form <<  h.Raw("&nbsp;")
    #form <<  h.Raw("&nbsp;")
    #form <<  h.input(type="submit",  name="action", value="Generate Output on New Page")



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
    select_processor(div, args, 'parse', 'input_processor')

def select_output_processor(div, args):
    select_processor(div, args, 'serialize', 'output_processor')

def select_processor(div, args, method, field_name):

    for p in plugin.registry:
        if hasattr(p, method):
            desc = []
            desc.append(p.__doc__)
            if hasattr(p, 'spec'):
                desc.append(h.span('  (See ', h.a('language specification', 
                                                href=p.spec), ")"))

            if args.getfirst(field_name) == p.id:
                button = h.input(type="radio",
                            name=field_name,
                            checked='YES',
                            value=p.id)
            else:
                button = h.input(type="radio",
                            name=field_name,
                            value=p.id)
            
            examples = h.span()
            if hasattr(p, 'examples') and p.examples:
                examples << h.br()
                examples << "Load example input: "
                for (name, text) in p.examples:
                    examples << h.input(type="submit", name="load_example", 
                                        value=name)

            div << h.p(button, desc, examples)

def load_example_texts():
    
    for p in plugin.registry:
        if hasattr(p, 'parse'):
            if not hasattr(p, 'examples'):
                p.examples = []
            for filename in sorted(glob.glob('/home/sandro/cvs/dev.w3.org/2009/rif/webapp-examples/%s/*' % p.id)):
                basename = os.path.basename(filename)
                if os.path.isfile(filename):
                    stream = open(filename, "r")
                    p.examples.append( (basename, stream.read()) )
                    stream.close()

            
def handle_example_input(args):
    """ Looks at the load_example parameter and, based on it,
        may CHANGE the value of the input_text and input_processor
        parameters.
    """

    load_example = args.getfirst("load_example")
    for p in plugin.registry:
        if hasattr(p, 'examples') and p.examples:
            for (name, text) in p.examples:
                if name == load_example:
                    try:
                        args["input_text"].value = text
                    except KeyError: 
                        args.list.append(cgi.MiniFieldStorage("input_text", text))
                    try:
                        args["input_location"].value = ""
                    except KeyError: 
                        args.list.append(cgi.MiniFieldStorage("input_location", ""))
                    try:
                        args["input_processor"].value = p.id
                    except KeyError: 
                        args.list.append(cgi.MiniFieldStorage("input_processor", p.id))
    
def select_input(div, args):

    input_location=args.getfirst("input_location") or ""
    div << h.p('(Method 1) Web Address of Input:',h.br(),
               h.input(type="text", name="input_location",
                       size="80",
                       value=input_location))
    
    input_text=args.getvalue("input_text", default_input())
    div << h.p(('(Method 2) Input Text:'), h.br(),
               h.textarea(input_text,
                          cols="90", rows="10", name="input_text"))

def run(page, args):

    input_text = input_text=args.getvalue("input_text", "")
    input_text = input_text.replace("\r\n", "\n")

    input_processor_id = args.getfirst("input_processor")
    iproc = None
    if input_processor_id:
        for p in plugin.registry:
            if hasattr(p, 'parse'):
                if p.id == input_processor_id:
                    iproc = p
                    break
    else:
        page << h.p('No input processor selected.')
        return False
            
    try:
        doc = iproc.parse(input_text)
    except error.SyntaxError, e:
        err = ""
        err += e.message + "\n"
        err += e.illustrate_position()
        page << h.pre("Error\n"+err,
                      style="padding: 1em; border:2px solid red;")
        return False

    
    output_processor_id = args.getfirst("output_processor")
    if output_processor_id:
        oproc = None
        for p in plugin.registry:
            if hasattr(p, 'serialize'):
                if p.id == output_processor_id:
                    oproc = p
                    break
        output = oproc.serialize(doc)
        page << h.pre(output, style="padding:1em; border:1px solid black;")
        return True 
    else:
        page << h.p('No output processor selected.')
        return False
        

            
def ensure_safety(uri):
    for x in ['"', "'", " "]:
        if uri.find(x) > -1:
            print "The string %s contains a %s" % (uri, x)
            raise ValueError

def cgiMain():

    load_example_texts()
    args = cgi.FieldStorage()
    handle_example_input(args)
    main_page(args)

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
