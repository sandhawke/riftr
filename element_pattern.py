#!/usr/bin/env python2.5
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

A simplified representation of XML Schema, with trivial validator

Ummmm, actually I don't have time to do this, do it.


"""

import xml.etree.cElementTree as etree 
import urllib2
import urlparse

xsns = "http://www.w3.org/2001/XMLSchema"

class Namespace(object):
    """
    For conveniences, lets us write rif.foo as shorthand for
    "{"+rifxmlns+"}"+"foo".
    """
    def __init__(self, ns):
        self.ns = ns
    def __getattr__(self, term):
        return "{" + self.ns + "}" + term

xs = Namespace(xsns)


class ElementPattern (object):
    
    def __init__(self):
        self.tag = None


class ComplexTypeElementPattern (ElementPattern):

    def __init__(self):
        ElementPattern.__init__(self)
        self.pattern = None

    def __str__(self):
        return "ComplexTypeElementPattern(%s, %s)" % (self.tag, str(self.pattern))

    def match(self, tree):
        if tree.tag != self.tag:
            return False
        return self.pattern.match([x for x in tree.getchildren()])

class TextElementPattern (ElementPattern):

    def __init__(self):
        ElementPattern.__init__(self)

    def match(self, tree):
        return len(tree) == 0

class Reference (object):

    def __init__(self, name):
        self.name=name


################

class Sequence (object):

    def __init__(self):
        self.subs = []    # array of  (ElementPattern, minOccurs, maxOccurs)

    def match(self, tree):

        pos = 0
        for (sub, minOccurs, maxOccurs) in subs:
            count = 0
            while sub.match(tree[pos]):
                count += 1
                pos += 1
            if count < minOccurs:
                return False
            if maxOccurs is not None and count > maxOccurs:
                return False

class Choice (object):

    def __init__(self):
        self.alternatives = []    # array of ElementPattern

    def match(self, tree):

        for a in alternatives:
            if a.match(tree):
                return True
        return False

################


class Schema (object):

    def __init__(self):
        self.targetNamespace = None
        self.pattern = {}
        self.elements = {}
        self.complexTypes = {}

    def __str__(self):
        s =  "Schema(\n"
        for key in sorted(self.elements.keys()):
            s += "  "+key+": "+str(self.elements[key])+"\n"
        s += ")\n"
        return s
    
    def load(self, location):
        stream = urllib2.urlopen(location)
        print "loading", location
        text = stream.read()
        tree = etree.fromstring(text)
        self.parse(tree, location)
        print "done loading", location

    def parse(self, tree, source_location):
        assert tree.tag == xs.schema
        
        self.targetNamespace = tree.get("targetNamespace")

        for child in tree.getchildren():

            print child.tag

            if child.tag == xs.annotation:
                pass

            elif child.tag == getattr(xs, "import"):
                pass

            elif child.tag == xs.include:
                relative_location = child.get("schemaLocation")
                absolute_location = urlparse.urljoin(source_location, relative_location)
                self.load(absolute_location)

            elif child.tag == xs.element:
                e = self.parse_element(child)

            elif child.tag == xs.group:
                name = child.get("name")
                self.sequence_or_choice(child[0])

            elif child.tag == xs.complexType:
                name = child.get("name")
                self.complexTypes[name] = self.sequence_or_choice(child[0])

            else:
                raise Exception("tag="+child.tag)

    def parse_element(self, tree):
        """Return an ElementPattern for this element

        Copy as necessary if it's got a ref or group or whatever.
        """
        assert tree.tag == xs.element

        ref = tree.get("ref")
        if ref:
            # forward references are allowed, so we need to link this up in a later pass
            return Reference(ref)

        name = tree.get("name")
        typ = tree.get("type") or ""
        print "     ", name
        if ref:
            raise Exception
        if typ.startswith("xs:"):
            print "  element %s given type %s" % (name, typ)
            # assume subtype of xs:string for now  @@@
            result = TextElementPattern()
        elif typ:
            result = ComplexTypeElementPattern()
            result.pattern = Reference(typ)
        elif len(tree) == 0:
            result = ComplexTypeElementPattern()
            result.pattern = []
        else:
            assert tree[0].tag == xs.complexType
            result = ComplexTypeElementPattern()
            result.pattern = self.sequence_or_choice(tree[0][0])

        result.tag = "{"+self.targetNamespace+"}"+name
        self.elements[name] = result
        return result
        
    def parse_group(self, tree):
        #   I think groups are a shorthand --- we don't reflect them into the
        #   actual grammar.    So parse it like complextype, but then we use
        #   it we make a copy....
        
        # <xs:group ref="ATOMIC"/>
        #     
        # <xs:group name="ATOMIC">
        # <!--
        # ATOMIC         ::= IRIMETA? (Atom | Frame)
        #    -->
        #    <xs:choice>
        #        <xs:element ref="Atom"/>
        #        <xs:element ref="Frame"/>
        #    </xs:choice>
        #  </xs:group>

        #  self.group[name]   --- but what is a group/complextype ?
        #
        #      could be a sequence or a choice which we then instantiate, I think.
        pass

    def parse_group_or_element(self, tree):
        if tree.tag == xs.group:
            return self.parse_group(tree)
        elif tree.tag == xs.element:
            return self.parse_element(tree)
        else:
            raise Exception()

    def sequence_or_choice(self, tree):

        if tree.tag == xs.sequence:
            result = Sequence()
            for e in tree.getchildren():
                item = self.parse_group_or_element(e)
                minOccurs = int(e.get("minOccurs", 0))
                maxOccurs = e.get("maxOccurs", "unbounded")
                if maxOccurs == "unbounded":
                    maxOccurs = None
                else:
                    maxOccurs = int(maxOccurs)
                result.subs.append(  (item, minOccurs, maxOccurs)   )
        elif tree.tag == xs.choice:
            print "doing choice"
            result = Choice()
            for e in tree.getchildren():
                item = self.parse_group_or_element(e)
                result.alternatives.append(item)
        else:
            raise Exception(tree.tag)

        return result



if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print "Usage: %s schema_URL" % sys.argv[0]
    else:
        s = Schema()
        s.load(sys.argv[1])
        print "RESULT: ", s

