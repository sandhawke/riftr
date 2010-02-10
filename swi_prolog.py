#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""
   Establish a SWI Prolog subprocess and allow simple interaction with it.

   >>> lf = chr(10)
   >>> p = Prolog()
   >>> p.say("X is 1+2."+lf)
   >>> p.response().strip()
   'X = 3.'

   >>> list(p.query('between(1,4,X)'))
   [{'X': '1'}, {'X': '2'}, {'X': '3'}, {'X': '4'}]

   >>> p.assertz('f(a)')
   >>> p.assertz('f(b)')
   >>> x = 'value needing quoting'
   >>> p.assertz('f({x})', globals(), locals())
   >>> list(p.query('f(Item)'))
   [{'Item': 'a'}, {'Item': 'b'}, {'Item': 'value needing quoting'}]


   This almost works, but it sometimes gets out of sync, has a few
   quoting problems, and but I expect it's vastly slower than
   pyswip[1], which I forgot about until I'd written 80% of this.
   Maybe it'll be nice to have both options?

   [1] http://code.google.com/p/pyswip/

"""

import sys
import os
import tempfile
import subprocess
import re
import time
import select
import fcntl

from debugtools import debug
import qname
import escape
import error

################################################################
#
#  swipl atom quoting
#

safe_atom = re.compile("[a-z][a-zA-Z_0-9]*$")
def atom_quote(s):
    if isinstance(s, unicode):
        s = s.encode('utf-8')
    m = safe_atom.match(s)
    if m is None:
        # it seems like we don't actually need to escape anything else...
        s = "'"+s.replace('\\', '\\\\').replace(r"'", r"\'")+"'"
    return s

def atom_unquote(s):
    if s[0] == "'":
        s = s[1:-1]
        s = s.replace("\'", "'")
        s = s.replace("\\\\", "\\")
    return s

def parse_bindings(s):
    result = {}
    for line in s.split(',\n'):
        (var, value) = line.split(" = ", 1)
        value = atom_unquote(value.strip())
        result[var] = value
    return result

def t(x):
    # print >>sys.stderr, "t="+`x`
    return x

expr_pattern = re.compile("\{([^}]*)\}")
def replace_exprs(text, caller_globals=None, caller_locals=None):
    if caller_globals is None:
        caller_globals = globals()
    if caller_locals is None:
        caller_locals = {}
    return re.sub(expr_pattern, 
                  lambda match: atom_quote(unicode(t(eval(match.group(1), 
                                                        caller_globals, 
                                                        caller_locals)))),
                  text
                  )

def nonblocking_read(stream):


    if not select.select([stream], [], [], 0.1)[0]:
        return ''
    return stream.read()

class Prolog(object):

    def __init__(self):
        self.popen = None
        self.count = 0
        self.start()

    def start(self):
        if self.popen:
            raise RuntimeError
        self.querying = False
        self.popen = subprocess.Popen(["swipl", "-q"],
                                      bufsize=0, # unbuffered for now at least
                                      stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.STDOUT,
                                      close_fds=True)

        #print "started swipl pid ", self.popen.pid

        # http://code.activestate.com/recipes/440554/
        #...says we don't need this.  They only block if NOTHING can be read.
        flags = fcntl.fcntl(self.popen.stdout, fcntl.F_GETFL)
        fcntl.fcntl(self.popen.stdout, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    def stop(self):
        #print "stopping swipl pid ", self.popen.pid
        self.popen.kill()
        self.popen = None

    def say(self, text, caller_globals=None, caller_locals=None):
        """

           x>>> p = Prolog()
           x>>> p.say("once((findall(X,foo(X),L),format('RESULT:~q~n',L))).\n")
           x>>> p.response()

        """
        safe_text = replace_exprs(text, caller_globals, caller_locals)
        self.popen.stdin.write(safe_text)
        
    def assertz(self, text, caller_globals=None, caller_locals=None):
        self.reset()
        self.say("assertz(")
        self.say(text, caller_globals, caller_locals)
        self.say(").\n")
        r = self.response().strip()
        if r == "true.":
            #print "asserted."
            pass
        else:
            raise RuntimeError('assertz not confirmed, got '+`r`)

    def query(self, text, caller_globals=None, caller_locals=None):
        self.reset()
        self.say(text+".\n", caller_globals, caller_locals)
        self.querying = True
        while True:
            line = self.response(endings=[" ", ".\n\n"])
            if line.endswith(".\n\n"):
                self.querying = False
                yield parse_bindings(line[:-3])
                return
            yield parse_bindings(line)
            self.popen.stdin.write(";\n")

    def reset(self):
        if self.querying:
            self.popen.stdin.write("\n")
        final = self.response([""])
        #print "reset got:", `final`
        self.querying = False
        #self.ping()  # not really necessary, of course...

    def response(self, endings=["\n"]):
        buf = nonblocking_read(self.popen.stdout)
        while True:
            for ending in endings:
                if buf.endswith(ending):
                    #print 'response='+`buf`
                    return buf
            #print "buffer missing proper endings, ",`endings`
            time.sleep(0.01)
            more = nonblocking_read(self.popen.stdout)
            if more == "":
                #print "waiting for more..., have:",`buf`
                pass
            else:
                #print "got more: ", `more`
                buf += more

    def ping(self, count=1):
        for i in range(0,count):
            t = time.time()
            txt = "hello_world_"+str(t)+"_"+str(self.count)
            self.count += 1
            self.say("format('~q~n', [{txt}]).\n", globals(), locals())
            r = self.response(["\ntrue.\n\n"])
            t1 = time.time()
            (l1, l2) = r.split("\n", 1)
            if atom_unquote(l1) == txt:
                #print "ping response in %0.2fms" % ((t1-t)*1000)
                pass
            else:
                raise RuntimeError("bad ping: expected %s got %s" % (`txt`, `l1`))
        

def test():
    p = Prolog()

    print "pinging..."
    p.ping(5000)
    print "5000 pings done."


    p.assertz("p(1,1)")
    p.assertz("p(1,2)")
    p.assertz("p(1,3)")
    p.assertz("p(4,0)")

    print "table:"
    for r in p.query("p(X,Y)"):
        print `r`

    print "adding 100 rows..."
    for i in range(0,100):
        p.assertz("p(9,%d)" % i)

    print "adding 100 rows, interrupting a query..."
    for i in range(0,100):
        for r in p.query("p(X,Y)"):
            break
        p.assertz("p(5,%d)" % i)

    p.ping()
    print "table:"
    for r in p.query("p(X,Y)"):
        print `r`

    p.ping(100)

    #x = r'''stuff: '"\ '''
    #p.assertz('f({x})', globals(), locals())
    #l=list(p.query('f(Item)'))
    #print `l`
    #print `x`
    ## some extra level of quoting is coming into play....
    #print l[0]['Item'] == x

if __name__=="__main__":
    import doctest, sys
    doctest.testmod(sys.modules[__name__])

    test()
