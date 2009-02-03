"""

Build and output an HTML web page, in a programming style that helps
keep the page well-formed, valid, and generally pleasant.  Why I'm
writing this in 2003 instead of 1993 is anyone's guess.  I must be
bored or procrastinating.

Write HTML In 7 Seconds:

   >>> from html import *
   >>> d = Document()
   >>> d.head << title("Web Site Story")
   >>> d << h1("Web Site Story")
   >>> d << p("To be continued...")
   >>> print prefixEveryLine("* ", d)
   * <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
   *           "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
   * <html lang="en" xml:lang="en" xmlns="http://www.w3.org/1999/xhtml">
   *   <head><title>Web Site Story</title></head>
   * 
   *   <body>
   *     <h1>Web Site Story</h1>
   * 
   *     <p>To be continued...</p>
   *   </body>
   * </html>
   *


[[  document should follow
       d.printWhenReady(1)
       d.start(p)
       d << "text"
       d.end()
    streaming style, I think, and
    if you want mutable fragments
    you make and use them before
    serializing....
]]

More Thorough:

   >>> from html import *
   >>> print span("Hello, World!")
   <span>Hello, World!</span>

span() is just shorthand for Element("span", ...., inline=1)

   >>> print Element("span", "Hello, World!", inline=1)
   <span>Hello, World!</span>

   
The inline=1 keeps the output on the same line, without it we get
newlines before and after the element (and indenting, which we don't
see here).

   >>> print prefixEveryLine("* ", Element("span", "Hello, World!"))
   * 
   * <span>Hello, World!</span>
   * 

The content is often a sequence...

   >>> print Element("span", ["Hello, ", "World!"], inline=1)
   <span>Hello, World!</span>

but that's deprectaed -- now use:

   >>> print Element("span", "Hello, ", "World!", inline=1)
   <span>Hello, World!</span>

Attributes are supported, of course...

   >>> e = Element("span", "Hello, ", "World!", class_="bright", inline=1)
   >>> print e
   <span class="bright">Hello, World!</span>

append() appends to the content...

   >>> dummy = e.append(" Goodnight, Moon! ")
   >>> print e
   <span class="bright">Hello, World! Goodnight, Moon! </span>

If the content was not a list, append turns it into one, first

   >>> s = span("Hello")
   >>> s.append(", World!")
   >>> print s
   <span>Hello, World!</span>

Elements may be nested, of course...

   >>> e.content = ["Good ", em("Morning"), " Everyone!"]
   >>> print e
   <span class="bright">Good <em>Morning</em> Everyone!</span>

The Document class handle doctype, html/head/body.

   >>> d = Document()
   >>> dummy = d.head.append(title("Test Document"))
   >>> dummy = d.append(h1("Test Document"))
   >>> print prefixEveryLine("* ", d)
   * <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
   *           "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
   * <html lang="en" xml:lang="en" xmlns="http://www.w3.org/1999/xhtml">
   *   <head><title>Test Document</title></head>
   * 
   *   <body>
   *     <h1>Test Document</h1>
   *   </body>
   * </html>
   * 


Pseudo-elements using the class= attribute can be handled nicely:

   >>> def StatusParagraph(content, attrs=None):
   ...    e =  p(content, attrs=attrs)
   ...    e.attrs.setdefault('class', 'status')
   ...    return e

   >>> d.body.content[0:0]=[StatusParagraph("This is a Demonstration Document")]
   >>> print prefixEveryLine("* ", d)
   * <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
   *           "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
   * <html lang="en" xml:lang="en" xmlns="http://www.w3.org/1999/xhtml">
   *   <head><title>Test Document</title></head>
   * 
   *   <body>
   *     <p class="status">This is a Demonstration Document</p>
   *   
   *     <h1>Test Document</h1>
   *   </body>
   * </html>
   * 

.......


Why not use DOM instead?   I dunno.

@@@ needs more content escaping functions, in various places

"""
__version__ = "$Revision$"
# $Id$

import cStringIO
import re

class Streamer:
    """An base class for things which implement writeTo instead of
    __str__."""
    def __str__(self):
        s = cStringIO.StringIO()
        self.writeTo(s)
        return s.getvalue()

class Document(Streamer):

   def __init__(self):
       self.html = Element('html',
                           attrs={ 'xmlns':'http://www.w3.org/1999/xhtml',
                                   'lang':'en', 'xml:lang':'en' })
       self.head = Element('head')
       self.html.append(self.head)
       self.body = Element('body')
       self.html.append(self.body)

   def writeTo(self, s):
       s.write('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"\n')
       s.write('          "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">')
       self.html.writeTo(s)

   def append(self, content):
       """

       cleverly put plain text into a div.   what else to do with it???
       """
       if isinstance(content, Element):
           self.body.append(content)
       else:
           # print "auto diving", content
           #self.body.append(div(content))
           self.body.append(content)
       #return self

   def __lshift__(self, content):
       """Convenience syntax for append, with no parens to balance."""
       return self.append(content)

class Raw(Streamer):
    """Wrapper for text content to say DONT XML-escape it"""

    def __init__(self, s):
        self.data = s
        
    def writeTo(self, s, prefix=""):
        text = re.sub("\n", "\n"+prefix, self.data)
        s.write(text)

def xstr(s):
    """Return the XML-escaped version of s"""
    s = str(s)
    s = re.sub("&", "&amp;", s)
    s = re.sub("<", "&lt;", s)
    s = re.sub(">", "&gt;", s)
    return s
    
class Element(Streamer):

    def __init__(self, tag, *content, **kwargs):
        self.tag=tag

        # pull out the real keyword args first
        if "inline" in kwargs:
            self.inline = kwargs["inline"]
            del kwargs["inline"]
        else:
            self.inline = 0
            
        if "attrs" in kwargs:
            # old style attrs
            self.attrs = kwargs["attrs"]
            del kwargs["attrs"]
        else:
            self.attrs = kwargs
            
        self.content=[]
        for x in content:
            if isinstance(x, list):
                # flatten one layer of nested lists (deprecated)
                self.content.extend(x)
            elif isinstance(x, dict):
                # let attrs be passed without a keyword (deprecated)
                self.attrs.update(x)
            else:
                self.content.append(x)


    prefixLength = 2

    def writeTo(self, s, prefix=""):
        if not self.inline:
            s.write("\n")
            s.write(prefix)
        s.write("<")
        s.write(self.tag)
        keys = self.attrs.keys()
        keys.sort()
        for key in keys:
            if self.attrs[key] is not None:
                s.write(" ")
                if key.endswith("_"):
                    # to allow the "class" attr to be given as "class_"
                    # (in standard python style) to avoid conflict with
                    # the python keyword.
                    s.write(key[0:-1])
                else:
                    s.write(key)
                s.write("=\"")
                s.write(self.attrs[key])
                s.write("\"")
        if self.content:
            s.write(">")
            #print "SELF", self.__class__
            try:
                for child in self.content:
                    #print "CHILD", child.__class__
                    try:
                        #print "Doing WriteTo", 
                        child.writeTo(s, prefix+(" "*self.prefixLength))
                        #print "Did WriteTo"
                    except AttributeError:
                        #print child.__class__
                        s.write(xstr(child))
            except TypeError:   # iteration over non-sequence
                child = self.content
                #print "CHILD", child.__class__
                try:
                    child.writeTo(s, prefix+(" "*self.prefixLength))
                except AttributeError:
                    #print child.__class__
                    s.write(xstr(child))
            s.write("</")
            s.write(self.tag)
            s.write(">")
        else:
            s.write("/>")
        if not self.inline:
            s.write("\n")
            s.write(prefix[0:-self.prefixLength])

    def append(self, content):
        if self.content is None:
            self.content = []
        try:
            self.content.append(content)
        except AttributeError:
            self.content = [ self.content ]
            self.content.append(content)
        #return self  # allows chaining    x.append(y).append(z)
        # (but then we get back a value we rarely use.  ugh)

    def __lshift__(self, content):
       """Convenience syntax for append, with no parens to balance."""
       return self.append(content)

class Comment:
    def __init__(self, content=None, inline=0):
        self.content=content
        if self.content is None: self.content = []
        self.inline = inline

    def __str__(self):
        s = cStringIO.StringIO()
        self.writeTo(s)
        return s.getvalue()
    
    def writeTo(self, s, prefix=""):
        if not self.inline:
            s.write("\n")
            s.write(prefix)
        s.write("<!-- ")
        s.write(self.content)       ## @@@ escaping?
        s.write(" -->")
        if not self.inline:
            s.write("\n")
            s.write(prefix[0:-2])
   

def stylelink(href):
    return Element("link", attrs={
        "rel":"stylesheet",
        "type":"text/css",
        "href":href})

def prefixEveryLine(prefix, s):
    extra = ""
    s = str(s)
    if s.endswith("\n"): extra = "\n"+prefix
    return prefix+("\n"+prefix).join(s.splitlines())+extra

class Flow:
    """
    >>> import html
    >>> h = html.Flow()
    >>> print prefixEveryLine("* ",
    ...                       h.span("Spanned Text", class_="authorName"))
    * 
    * <span class="authorName">Spanned Text</span>
    * 
    """
    def __getattr__(self, name):
        def func(*content, **kw):
            kw["inline"] = 0
            return apply(Element, [name]+list(content), kw)
        return func

class Inline:
    """
    >>> import html
    >>> h = html.Inline()
    >>> print h.span("Spanned Text", class_="authorName")
    <span class="authorName">Spanned Text</span>
    """
    def __getattr__(self, name):
        def func(*content, **kw):
            kw["inline"] = 1
            return apply(Element, [name]+list(content), kw)
        return func

"""Foo"""

def createStdElements():
    import html

    flow = Flow()
    inline = Inline()

    # These element names come from
    # http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd
    #
    # I added the "+" myself (a flag for non-inline element); it's
    # just about the style in which the HTML is generated and doesnt
    # HAVE to match inline/flow in HTML's own syntax.

    elements = """a abbr acronym address area b base bdo big
    blockquote+ body+ br+ button caption cite code col colgroup dd del
    dfn div+ dl dt em fieldset form+ h1+ h2+ h3+ h4+ h5+ h6+ head+ hr+ html+ i
    img input+ ins kbd label legend li link map meta noscript object ol+
    optgroup option p+ param pre q samp script+ select+ small span strong
    style sub sup table+ tbody+ td textarea+ tfoot th thead title tr+ tt
    ul+ var"""

    for x in elements.split(" "):
        tag = x.strip()
        if tag:
            if tag.endswith("+"):
                tag = tag[0:-1]
                html.__dict__[tag] = getattr(flow, tag)
            else:
                html.__dict__[tag] = getattr(inline, tag)
            

createStdElements()

if __name__ =='__main__':
    import doctest, html
    print "Performing doctest..."
    print doctest.testmod(html) 

# $Log$
# Revision 1.1  2009/02/03 05:11:04  sandro
# skeletal beginning
#
# Revision 1.1  2007/01/06 22:20:57  sandro
# copied from 2001/10/swap
#
# Revision 1.6  2003/09/04 05:40:13  sandro
# added XML quoting and Raw elements
#
# Revision 1.5  2003/08/01 15:40:46  sandro
# simpler API; actually changed Apr 29 but not comitted
#
# Revision 1.4  2003/04/29 04:46:57  sandro
# added clever << operator (now where have I seen that before?)
#
# Revision 1.3  2003/02/18 17:02:05  sandro
# added auto-generation of element-creation functions, based on XHTML DTD
#
# Revision 1.2  2003/02/14 00:44:24  sandro
# added some more functions: htable, tr, td, a
#
# Revision 1.1  2003/01/29 18:28:37  sandro
# first version, passes doctests, [warning: excessive tool-building]
#
