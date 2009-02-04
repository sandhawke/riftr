#!/usr/bin/env python2.5
#      -*-mode: python -*-    -*- coding: utf-8 -*-

"""



"""
__version__="unknown"

import time
import sys
import cgi
import glob
import os.path
from optparse import OptionParser

import debugtools 
from debugtools import debug

import plugin
import ps_parse
import ps_lex
import xml_in
import bld_xml_out
import rif
import error

def run():
    parser = OptionParser(usage="%prog [options] input-location",
                          version=__version__)
    parser.set_defaults(verbose=True)
    parser.set_defaults(in_id="auto")
    parser.set_defaults(out_id="auto")
    parser.set_defaults(output="-")
    parser.add_option("-i", "--input_processor",
                      action="store", dest="in_id", 
                      help="id code for input processing plugin")
    parser.add_option("-o", "--output_processor",
                      action="store", dest="out_id", 
                      help="id code for output processing plugin")
    parser.add_option("-q", "--quiet",
                      action="store_false", dest="verbose", 
                      help="don't print status messages to stderr")
    parser.add_option("-D", "--debug",
                      action="append", dest="debugTags", 
                      help="turn on debugging of a particular type (try 'all')")
    parser.add_option("-O", "--output", action="store", dest="output",
                      help="Save the output to this file (else stdout)")
                      
    (options, args) = parser.parse_args()

    if options.debugTags:
        debugtools.tags.update(options.debugTags)
    verbose = options.verbose

    debug('cmdline', 'args:', args)
    
    if len(args) != 1:
        parser.print_help()
        sys.exit(1)

    debug('cmdline', 'Yo!')

    input_filename = args[0]
    if input_filename == "-":
        input_stream = sys.stdin
    else:
        input_stream = open(input_filename, "r")
    input_text = input_stream.read()

    debug('cmdline', 'read %d bytes' % len(input_text))

    iproc = None
    for p in plugin.registry:
        debug('cmdline', 'possible plugin:', p)
        if hasattr(p, 'parse'):
            if p.id == options.in_id:
                iproc = p
                break
    if iproc is None:
        print >>sys.stderr, "No input plugin %s found." % `options.in_id`
        return
    debug('cmdline', 'Input processor=', iproc)
            
    try:
        doc = iproc.parse(input_text)
    except error.SyntaxError, e:
        err = ""
        err += e.message + "\n"
        err += e.illustrate_position()
        print >>sys.stderr, err
        return

    if options.output == "-":
        out_stream = sys.stdout
    else:
        out_stream = open(options.output, "w")

    oproc = None
    for p in plugin.registry:
        if hasattr(p, 'serialize'):
            if p.id == options.out_id:
                oproc = p
                break
    if oproc is None:
        print >>sys.stderr, "No output plugin %s found." % `options.out_id`
        return

    debug('cmdline', 'Output processor=', oproc)
    str = oproc.serialize(doc)
    out_stream.write(str)

if __name__ == "__main__":
    import doctest, sys
    doctest.testmod(sys.modules[__name__])

    run()
