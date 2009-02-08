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
import fsxml_out
import xps_out
import rif
import error

def run():
    parser = OptionParser(usage="%prog [options] input-location",
                          version=__version__)
    parser.set_defaults(verbose=True)
    parser.set_defaults(output="-")
    parser.add_option("-q", "--quiet",
                      action="store_false", dest="verbose", 
                      help="don't print status messages to stderr")
    parser.add_option("-D", "--debug",
                      action="append", dest="debugTags", 
                      help="turn on debugging of a particular type (try 'all')")
    #parser.add_option("-O", "--output", action="store", dest="output",
    #                  help="Save the output to this file (else stdout)")
    plugin.add_to_OptionParser(parser)
                      
    (options, args) = parser.parse_args()

    # feed the options back, somehow...
    #   plugin.options_from_OptionParser(options)  maybe?

    if options.debugTags:
        debugtools.tags.update(options.debugTags)
    verbose = options.verbose

    debug('cmdline', 'args:', args)
    
    if len(args) != 1:
        parser.print_help()
        sys.exit(1)

    input_filename = args[0]
    if input_filename == "-":
        input_stream = sys.stdin
    else:
        input_stream = open(input_filename, "r")
    input_text = input_stream.read()

    debug('cmdline', 'read %d bytes' % len(input_text))

    try:
        iproc = plugin.get_plugin("input", options)
    except ValueError:
        print >>sys.stderr, "No input plugin selected"
        return
            
    try:
        doc = iproc.parse(input_text)
    except error.SyntaxError, e:
        err = ""
        err += e.message + "\n"
        err += e.illustrate_position()
        print >>sys.stderr, err
        return

    out_stream = sys.stdout

    try:
        oproc = plugin.get_plugin("output", options)
    except ValueError:
        print >>sys.stderr, "No output plugin selected"
        return
            

    debug('cmdline', 'Output processor=', oproc)
    oproc.serialize(doc, out_stream)

if __name__ == "__main__":
    import doctest, sys
    doctest.testmod(sys.modules[__name__])

    run()
