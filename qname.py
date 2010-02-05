"""
   Manage going back and forth between QNames and URIs, ie:

   rdf:type <---> 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'

   Basic usage:

   >>> import qname
   >>> map = qname.Map()

   >>> map.defaults = [qname.common]
   >>> map.uri('rdf:type')
   'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'
   >>> map.qname('http://www.w3.org/1999/02/22-rdf-syntax-ns#type')
   'rdf:type'

   >>> map.foo = "http://example.com/"
   >>> map.uri('foo:bar')
   'http://example.com/bar'
   >>> map.qname('http://example.com/bar')
   'foo:bar'

   It's supposed to handle all the clever thinking about qnames you
   want in parsing or generating a language that uses qnames as short
   forms of URIs
   
"""

import re

class DuplicateShortName(NameError):
    pass

class BlankQName(RuntimeError):
    pass

class Map:
    """

    >>> import qname
    >>> map = qname.Map()

    Part 1 -- maps are basic bi-directional hashes.  You can look up
    the long name (the namespace) from the short name (the qname
    prefix), or the other way around.
    
    >>> print map
    qname.Map({})
    >>> map.bind('rdf', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
    >>> print map
    qname.Map({'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'})
    >>> map.getLong('rdf')
    'http://www.w3.org/1999/02/22-rdf-syntax-ns#'

    We also let you use shortnames as attributes on the map as a
    python object
    
    >>> map.rdf
    'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
    >>> map.getShort(map.rdf)
    'rdf'
    >>> map.owl = 'http://www.w3.org/2002/07/owl#'

    Repeated binding is okay, if it's the same values
    
    >>> map.bind('rdf', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')

    With a different long part, it's an error

    >>> map.bind('rdf', 'http://www.w3.org/something-different')
    Traceback (most recent call last):
    ...
    DuplicateShortName: Shortname 'rdf' cannot be bound to 'http://www.w3.org/something-different' since it is already bound to 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'

    with a different short part, it's an alias.  getShort will always
    return the first shortname bound for this longname.  ERR, not any
    more.  Now it's arbitrary.

    >>> map.bind('r', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
    >>> map.r
    'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
    >>> map.getShort(map.r) == 'rdf' or map.getShort(map.r) == 'r' 
    True
    

    Part 2 -- inheritance from"defaults".  Each map has a list of
    defaults.  If you set some default, bindings get inherited from
    those defaults.

    >>> m1 = qname.Map()
    >>> m1.bind("a", "http://a1.example.com")
    >>> m2 = qname.Map()
    >>> m2.bind("a", "http://a2.example.com")
    >>> m2.bind("b", "http://b.example.com")
    >>> map.defaults = [m1, m2]
    >>> map.a
    'http://a1.example.com'
    >>> map.b
    'http://b.example.com'

    Part 3 -- we'll make up shortnames if you ask for one and we don't
    have one.    

    >>> uri = 'http://www.w3.org/2000/10/swap/log#'
    >>> map.getShort(uri)
    'log'
    >>> map.log
    'http://www.w3.org/2000/10/swap/log#'

    Part 4 -- to/from qnames

    >>> map.qname('http://www.w3.org/2000/10/swap/log#implies')
    'log:implies'
    >>> map.uri('log:implies')
    'http://www.w3.org/2000/10/swap/log#implies'
    
    """
    
    def __init__(self, defaults=None, short_base="ns"):
        self._long = {}
        self._short = {}
        self._old_shorts = {}
        self.short_base = short_base      # see setattr
        self._highestKnownUsed = { short_base: 1 }
        self.defaults = defaults or []    # see setattr

    def __setattr__(self, name, new_value):
        if (name.startswith("_") or
            name == "short_base" or
            name == "defaults"):
            self.__dict__[name] = new_value
        else:
            self.bind(name, new_value)

    def bind(self, short, long):
        try:
            old = self._long[short]
            if self._long[short] == long:
                return   # already bound
            raise DuplicateShortName, (
                "Shortname '%s' cannot be bound to '%s' since it is already bound to '%s'" % (short, long, old))
        except KeyError:
            pass
        self._long[short] = long
        # if we already have a shortname for this longname, remember it
        # but use this latest one.
        if long in self._short:
            self._old_shorts.setdefault(long, []).append(self._short[long])
        self._short[long] = short

    def getShort(self, long, make=True):
        try:
            return self._short[long]
        except KeyError:
            pass
        if make:
            short = self.newShort(long)
            self.bind(short, long)
            return short
        else:
            raise KeyError, long

    def getLong(self, short):
        try:
            return self._long[short]
        except KeyError:
            pass
        for source in self.defaults:
            try:
                # flag this as inherited, somehow?
                return source.getLong(short)
            except KeyError:
                pass
        raise KeyError, (
            "QName prefix '%s' has no registed expansion" % short)

    def __getattr__(self, name):
        try:
            return self.getLong(name)
        except KeyError:
            raise AttributeError, name

    def newShort(self, long):
        """
        >>> import qname
        >>> map = qname.Map()

        # implicit making
        >>> map.getShort('http://a.example.com/foo#')
        'foo'

        # now it's there
        >>> map.foo
        'http://a.example.com/foo#'


        # make a some more, for which we'll also guess "foo"
        >>> map.getShort('http://b.example.com/foo#')
        'foo2'
        >>> map.getShort('http://c.example.com/foo#')
        'foo3'
        >>> map.getShort('http://d.example.com/foo#')
        'foo4'

        # try one for which we'll fall back to "ns"
        >>> map.getShort('http://d.example.com')
        'ns1'
        >>> map.getShort('http://e.example.com')
        'ns2'
        
        """

        base = self.newShortBase(long)
        if base:
            if base not in self._long:
                return base
        else:
            base = self.short_base
        highest = self._highestKnownUsed.get(base, 2)
        while True:
            candidate = base+str(highest)
            if candidate not in self._long:
                self._highestKnownUsed[base] = highest
                return candidate
            highest += 1
            assert(highest < 100000)

    def newShortBase(self, long):
        candidate = None
        for source in self.defaults:
            try:
                candidate = source.getShort(long, make=False)
            except KeyError:
                pass
        if not candidate:
            try:
                candidate = guessShort(long)
            except KeyError:
                pass
        return candidate

    def qname(self, uri, joining_character=":"):
        (long, local) = uri_split(uri)
        short = self.getShort(long)
        if short:
            return short+joining_character+local
        else:
            if local:
                return local
            else:
                for short in self._old_shorts.get(long, []):
                    if short:
                        return short+joining_character+local
                raise BlankQName, uri

    def uri(self, qname):
        try:
            (short, local) = qname.split(':', 2)
        except ValueError:
            short = ""
            local = qname
        long = self.getLong(short)
        return long+local

    def __str__(self):
        return "qname.Map("+str(self._long)+", "+str(self._short)+")"

    def iteritems(self):
        return self._long.iteritems()
    
    def shortNames(self):
        return self._long.keys()

splitPattern = re.compile(r"""^(.*[#?/])([a-zA-Z_][-\w]*|)$""")

class Unsplitable(RuntimeError):
    pass

def uri_split(uri):
    """

    >>> uri_split('http://www.w3.org/2002/07/owl#Class')
    ('http://www.w3.org/2002/07/owl#', 'Class')

    >>> uri_split('http://www.w3.org/2002/07/owl#')
    ('http://www.w3.org/2002/07/owl#', '')

    >>> uri_split('http://www.w3.org/2002/07/owl#ok-stuff')
    ('http://www.w3.org/2002/07/owl#', 'ok-stuff')

    >>> uri_split('http://www.w3.org/2002/07/owl#bad stuff')
    Traceback (most recent call last):
    ...
    Unsplitable: http://www.w3.org/2002/07/owl#bad stuff

    """
    m = splitPattern.match(uri)
    if m:
        return m.groups()
    raise Unsplitable, uri

nsPattern = re.compile(r"""^\w+://[\w.]*(?:[^a-zA-Z_]*([a-zA-Z_]+\w*))*[^a-zA-Z_]*$""")

def guessShort(long):
    """
    Return the last part of the URI which looks like a word.

    We do not consider "-" a legal character, although it legal in an
    XML qname.
    
    >>> guessShort('http://www.w3.org/2002/07/owl#')
    'owl'

    >>> guessShort('http://www.w3.org/2000/01/rdf-schema')
    'schema'

    >>> guessShort('http://www.w3.org/2000/01/rdf-schema#')
    'schema'

    >>> guessShort('http://purl.org/dc/elements/1.1/')
    'elements'

    >>> guessShort('http://purl.org/dc/elements2/1.1/')
    'elements2'
    
    """
    m = nsPattern.match(long)
    if m:
        text = m.groups()[0]
        if text in common._long:
            # don't guess something like "rdf"
            raise KeyError, long
        return text
    else:
        raise KeyError, long
    


common = Map()
common.rdf  = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
common.rdfs = 'http://www.w3.org/2000/01/rdf-schema#'
common.xs = 'http://www.w3.org/2001/XMLSchema#'
common.dc10 = 'http://purl.org/dc/elements/1.0/'
common.dc = 'http://purl.org/dc/elements/1.1/'
common.foaf = 'http://xmlns.com/foaf/0.1/'
common.log = 'http://www.w3.org/2000/10/swap/log#'
common.owl = 'http://www.w3.org/2002/07/owl#'
common.rif = 'http://www.w3.org/2007/rif#'
common.func = 'http://www.w3.org/2007/rif-builtin-function#'
common.pred = 'http://www.w3.org/2007/rif-builtin-predicate#'

if __name__ == "__main__":
    import doctest, sys
    doctest.testmod(sys.modules[__name__])
