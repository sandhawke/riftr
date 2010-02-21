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

import rif
import error
import plugin
###import xml_in
import xml_in_etree
import xml_out
import dump2_out
import prolog_out
import func_to_pred
import unnest
import frame_view
import rdfxml_out

# one of these messes up namespace handling in AST2
# ...
###import ps_parse
####import ps_lex
###import bld_xml_out
###import fsxml_out
###import xps_out
####import gend_mps_in
###import blindfold
###import bnf_out
###import ply_out
###import dump_out
###import plugins.test_1

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
    
    plugins = plugin.combined(options)
    if plugins.can_run("system_test"):
        if plugins.system_test():
            sys.exit(0)
        else:
            sys.exit(1)

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

    iproc = plugin.get_one_plugin(["input"], options)
            
    try:
        doc = iproc.parse(input_text)
    except error.SyntaxError, e:
        err = ""
        err += e.message + "\n"
        err += e.illustrate_position()
        print >>sys.stderr, err
        return


    for p in plugin.get_plugins(["transform","analysis"], options):
        if isinstance(p, plugin.TransformPlugin):
            doc = p.transform(doc)
        elif isinstance(p, plugin.AnalysisPlugin):
            report = p.analyze(doc)
            print "\nReport from %s plugin:" % p.id
            print report
            print
        else:
            raise RuntimeError

    out_stream = sys.stdout

    oproc = plugin.get_one_plugin(["output"], options)

    debug('cmdline', 'Output processor=', oproc)
    oproc.serialize(doc, out_stream)

if __name__ == "__main__":
    import doctest, sys
    doctest.testmod(sys.modules[__name__])

    run()
