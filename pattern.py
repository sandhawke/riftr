"""

"Tree Patterns"



General code for handle RIF's Abstract Syntax Notation (asn07).

  -- data model  (classes, datatypes, and slots)
  -- read ascii syntax
  -- write ascii syntax
  -- decode from OWL RDF graph / Ontology
  -- encode into OWL RDF graph / Ontology

  -- write rng syntax
  -- write xml schema

** The whole notion of Grammars here is unnecessary, I think.


ISSUE:
     call "List of Foo" as "ordered Foo*" ?  or List(Foo) !
     
"""

import re
import urllib2
import cStringIO
import rdflib
import rdflib.Collection
from sys import stderr
import sys

import qname

#  This difference is confusing.   The RelaxNG for RDF/XML uses the
# -datatypes version, and lots of others do, too.
# XS_NAMESPACE = "http://www.w3.org/2001/XMLSchema-datatypes"
XS_NAMESPACE = "http://www.w3.org/2001/XMLSchema"

OWL = rdflib.Namespace("http://www.w3.org/2002/07/owl#")
RDF = rdflib.Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS = rdflib.Namespace("http://www.w3.org/2000/01/rdf-schema#")

class Error(RuntimeError):
   pass
class SlotRedefined(RuntimeError):
   pass
class ClassNotFound(RuntimeError):
   pass

#
# Stream Utils
#

uriSchemePattern = re.compile(r"""^([a-zA-Z_0-9]*):""")

def ensure_open_source(source):
    """Given various possibilities for how you might want to provide
    some input data, return a readable & closeable stream for it.

    Filenames and URLs are distinguished from input data by the
    presense of one or more newlines.   That's kind a hack, isn't it?
    Heh.   Maybe that should come out.

    """

    if hasattr(source, "read") and hasattr(source, "close"):
        return source
    if source.find("\n") >= 0:
        return cStringIO.StringIO(source)
    if uriSchemePattern.match(source):
        return urllib2.urlopen(source)
    else:
        return open(source, "r")
    
def ensure_open_sink(sink):
    """Given a stream-like object, or a filename, or a URL, return an
    open stream.   This lets people be more casual when calling us."""   
    if hasattr(sink, "write") and hasattr(sink, "close"):
        return sink
    return open(sink, "w")

def default_importer(source):
    raise Error

def kleeneOp(s):
    """
    Return the Kleene operator (+, *, ?, nothing) for an object with
    a minCardinality and a maxCardinality.
    """
    if s.minCardinality == 0:
        if s.maxCardinality is None:
            return "*"
        elif s.maxCardinality == 1:
            return "?"
        else:
            raise Error, "unusable maxCardinality"
    elif s.minCardinality == 1:
        if s.maxCardinality is None:
            return "+"
        elif s.maxCardinality == 1:
            return ""
        else:
            raise Error, "unusable maxCardinality"
    else:
        raise Error, "unusable minCardinality"
   
#
# Abstract Grammar Structure
#

class Slot:
    """A slot models the relationship between a Property and a Class.

    It has a cls, a valueType (which must be an pattern.Class or
    pattern.Datatype), a propertyIRI, a minCardinality, optional
    maxCardinality, and isList.  [ the isList flag could be done under
    valueType ]

    """
    def __init__(self, **kwargs):
        self.cls = kwargs.get("cls")
        self.propertyIRI = kwargs.get("propertyIRI")
        self.valueType = kwargs.get("valueType")
        self.minCardinality = kwargs.get("minCardinality", 0)
        self.maxCardinality = kwargs.get("maxCardinality", None)
        self.isList = kwargs.get("isList", False)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

class ValueType (object):

   def __init__(self, **kwargs):
      self.users = []   # folks who refer to you by name, as a type

   def clearUsers(self, done):
      self.users = []

   def setUsers(self, done, prefix):
      pass

class Class (ValueType):

    def __init__(self, **kwargs):
        ValueType.__init__(self, **kwargs)
        self.grammar = kwargs.get("grammar")
        self.iri = kwargs.get("iri")

        self._superclasses=[]
        self._subclasses=[]
        self._slots = []
        self.abstract = kwargs.get("abstract", False)

    def clearUsers(self, done=set()):
       self.users = []
       for cls in self._subclasses + [x.valueType for x in self._slots]:
          if cls not in done:
             done.add(cls)
             cls.clearUsers(done)

    def setUsers(self, done=set(), prefix="   "):
       """For this class and its subclasses and slot.valueTypes,
       assign a list of .users, the Classes which use this class.
       Uses "done" to avoid loops."""
       if self in done:
          return
       #print "sU"+prefix+str(self)
       done.add(self)
       for cls in self._subclasses:
          cls.setUsers(done, prefix+" s ")
       for slot in self._slots:
         if self not in slot.valueType.users:
            slot.valueType.users.append(self)
         slot.valueType.setUsers(done, prefix+" t ")

    def addSlot(self, new):
        "link it in, unless we already have it..."
        for slot in self._slots:
            if slot.propertyIRI == new.propertyIRI:
                #found it -- is it the same?
                if slot == new:
                    return
                else:
                    raise SlotRedefined
        self._slots.append(new)
        
    def obtainSlot(self, propertyIRI, created=None):
        for slot in self._slots:
            if slot.propertyIRI == iri:
                if created:
                    created[0] = False
                return slot
        if created:
            created[0] = True
        return self.newSlot(propertyIRI)

    def newSlot(self, propertyIRI):
        slot = Slot(cls=self, propertyIRI=propertyIRI)
        self._slots.append(slot)
        return slot

    def getSlot(self, propertyIRI):
        for slot in self._slots:
            if slot.propertyIRI == propertyIRI:
                return slot
        return None
    
    @property
    def slots(self):
       for cls in self.superclasses + [self]:
          for slot in cls._slots:
             yield slot
          
    @property
    def superclasses(self):
       """In root-to-leaves order, except maybe for multiple inheritance."""
       result = []
       for cls in self._superclasses:
          for s in cls.superclasses + [cls]:
             if s not in result:
                result.append(s)
       #print "  ", self, " has all superclasses: ", result
       return result

    @property
    def superclasses_up(self):
       """In leaves-to-root order, except maybe for multiple inheritance."""
       result = []
       #print self, "direct supers:", self._superclasses
       for cls in self._superclasses:
          for s in [cls] + cls.superclasses:
             if s not in result:
                result.append(s)
       #print "  ", self, " has all superclasses_up: ", result
       return result

    @property
    def unabstract(self):
       """Return self or first superclass which is not abstract"""
       for cls in [self] + self.superclasses_up:
          if not cls.abstract:
             return cls
       raise Exception, "No unabstract class in hierarchy! "+str(self)

    def addSuperclass(self, other):
        if other in self._superclasses:
            return
        self._superclasses.append(other)
        other._subclasses.append(self)
        # print >>stderr, self, "has superclass", other

    def directSubclasses(self):
        for cls in self._subclasses:
            yield cls

    def allSubclasses(self):
        yield self
        for cls in self._subclasses:
            for sub in cls.allSubclasses():
                yield sub

    def allSuperclasses(self):
        yield self
        for cls in self._superclasses:
            for sub in cls.allSuperclasses():
                yield sub

    def getLeafSubclasses(self):
        """
        >>> import pattern
        >>> c1 = Class(iri="c1")
        >>> c2 = Class(iri="c2")
        >>> c3 = Class(iri="c3")
        >>> c3.addSuperclass(c2)
        >>> c2.addSuperclass(c1)

        >>> [x.iri for x in c3.allSubclasses() ]
        ['c3']
        >>> [x.iri for x in c2.allSubclasses() ]
        ['c2', 'c3']
        >>> [x.iri for x in c1.allSubclasses() ]
        ['c1', 'c2', 'c3']

        >>> [x.iri for x in c3.getLeafSubclasses() ]
        ['c3']
        >>> [x.iri for x in c2.getLeafSubclasses() ]
        ['c3']
        >>> [x.iri for x in c1.getLeafSubclasses() ]
        ['c3']

        >>> c1.isLeaf()
        False
        >>> c2.isLeaf()
        False
        >>> c3.isLeaf()
        True
        
        """
        if self._subclasses:
            for cls in self._subclasses:
                for sub in cls.getLeafSubclasses():
                    yield sub
        else:
            yield self

    def isLeaf(self):
        return (self._subclasses == [])

    def __repr__(self):
        return self.iri

    @property
    def children(self):
       """The direct subclasses and they types of my slots"""

       for sub in self._subclasses:
          yield sub
          for slot in sub.slots:
             yield slot.valueType

    def XXXdescendents(self, loop_tracker=None):
       """Recursive children, including self"""

       if loop_tracker is None:
          loop_tracker = set()
       else:
          if self in loop_tracker:
             return
       yield self
       for sub in self._subclasses:
          for slot in sub.slots:
             yield slot.valueType
          for dec in sub.descendents(loop_tracker):
             yield dec

    def reachable(self, visited=set()):
       """All the classes that can be reached from this class, either
       as the subclass of a reachable cleass, or as the valueType of a
       slot of a reachable class.  We don't specifically return
       superclases, but we will pick up their slots, via slot
       inheritance."""
       if self in visited:
          return
       visited.add(self)
       yield self
       for sub in self.allSubclasses():
          for r in sub.reachable(visited):
             yield r
          for slot in sub.slots:
             t = slot.valueType
             if isinstance(t, Class):
                for r in t.reachable(visited):
                   yield r
                

class Datatype (ValueType):
    """

    NOTE that a Class is semantically different from a Datatype, in
    that a typetype constrains BOTH the kinds of thing that can appear
    there, AND the way it is serialized.    Consider the case of two
    datatypes which have the same value space (eg decimal and
    hexadecimal) but different lexical spaces.)....   hrm.
    """

    def __init__(self, **kwargs):
        ValueType.__init__(self, **kwargs)
        self.iri = kwargs.get("iri")
        self.grammar = kwargs.get("grammar")

    def directSubclasses(self):
       # or tap into subtype hierarchy....?
       return []

    @property
    def unabstract(self):
       return self

    @property
    def slots(self):
       return []
    
nsPattern = re.compile(r"""^\s*(?P<default>default)?\s*namespace\s+(?P<short>\w*)\s*=\s*"(?P<long>[^"]*)"\s*""")
commentPattern = re.compile(r"^([^#]*)\s*#")
indentPattern = re.compile(r"^( *)(.*)$")
classLinePattern = re.compile(r"^(sub)?class\s+(?P<name>(\w|:)+)(?P<abstract>\s+abstract)?\s*$")

# OLD propertyLinePattern = re.compile(r"^property\s+(?P<name>(\w|:)+)\s*:\s*((?P<set>set\s+of\s*)|(?P<list>list\s+of\s*)|)(?P<type>(\w|:)+)\s*(,\s*(?P<optional>optional))?\s*$")

propertyLinePattern = re.compile(r"^property\s+(?P<name>(\w|:)+)\s*:\s*((?P<set>set\s+of\s*)|(?P<list>list\s+of\s*)|)(?P<type>(\w|:)+)(?P<op>[*+?])?\s*$")

class Grammar:
    """A container for Classes/Slots/Datatypes.   Same as an Ontology.

    Classes, Slots, Datatypes are owned by their Grammar.  They may
    not be shared between Grammars.
    """

    def __init__(self, **kwargs):
        self.reset()

    #
    # Medium Level Public
    #
    
    #def newClass(self, **kwargs):
    #    return Class(grammar=self, **kwargs)

    def obtainClass(self, iri):
        for cls in self._classes:
            if cls.iri == iri:
                return cls
        cls = Class(grammar=self, iri=iri)
        self._classes.append(cls)
        return cls

    def getClass(self, iri):
        for cls in self._classes:
            if cls.iri == iri:
                return cls
        raise ClassNotFound, iri

    def obtainDatatype(self, iri):
        for datatype in self._datatypes:
            if datatype.iri == iri:
                return datatype
        dt = Datatype(grammar=self, iri=iri)
        self._datatypes.append(dt)
        return dt
        
    def obtainType(self, iri):
        # Something of a hack for now.  How are we supposed to know?
        # I guess classes are declared -- datatypes might not be?
        # But in either case, they might be forward references, no?
        if iri.startswith(XS_NAMESPACE):
            return self.obtainDatatype(iri)
        else:
            return self.obtainClass(iri)

    def reset(self):
        "Make this Grammar be empty."
        self._classes = []
        self._datatypes = []

    #
    #
    #

    def parents_mapping(self):
       "Return a mapping from each class/datatype to the set of its parents."
       result = {}
       for parent in self._classes:
          for child in parent.children:
             result.setdefault(child, set()).add(parent)
       return result

    #
    # High Level Public
    #

    def save(self, stream):
        raise RuntimeError()

    def load(self, source, importer=default_importer, qmap=None):
        """
        Add all the declarations found on the input stream to this
        Grammar; calls the importer function on any imports found,
        which are expected to call us again recursively.   Loops are
        detected in here (we don't fromText the same source twice).

        >>> import pattern
        >>> g = pattern.Grammar()
        >>> g.load("test/books.asn")
        >>> for cls in g._classes: print cls.iri
        http://www.w3.org/2007/01/ss-example#Book
        http://www.w3.org/2007/01/ss-example#Person
        >>> for dt in g._datatypes: print dt.iri
        http://www.w3.org/2001/XMLSchema#string
        http://www.w3.org/2001/XMLSchema#datetime

        # >>> for cls in g._classes: print cls.iri, cls._slots
        """
        source = ensure_open_source(source)
        indents = [ (-1, None) ]
        if qmap is None:
            qmap = qname.Map()
            qmap.defaults = [qname.common]
        for line in source:
            self.loadLine(line, indents, importer, qmap)

    def loadLine(self, line, indents, importer, qmap):
        
      #print >>stderr, ""
      #print >>stderr, "line:", line

      m = nsPattern.match(line)
      if m:
         d = m.groupdict()
         if d["default"]:
            qmap.bind('', d["long"])
         else:
            if not d["short"]:
               raise Error, "Namespace declaration needs short name, if not default"
         qmap.bind(d["short"], d["long"])
         return

      m = commentPattern.match(line)    # doesn't know about quotes
      if m:
         line = m.groups()[0]

      if not line.strip():
         return

      if line.find("\t") != -1:
         raise Error, "no tab characters allowed (M-x untabify, man expand, or something)"

      m = indentPattern.match(line)
      (indentText, line) = m.groups()
      indent = len(indentText)

      (baseIndent, container) = indents[-1]
      #print >>stderr, "[start] indent: %i, baseIndent: %i, container: %s" % (indent, baseIndent, container)
      while indent <= baseIndent:
         indents.pop()
         (baseIndent, container) = indents[-1]
         #print >>stderr, "[pop'd] indent: %i, baseIndent: %i, container: %s" % (indent, baseIndent, container)
               
      m = classLinePattern.match(line)
      if m:
         d = m.groupdict()
         item = self.obtainClass(qmap.uri((d["name"])))
         #print >>stderr, ("Got class, URI: %s" % qmap.uri((d["name"])))
         if container:
            #print >> stderr, "container: %s" % container
            assert isinstance(container, Class)
            item.addSuperclass(container)
         item.abstract = d["abstract"] is not None
            
      else:
         m = propertyLinePattern.match(line)
         if m:
            d = m.groupdict()
            #print >>stderr, ("Got slot, prop: %s" % qmap.uri((d["name"])))
            #print >>stderr, "container: %s" % container
            item = Slot()
            item.propertyIRI = qmap.uri(d["name"])
            item.valueType = self.obtainType(qmap.uri(d["type"]))
            item.isList = d["list"] is not None

            if d["set"] is not None:
                raise Error, "obsolete 'set of' syntax.  Use '*' instead."
            op = d["op"]
            if op == "+":
                item.minCardinality = 1
            elif op == "*":
                pass
            elif op == None:
                item.minCardinality = 1
                item.maxCardinality = 1
            elif op == "?":
                item.maxCardinality = 1
            else:
                raise Error, "unknown"

            try:
                container.addSlot(item)
            except SlotRedefined:
                raise Error, ("Property "+d["name"]+" of "+container.iri+" redefined.")
         else:
            raise Error, "syntax error: "+line
      indents.append( (indent, item) )
      #print >>stderr, "[end] indents: %s" % indents

    def exportAsOWLTriples(self, store):
        """
        Convert this Grammar to an OWL Ontology, which we add to the
        given TripleStore.

        """
        for cls in self._classes:
           clsref = rdflib.URIRef(cls.iri)
           #print >>stderr, 'doing class ', clsref
           store.add((clsref, RDF.type, OWL.Class))
           addDisjointUnionSubclasses(store, clsref,
                                 [rdflib.URIRef(sub.iri)
                                  for sub in cls.directSubclasses()])
           for slot in cls._slots:
              propref = rdflib.URIRef(slot.propertyIRI)

              #print >>stderr, '  doing property ', propref
              if isinstance(slot.valueType, Datatype):
                 store.add((propref, RDF.type, OWL.DatatypeProperty))
              else:
                 store.add((propref, RDF.type, OWL.ObjectProperty))
              # @@ NOTE THAT two slots can not differ by this much;
              # (there is something in common, globally, about the property)

              # optional list handling....

              r = newRestriction(store, clsref, propref)
              avf = rdflib.URIRef(slot.valueType.iri)
              store.add( (r, OWL.allValuesFrom, avf) )
              if (slot.valueType.iri ==
                  "http://www.w3.org/2001/XMLSchema#string"
                  or
                  slot.valueType.iri ==
                  "http://www.w3.org/2001/XMLSchema#int"
                  or
                  slot.valueType.iri ==
                  "http://www.w3.org/2001/XMLSchema#decimal"
                  or
                  slot.valueType.iri ==
                  "http://www.w3.org/2001/XMLSchema#datetime"
                  or
                  slot.valueType.iri ==
                  "http://www.w3.org/2001/XMLSchema#anyURI"
                  ):
                 pass
              else:
                 avf_cls = self.getClass(slot.valueType.iri)
                 #print >>stderr, '    all values from', slot.valueType.iri
                 #store.add( (avf, RDF.type, OWL.Class) )
              
              if slot.maxCardinality is not None:
                 r = newRestriction(store, clsref, propref)
                 store.add((r, OWL.maxCardinality,
                            rdflib.Literal(slot.maxCardinality)))
              if slot.minCardinality > 0:
                 r = newRestriction(store, clsref, propref)
                 store.add((r, OWL.minCardinality,
                            rdflib.Literal(slot.minCardinality)))


    def exportAsOWL(self, sink):
        """
        Write out this Grammar in OWL....
        
        >>> import pattern
        >>> g = pattern.Grammar()
        >>> g.load("test/foo.asn")
        >>> g.exportAsOWL("/tmp/foo.owl")

        http://svn.rdflib.net/trunk/examples/example.py
        
        """
        store = rdflib.ConjunctiveGraph()
        store.bind("rdf", RDF)
        store.bind("rdfs", RDFS)
        store.bind("owl", OWL)
        store.bind("rif", "http://www.w3.org/2007/rif#")    ## @@ hack
        self.exportAsOWLTriples(store)
        sink = ensure_open_sink(sink)
        # see rdflib/plugin/py for list
        store.serialize(sink, format="xml")
        sink2 = ensure_open_sink('/tmp/foo.n3')
        store.serialize(sink2, format="n3")
        sink3 = ensure_open_sink('/tmp/foo.nt')
        store.serialize(sink3, format="nt")

    def importAsOWLTriples(self, store):
        """
        Search the given TripleStore for all the OWL we can use, and
        load it into this Grammar.
        """
        raise RuntimeError()

    def exportAsRNC(self, sink):
        """
        Write out this Grammar in Relax-NG Compact Syntax
        (assuming RDF/XML-subset style)

        THIS HAS SOME RIF-SPECIFIC HACKS RIGHT NOW
        
        >>> import pattern
        >>> g = pattern.Grammar()
        >>> g.load("test/bld.asn")
        >>> g.exportAsRNC("/tmp/bld.rnc")

        do we save the map?
        do we save the "default" namespace?
        """
        sink = ensure_open_sink(sink)
        sink.write("\n")
        sink.write('default namespace = "http://www.w3.org/2007/rif#"\n')
        sink.write('namespace rdf = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"\n')
        # this is what rnc needs for XMLS
        sink.write('datatypes xs = "http://www.w3.org/2001/XMLSchema-datatypes"\n')
        sink.write("\n")
        sink.write("start = element rdf:RDF { xml_lang?, xml_base?, Ruleset* }\n")
        sink.write("xml_lang = attribute xml:lang { text }\n")
        sink.write("xml_base = attribute xml:base { text }\n")
        sink.write("\n")
        sink.write("rdf_about = attribute rdf:about { text }\n")
        sink.write("rdf_nodeID = attribute rdf:nodeID { text }\n")
        sink.write('rdf_collection = attribute rdf:parseType {"Collection"}\n')
        sink.write("rdf_list_item = element rdf:Description {\n")
        sink.write("    attribute rdf:nodeID { text }\n")
        sink.write("  | element value {\n")
        sink.write("        attribute rdf:datatype { xs:anyURI }?,\n")
        sink.write("        text\n")
        sink.write("    }\n")
        sink.write("}\n")
        sink.write("\n")


        map = qname.Map()
        map.bind('', 'http://www.w3.org/2007/rif#')
        map.bind('xs', XS_NAMESPACE+"#")
        map.bind('rdf', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
        for cls in self._classes:
            short = map.qname(cls.iri)

            if cls.isLeaf():
                sink.write("\n# Leaf Syntactic Class "+short+"\n")
                sink.write(short)
                sink.write(" = element ")
                sink.write(short)
                sink.write(" { ")
                pinfo = [(s.propertyIRI,
                          short+"__"+map.qname(s.propertyIRI,"__"), s)
                         for s in cls._slots]
                pinfo.sort()
                subs = [ "rdf_about?", "rdf_nodeID?" ]
                subs.extend([code+kleeneOp(s) for (pi, code, s) in pinfo])
                sink.write(", ".join(subs))
                sink.write(" }\n")
                for (pi, code, s) in pinfo:
                    sink.write(code+" = element "+map.qname(pi)+" { ")
                    if s.isList:
                        sink.write("rdf_collection, (rdf_list_item | ")
                        sink.write(map.qname(s.valueType.iri))
                        sink.write(")*")
                    else:
                        sink.write("rdf_nodeID | ")
                        sink.write(map.qname(s.valueType.iri))
                    sink.write(" }\n")
            else:
                sink.write("\n# Abstract Syntactic Class "+short+"\n")
                sink.write(short)
                sink.write(" = ( ")
                sink.write(" | ".join([
                    map.qname(leaf.iri) for leaf in cls.getLeafSubclasses()
                    ]))
                sink.write(" )\n")

    def exportAsISEBNF(self, sink):
        """
        Write out this Grammar in as EBNF for an 'intermediate syntax'

        THIS ONLY WORKS FOR THE RIF NAMESPACE AT THE MOMENT.
        
        >> import pattern
        >> g = pattern.Grammar()
        >> g.load("test/bld.asn")
        >> g.exportAsISEBNF("/tmp/bld.bnf")

        do we save the map?
        do we save the "default" namespace?
        """
        sink = ensure_open_sink(sink)
        sink.write("\n")

        map = qname.Map()
        map.bind('', 'http://www.w3.org/2007/rif#')
        map.bind('xs', XS_NAMESPACE+"#")
        map.bind('rdf', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
        
        pmap = self.parents_mapping()
        queue = [cls for cls in pmap if len(pmap[cls])==0]
        if not queue:
           # sometimes there are no orphans to be root, because
           # the "root" is a loop, so... pick the first class?
           queue = [self._classes[0]]

        done = set()
        while queue:
           cls = queue.pop(0)
           if cls in done:
              continue
           if isinstance(cls, Datatype):
              continue
           #sink.write("# done = "+repr(done)+"\n")
           #sink.write("# queue = "+repr(queue)+"\n")

           short = map.qname(cls.iri)
           done.add(cls)

           lead = short + " ::= "
           sink.write(lead)
           prefix = " " * (len(lead)-2) + "| "
           first = True

           # queue up everything from this production first, so we 
           # output the grammar depth-first, which requires less human
           # brain-power to read, I think...   Or, so we have that choice
           queue_additions = []

           had_branch = False
           for branch in self.bnf_branches(cls.directSubclasses(), pmap):
               had_branch = True
               if first:
                  first = False
               else:
                   sink.write(prefix)

               if branch.isLeaf():
                  sink.write("'")
                  sink.write(map.qname(branch.unabstract.iri))
                  done.add(branch)
                  sink.write("' '(' ")
                  for slot in branch.slots:
                     queue_additions.append(slot.valueType)
                     #sink.write("# enqueuing "+map.qname(slot.valueType.iri))
                     pshort = map.qname(slot.propertyIRI)
                     tshort = map.qname(slot.valueType.iri)
                     # unclear if we want this or not....
                     #sink.write("'"+pshort+" ->' ")
                     sink.write(pshort+"=")
                     if slot.isList:
                        sink.write("list("+tshort+")")
                     else:
                        sink.write(tshort)
                     sink.write(kleeneOp(slot)+" ")
                  sink.write("')' ")
               else:
                  sink.write(map.qname(branch.iri))
                  queue_additions.append(branch)
                  #sink.write("# enqueuing "+map.qname(branch.iri))
               sink.write("\n")
           if not had_branch:
                  # obvisouly this needsto be cleaned up wrt above
                  branch = cls
                  sink.write("'")
                  sink.write(map.qname(branch.unabstract.iri))
                  done.add(branch)
                  sink.write("' '(' ")
                  for slot in branch.slots:
                     queue_additions.append(slot.valueType)
                     #sink.write("# enqueuing "+map.qname(slot.valueType.iri))
                     pshort = map.qname(slot.propertyIRI)
                     tshort = map.qname(slot.valueType.iri)
                     # unclear if we want this or not....
                     #sink.write("'"+pshort+" ->' ")
                     sink.write(pshort+"=")
                     if slot.isList:
                        sink.write("list("+tshort+")")
                     else:
                        sink.write(tshort)
                     sink.write(kleeneOp(slot)+" ")
                  sink.write("')' ")
                  sink.write("\n")
           sink.write("\n")
           queue[0:0] = queue_additions
           #queue.extend(queue_additions)

    def bnf_branches(self, subclasses, pmap):
       """yield the decendent classes which are leaves or have more
       tha one parent; that is, skip into (and avoid printing) any classes
       which are unnecessary."""
       return subclasses

       #   not right --- doesn't notice that a class is used as 
       #   a valueType
       #
       # for now....
       #for cls in subclasses:
       #   if not cls.isLeaf() and len(pmap[cls]) == 1:
       #      for branch in self.bnf_branches(cls.directSubclasses(), pmap):
       #         yield branch
       #   else:
       #      yield cls

def newRestriction(store, clsref, propref):
   restriction = rdflib.BNode()
   store.add((restriction, RDF.type, OWL.Restriction))
   store.add((restriction, OWL.onProperty, propref))
   store.add((clsref, RDFS.subClassOf, restriction))
   return restriction

def addDisjointUnionSubclasses(store, super, subs):

   rest = RDF.nil
   
   for sub in subs:

      list = rdflib.BNode()
      store.add( (list, RDF.type, RDF.List) )
      store.add( (list, RDF.first, sub) )
      store.add( (list, RDF.rest, rest) )
      rest = list

      store.add( (sub, RDFS.subClassOf, super) )
      # store.add( (sub, RDF.type, OWL.Class) )
      #print >>stderr, '  subclass ', sub
      
      for other in subs:
         if sub < other:
            store.add( (sub, OWL.disjointWith, other ) )

   if rest != RDF.nil:
      store.add( (super, OWL.unionOf, rest) )

# make sure the "new" stuff is okay with dups....


# set some module variable that says that we have a read_grammar function...?


class Writer (object):

   def __init__(self, output_stream=sys.stdout, **kwargs):
      self.output_stream = output_stream
      self.__dict__.update(kwargs)
   
   def out(self, *args):
      for arg in args:
         self.output_stream.write(arg)

class BNF_Writer (Writer):
   
   def serialize(self, root, **kwargs):
      self.__dict__.update(kwargs)
      
      self.map = qname.Map()
      self.map.bind('', 'http://www.w3.org/2007/rif#')
      self.map.bind('xs', XS_NAMESPACE+"#")
      self.map.bind('rdf', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')

      self.done = set()
      root.clearUsers()
      root.setUsers()

      self.do_Production(root)

   def name(self, cls):
      result = self.map.qname(cls.iri)
      if getattr(cls, "abstract", False):
         result = result.upper()
      return result

   def do_Production(self, cls):
      if cls in self.done:
         return
      self.done.add(cls)

      # self.out("\n# ", str(cls), "  users=", str(cls.users), "\n     superclasses:=", str(getattr(cls, "_superclasses", None)),"\n")

      if isinstance(cls, Datatype):
         return
      
      short = self.name(cls)
      lead = short + " ::= "
      self.out(lead)
      prefix = " " * (len(lead)-2) + "| "
      first = True
      todo = []

      if cls.isLeaf():
         branches = [cls]
      else:
         # branches = cls._subclasses
         branches = self.branches(cls._subclasses)
      for branch in branches:

         if first:
            first = False
         else:
            self.out(prefix)
         
         #self.out("\n#  BRANCH:", str(branch), "  users=", str(branch.users), "\n")
         #self.out("\n#     of class ", str(cls))
         #other_users = [x for x in branch.users if x != cls]
         if branch == cls or (branch.isLeaf() and not branch.users):
            self.out("'")
            self.out(self.name(branch.unabstract))
            self.out("' '(' ")
            for slot in branch.slots:
               todo.append(slot.valueType)
               pshort = self.map.qname(slot.propertyIRI)
               tshort = self.name(slot.valueType)
               #self.out("'"+pshort+" ->' ")
               self.out(pshort+"=")
               if slot.isList:
                  self.out("list("+tshort+")")
               else:
                  self.out(tshort)
               self.out(kleeneOp(slot)+" ")
            self.out("')' ")
         else:
            self.out(self.name(branch))
            todo.append(branch)
         self.out("\n")
      self.out("\n")

      for cls in todo:
         self.do_Production(cls)

   def branches(self, subclasses):
      for cls in subclasses:
         if not cls.isLeaf() and len(cls.users) == 0 and len(cls._superclasses) == 1:
            #self.out("### skipping down through ", str(cls))
            for branch in self.branches(cls.directSubclasses()):
               yield branch
         else:
            yield cls


def check(node, cls, path=""):

   if isinstance(node, AST2.Instance):
      for slot in cls.slots:
         path += "."+name(slot.propertyIRI)
         cardinality = 0
         for value in getattr(node, slot.propertyIRI).values:
            if cardinality > 0:
               ppath = path + ".val(%d)" % cardinality
            else:
               ppath = path
            cardinality += 1
            if slot.isList:
               if not isintance(value, AST2.Sequence):
                  fail(ppath, "expecting list value")
               posn = 0
               for item in value:
                  check(item, slot.valueType, ppath+"[%d]"%posn)
                  posn += 1
            else:
               check(value, slot.valueType, ppath)
         if slot.minCardinality is not None:
            if cardinality < slot.minCardinality:
               fail(path, "below minCardinality")
         if slot.maxCardinality is not None:
            if cardinality > slot.maxCardinality:
               fail(path, "above maxOccurs")
   elif isinstance(node, AST2.DataType):
      raise RuntimeError
   else:
      raise RuntimeError

   #//   also fill in all the Class values we know....?    and pick
   #// the lowest non-abstract one as Primary

if __name__ == "__main__":
    import doctest, sys
    doctest.testmod(sys.modules[__name__])

    g=Grammar()
    g.load("test/bld.asn")
    #for c in g._classes[0].reachable():
    #   print c
       
    #with open("/tmp/bld.bnf", "w") as out:
    #   BNF_Writer(out).serialize(g._classes[0])

