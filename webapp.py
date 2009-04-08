#!/usr/bin/env python2.5
#      -*-mode: python -*-    -*- coding: utf-8 -*-

"""

This provides the web interface, in parallel to cmdline.py providing
the command-line interface.


"""

import time
import sys
import cgi
import glob
import os.path
from cStringIO import StringIO

import html as h

import plugin
import rif
import error

import xml_in
import xml_out
import dump2_out
import prolog_out
import func_to_pred
import unnest

#import ps_parse
#import ps_lex
#import xml_in
#import bld_xml_out


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

    form << h.h3("Step 3: (Optional) Select transform or analysis plugins") 
    select_middle(form, args)
    
    analysis_div = h.div()
    page << analysis_div

    form << h.h3("Step 4: Select Output Processor") 
    select_output_processor(form, args)

    form << h.h3("Step 5: Begin Processing") 

    form << h.br()

    output_div = h.div()
    output_done = run(output_div, args, analysis_div)
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
            if getattr(p, 'examples', []):
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
    
    input_text=args.getvalue("input_text", "")
    div << h.p(('(Method 2) Input Text:'), h.br(),
               h.textarea(input_text,
                          cols="90", rows="10", name="input_text"))

def select_middle(div, args):

    any = False
    line = h.p("[NOT WORKING RIGHT NOW].  Select plugins to instantiate: ")
    div << line
    for p in plugin.registry:
        if p.action_word() in ["transform", "analysis"]:
            line << h.span(p.id)   # javascript so click makes a new block for it appear below....
            line << " "
            any = True
    if not any:
        line << "(none available)."

class OptionSet (object):
    pass

def run(outdiv, args, middiv):

    options = OptionSet()
    options.plugins = [ args.getfirst("input_processor"),
                        args.getfirst("output_processor"),
                        ] + args.getlist("plugin")
    
    # get other "options" out of args...
    #    they're named (pluginid_optionname):   xml_out_indent=
    
    for p in plugin.registry:
        for option in getattr(p, 'options', []):
            key = p.id + "_" + option.name
            values = args.getlist(key)
            if values:
                setattr(options, key, values[0])
            else:
                default = getattr(option, 'default', None)
                if default:
                    setattr(options, key, default)

    try:
        (iproc,) = plugin.get_plugins(["input"], options)
    except ValueError:
        outdiv << h.p('No input processor selected.')
        return False

    input_text = input_text=args.getvalue("input_text", "")
    input_text = input_text.replace("\r\n", "\n")
    try:
        doc = iproc.parse(input_text)
    except error.SyntaxError, e:
        err = ""
        err += e.message + "\n"
        err += e.illustrate_position()
        outdiv << h.pre("Error\n"+err,
                      style="padding: 1em; border:2px solid red;")
        return False


    for p in plugin.get_plugins(["transform","analysis"], options):
        if isinstance(p, plugin.TransformPlugin):
            doc = p.transform(doc)
        elif isinstance(p, plugin.AnalysisPlugin):
            report = p.analyze(doc)
            d = h.div()
            d << h.p("Report from %s plugin:" % p.id)
            d << h.pre(report, style="padding:1em; border:1px solid black;")
            middiv << d
        else:
            raise RuntimeError


    try:
        (oproc,) = plugin.get_plugins(["output"], options)
    except ValueError:
        outdiv << h.p('No output processor selected.')
        return False

    buffer = StringIO()
    oproc.serialize(doc, buffer)
    outdiv << h.pre(buffer.getvalue(), style="padding:1em; border:1px solid black;")
    return True 
        

            
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

