#! /usr/bin/env python
"""

Some code for handling web/xml stuff, factored out of various projects
I've done.    [ sandro@hawke.org ]


Should pull out some of the http-cache logic from the table-generator
project, or maybe it's a standard python library, by now?

NOT everything is nicely coordinated!   There is duplication, etc.
(sorry)

Mostly this is stuff I wish were in the Dom implementations.  (That's
part of why I'm using Java instead of Python naming conventions.)

"""
__version__ = """$Id$"""

import urllib2 
import time
import sys
import os
from optparse import OptionParser
from xml.dom.minidom import parseString
import xml.dom.minidom
import htmlentitydefs
import re

from debugtools import debug
import debugtools

XML = "http://www.w3.org/XML/1998/namespace"

class UnexpectedContent (Exception):
    pass

# shortcut web access.   very installation specific, of course.
# hacked in here crudely for now.  
localizeURLs = (
    #('http://www.w3.org/2008/', '/home/sandro/8/'),
    #('http://www.w3.org/2007/rif#', '/home/sandro/7/rif.xml'),
    #('http://www.w3.org/2007/rif#', '/home/sandro/cvs/cvs.w3.org/WWW/2008/02/xtan/test/1000-rif/RIF.xsd'),
    )

def debugattrs(node):
    debug("attr(", "attributes: ")
    debug("attr", "attrsNS: %s" % `node._attrsNS`)
    debug("attr", "attrs: %s" % `node._attrs`)
    a = node.attributes
    for i in range(0, a.length):
        debug("attr", "%s=\"%s\"" % (a.item(i).name, a.item(i).value))
    debug("attr)")

def findNodeByID(node, target_id):
    '''  use elementByID instead '''
    if node.nodeType == node.ELEMENT_NODE:
        debug("find(", "node: "+node.tagName+"  id=%s?"%target_id)
        debugattrs(node)
        this_id = node.getAttributeNS(XML, 'id')
        debug("find", "got xml:id=%s" % `this_id`)
        if this_id is "":
            this_id = node.getAttribute('id')
            debug("find", "got id=%s" % `this_id`)
        if target_id == this_id:
            debug("find)", "YES")
            return node
    for child in node.childNodes:
        result = findNodeByID(child, target_id)
        if result is not None:
            debug("find)", "YES")
            return result
    if node.nodeType == node.ELEMENT_NODE:
        debug("find)", "nope")
    return None

def loadXMLFragment(URL):
    try:
        (pre, post) = URL.split("#")
        dom = loadXML(pre)
        node = findNodeByID(dom, post)
        if node is None:
            raise RuntimeError, 'missing xml node "%s"' % URL
        return node
    except ValueError:
        return loadXML(URL)

# no real cache control -- assume this system runs instaneously, not
# long-term.
 
domCache = {}

def openStream(URL):
    for extra in ('', '.xml', '.xsd'):
        if os.path.exists(URL+extra):
            filename = URL+extra
            stream = open(filename)
            return stream
    for (URLPrefix, FilesystemPrefix) in localizeURLs:
        if URL.startswith(URLPrefix):
            suffix = URL[len(URLPrefix):]
            filename = FilesystemPrefix + suffix
            for extra in ('', '.xml', '.xsd'):
                if os.path.exists(filename+extra):
                    filename = filename+extra
                    break
            debug('web', 'actually using file '+filename)
            stream = open(filename, "r")
            return stream
    debug("web", "opening "+`URL`)
    stream = urllib2.urlopen(URL)
    return stream

def tidy(text):
    to_tidy = tempfile.NamedTemporaryFile()
    to_tidy.write(text)
    to_tidy.flush()
    from_tidy = tempfile.NamedTemporaryFile("r")
    tidy = "/usr/bin/tidy"
    tidy_error_sink = "/tmp/tidy.errors"
    cmd = ("""%s -wrap 68 -numeric -quiet -asxml -utf8 -f %s < %s > %s""" %
           (tidy, tidy_error_sink, to_tidy.name, from_tidy.name))
    code = os.system(cmd)
    to_tidy.close()
    return from_tidy.read()
        
def loadXML(URL, use_html_entities=True):
    debug('web(', 'Fetching '+URL)
    try:
        return domCache[URL]
    except KeyError:
        pass
    t0 = time.time()
    stream = openStream(URL)
    text = stream.read()
    
    t1 = time.time()
    debug('web', len(text), "bytes fetch in",(t1-t0),"seconds.")

    # call tidy?
    # try html5lib?

    text = expandHTMLEntities(text)
    dom = parseString(text)

    t2 = time.time()
    debug('web)', "and parsed to DOM in",(t2-t1),"seconds.")
    domCache[URL] = dom
    # pattr(dom.documentElement)
    return dom


def tree_search(tree, condition, extra=None):
    if condition(tree, extra):
        yield tree
    else:
        for child in tree.childNodes:
            for result in tree_search(child, condition, extra):
                yield result

def subNodes(node):
    """Return iterator over all the nodes under this one."""
    for child in node.childNodes:
        yield child
        for sub in subNodes(child):
            yield sub

def elementById(node, match_id):
    for sub, this_id in subElements(node, None, "id"):
        if this_id == match_id:
            return sub

def elementByIdOrName(node, match_id):
    for sub, this_id, this_name in subElements(node, None, "id", "name"):
        if this_id == match_id or this_name == match_id:
            return sub

def subElements(node, tag=None, *attrs):
    """Return iterator over all the sub_elements (decendants) of this node.

    if attrs are provided, then what's yielded is a tuple of 
    (element, value of attr 0, value of attr 1, ...)

    maybe have a "values" map, which is strings or regexp's of allowed
    value for the attributes... ?

    """
    for child in node.childNodes:
        if child.nodeType == node.ELEMENT_NODE:
            if tag is None or tag == child.tagName:
                if attrs:
                   result = [child]
                   for attr in attrs:
                       #debug("attr: ", attr)
                       if child.hasAttribute(attr):
                           result.append(child.getAttribute(attr))
                       else:
                           # getAttribute returned "" for a missing
                           # attribute, which is semantically quite
                           # different from None.  For instance,
                           # browsers treat <a href="" name="foo" />
                           # quite different from <a name="foo" />
                           result.append(None)
                   #debug("subElements", result)
                   yield result
                else:
                    yield child
            for sub in subElements(child, tag, *attrs):
                yield sub

def fetch(url, supercache=False):
    """Download the contents over the web.    We can super-cache
    everything, since wikis aren't so good about giving us good
    cacheability information.

    (See wiki_cache module for sophisticated version of this.)

    TODO: we should have a separate process which keeps these
    up-to-date by using the wiki watch mechanism, especially for wikis
    (unlike wikipedia) which will mail out change notifications.  This
    wiki-cache-maintainer can make the kind of cache access we're
    doing here be just fine.

    Just use a structure like this:
    
        wiki-dump-cache/quoted-URL

    Note that modern linux filesystems (post ext2) should handle this fine
    up to millions of cache entries.   cf the test results in 
    http://groups.google.com/group/alt.os.linux.suse/browse_thread/thread/02d5738ce786bd4c/52fa2c128c8f1d32
    """
    if not os.path.exists(cacheDir):
        os.makedirs(cacheDir)
    filename = cacheDir+"/"+urllib.quote(url, "")
    if not supercache or not os.path.exists(filename):
        debug("web", '   fetching '+url)
        urllib.urlretrieve(url, filename)
        time.sleep(0.2)
    return(open(filename).read())


def nodeContents(xml):
    '''
        aka innerHTML()
    '''
    result = []
    for e in xml.childNodes:
        result.append(e.toxml())
    result = "".join(result)
    try:
        result = unicode(result)
    except UnicodeDecodeError:
        print >>stderr, 'Unicode error in string', result
    assert type(result) == unicode
    return result

def nodeText(node):
    '''
    like nodeContents but requires content to be plain text
    '''
    node.normalize()
    if (node.nodeType == node.TEXT_NODE or
        node.nodeType == node.CDATA_SECTION_NODE):
        return node.data
    #print >>sys.stderr, "should be no markup, but was: "+`nodeContents(node)`+", node type "+str(node.nodeType)+"; while ELEMENT is nodetype "+str(node.ELEMENT_NODE)
    raise UnexpectedContent("should be no markup, but was: "+`nodeContents(node)`+", node type "+str(node.nodeType))
        
def nodeContentsWithoutMarkup(node):
    s = []
    for n in subNodes(node):
        if (n.nodeType == node.TEXT_NODE or
            n.nodeType == node.CDATA_SECTION_NODE):
            s.append(n.data.strip())
    return " ".join(s)

def white(node):
    if (node.nodeType == node.TEXT_NODE or
        node.nodeType == node.CDATA_SECTION_NODE):
        text = node.data
        if text.strip() == "":
            return True
    if node.nodeType == node.COMMENT_NODE:
        return True
    return False


def expandHTMLEntities(text):
    """
    Given some HTML text, expand any of the standard HTML entities --
    BUT NOT the XML ones in it.

    This is a total hack -- our HTML parser should be doing this for
    us, but right now I can do this faster.  :-(  :-(

    """
    use_unicode = ( type(text) == type(u"") )

    if use_unicode:
        text = text.encode('utf-8')

    # this code works in utf-8, but that's probably not the best
    # choice for performances....  *shrug*
    result = re.sub("&(\w+);", expandHTMLEntity, text)

    if use_unicode:
        result = result.decode('utf-8')

    return result

def expandHTMLEntity(match):
    entity = match.group(1)
    if (entity == "lt" or entity == "gt" or
        entity == "quot" or entity == "amp" or entity == "apos"):
        return "&"+entity+";"
    try:
        expansion = htmlentitydefs.name2codepoint[entity]
        return unichr(expansion).encode('utf-8')
    except KeyError:
        raise Exception, "undefined entity %s" % `entity`

    
def entifyString(text):
    """
    Given the whole HTML page, convert the code points to named HTML entities,
    and maybe convert some &quot; entities back into quote characters.

    This is needed to make the diff-to-wiki not so ugly.
    """

    out = []
    for x in text:
        try:
            entity = htmlentitydefs.codepoint2name[ord(x)]
            if (entity == "lt" or entity == "amp" or entity == "gt" or entity=="quot"):
                out.append(x)
            else:
                #print >>sys.stderr, "Got one!  %s" % entity
                out.append("&"+entity+";")
        except KeyError:
            out.append(x)

    text = (u''.join(out)).encode( "utf-8" )
    return text

# if this string appears inside the document text, it'll get
# mysterously turned into a quote entity.   Arguably, we should
# pick a different magic string if this one happens to be present.
# that is, we could/should use one parameterized by a value we
# increment as needed....
magic_string = '!+!xmlextras-magic-string!+!'

def attrquot_step_1(root):
    """
    Change every quote character in an attribute value into a magic
    string, so that we can find those characters after serialization.
    """
    debug('attrquot(', 'Changing attribute values...')
    for node in subElements(root):
        nnmap = node.attributes
        for i in range(0, nnmap.length):
            attr = nnmap.item(i)
            value = attr.value
            # debug('attrquot', attr, "=", value)
            value2 = value.replace('"', magic_string)
            if value != value2:
                attr.value=value2
                debug('attrquot', 'Changed an %s value: %s' %(`attr.name`, `value2`))
    debug('attrquot)')

def attrquot_step_2(text):
    """
    Change every &quot back to a ", and every magic-string into a &quot,
    so we end up with XML that's only quoting the quotes that happen to
    be inside attribute values.
    """
    text = text.replace('&quot;', '"')
    text = text.replace(magic_string, '&quot')
    return text
    
def save(node, filename, use_html_entities=True):
    """

    Entify == use named HTML entities where possible.  This can help
    with diffs, etc.

    """
    stream = open(filename, "w")
    if use_html_entities:
        attrquot_step_1(node)
    text = node.toxml()

    # hack to workaround the fact the in HTML you can't actually
    # repeat the xmlns declaration for HTML -- which rdf:Literals give
    # us.
    text = text.replace('<div xmlns="http://www.w3.org/1999/xhtml">', '<div>')
        
    if use_html_entities:
        text1 = entifyString(text)
        text = attrquot_step_2(text1)
        debug('attrquot', 'step 2 strings were different?', text==text1)

    stream.write(text)
    stream.close()

def appendText(node, text):
    """Parse the text as XML and insert it into the document right
    after the given node.
    
    Returns the inserted node.
    """

    if type(text) == unicode:
        text = text.encode('utf-8')
    doc = xml.dom.minidom.parseString(text)
    return node.parentNode.insertBefore(doc.documentElement, node.nextSibling)
    
def hasHTMLClass(node, cls):
    """

    Does this node or one of its ancestors have a "class" attribute with
    cls as one of the classes?

    """
    if node.nodeType == node.DOCUMENT_NODE:
        return False
    cls_str = node.getAttribute("class")
    classes = cls_str.split(" ")
    if cls in classes:
        return True
    return hasHTMLClass(node.parentNode, cls)

def HTMLClasses(node):
    """
    Yield sequence of each HTML class word, in order, going outward.
    """
    if node.nodeType == node.DOCUMENT_NODE:
        return
    cls_str = node.getAttribute("class")
    classes = cls_str.split(" ")
    for cls in classes:
        yield cls
    for cls in HTMLClasses(node.parentNode):
        yield cls

def followedByText(startNode, matchText):
    """
    Is this node followed by this character (after any whitespace)?
    (Look up and down the tree [using nextLeaf] to figure this out.)

    There's some questionable whitespace logic...  Some whitespace is
    dropped.  It's good enough for me for now.  Maybe next stage would
    be to do a regexp match, but I don't know how to tell if having
    more text would satisfy the regexp (and thus we should gather more
    text.)
    
    It might also be nice to have a flag/version for seeing/matching
    the markup, but that's a different thing.

    >>> tree = parseString('<a>boo<b>ba<c id="start"/> (<d>ping</d>)</b>baz</a>')
    >>> node = elementById(tree, "start")
    >>> followedByText(node, "(")
    True
    >>> followedByText(node, "(ping)")
    True
    >>> followedByText(node, "(pong)")
    False
    >>> followedByText(node, " ")
    False

    """
    text = ""
    node = startNode
    while True:
        node = nextLeaf(node)
        if (node.nodeType == node.TEXT_NODE or
            node.nodeType == node.CDATA_SECTION_NODE):
            text += node.data.strip()
        else:
            raise RuntimeError("Unexpected node"+repr(node))
        if len(text) < len(matchText):
            if text == matchText[0:len(text)]:
                continue  # matching so far...
            else:
                return False   # it'll never match, give up
        else:
            return text[0:len(matchText)] == matchText


def nextLeaf(node):
    """
    Return the next node without children, in an in-order traversal of
    the tree.  This can be used to navigate among TEXT_EMEMENTS, etc.

    >>> tree = parseString('<a>boo<b>ba<c id="start"/>r<d>ping</d></b>baz</a>')
    >>> node = elementById(tree, "start")
    >>> next = nextLeaf(node)
    >>> next
    <DOM Text node "r">
    >>> next = nextLeaf(next)
    >>> next
    <DOM Text node "ping">
    >>> next = nextLeaf(next)
    >>> next
    <DOM Text node "baz">
    >>> next = nextLeaf(next)
    >>> next is None
    True

    """
    next = node.nextSibling
    while next is None:
        node = node.parentNode
        if node is None:
            return None  # there is no nextLeaf
        next = node.nextSibling
    while next.hasChildNodes():
        next = next.firstChild
    return next


def theChildElement(node):
    
    theOne = None
    for child in node.childNodes:
        if child.nodeType == node.ELEMENT_NODE:
            if theOne is None:
                theOne = child
            else:
                raise UnexpectedContent()
    #if theOne is None:
    #    raise RuntimError("fewer child nodes than allowed")
    return theOne


if __name__ == "__main__":
    import doctest, sys
    doctest.testmod(sys.modules[__name__])

