#!/usr/bin/env python2.5
#      -*-mode: python -*-    -*- coding: utf-8 -*-

"""

Every plugin should:

   1.  import this module (plugin)

   2.  create an plugin class which is subclass of one of the below
       plugin subclasses (InputPlugin or OutputPlugin, at the moment)
       and give it:

        plugin.id

                Some short unique identifier-syntax string

                Typically <language_name>_in or <language_name>_out

        plugin.__doc__

                The documentation for that plugin -- ie what we print
                out to describe it!

        plugin.spec  (optional)

                A string with the URL of the spec for the implemented
                language.

        plugin.options

                A list of options which this plugin supports.  They'll
                turn into keyword parameters to the constructed Parser
                or Serializer?  Or just be passed to parse/serialize?
                Or what?

                Each item in the list is a plugin.Option 

        plugin.parse(str)
        plugin.serialize(node)

                One of these two functions, depending whether you do
                input or output.

   3.  Toward the end of your module, call:   

           plugin.register(your_plugin_instance)


Design Note:

   Why is this an INSTANCE of that class instead of just being the
   class? It could work either way, but being an instance gives us a
   little more flexibility, eg for making multiple very-similar
   languages.  But, really, we could have done it either way.  Still
   we have to pick one, since parse and serialize will be called
   differently if they're bound to an instance.

Design Note:

   We don't really pay enough attention to Input vs Output plugins.
   Could a plugin be both?  I guess we'll understand this better
   when/if we have more types of plugins.

"""

import optparse
from debugtools import debug
from cStringIO import StringIO

registry = []


class Plugin (object):
    """Must have a doc attribute
    """


    @classmethod
    def add_to_OptionParser(cls, parser, group):

        group.add_option("--"+cls.id,
                         action="store_const",
                         const=cls.id,
                         dest=cls.action_word() + "_plugin",
                         help= ( "Use this plugin for " +
                                 cls.action_word()+ 
                                 ".  Description: "+
                                 cls.__doc__ 
                                 ))


class InputPlugin (Plugin):
    """Must have a parse() method"""

    def parse(self, input_text):
        raise RuntimeError("Not implemented")

    @classmethod
    def action_word(cls):
        return "input"

class OutputPlugin (Plugin):
    """Must have a serialize() method"""

    def serialize(self, root_node, output_stream):
        raise RuntimeError("Not implemented")

    def serialize_to_string(self, root_node):
        buffer = StringIO()
        self.serialize(root_node, buffer)
        return buffer.getvalue()

    @classmethod
    def action_word(cls):
        return "output"

def register(p):
    """

    """
    assert p.__doc__
    assert p.id
    if isinstance(p, Plugin):
        print "WARNING: plugin passed instance -- ignored", p.id
        return
    registry.append(p)



################################################################

################################################################

def add_to_OptionParser(parser):
    """
        When using a python optparse.OptionParser, for unix-style
        command-line arguments, you can add plugin options to your
        command line arguments like this.

            from optparse import OptionParser
            ...
            parser = OptionParser(usage="%prog [options] input-location",
                          version=__version__)
            plugin.add_options_to_OptionParser(parser)
    """                          

    parser.set_defaults(input_plugin=None,
                        output_plugin=None)
    
    for plugin in registry:
        #print plugin.id
        group = optparse.OptionGroup(parser,
                                     "For %s plugin" % (plugin.id))

        plugin.add_to_OptionParser(parser, group)

        for option in getattr(plugin, 'options', ()):
            option.add_to_OptionParser(plugin, parser, group)
        parser.add_option_group(group)

def get_plugin(action, options):
    
    plugin_id = getattr(options, action+"_plugin")
    if plugin_id is None:
        raise ValueError
    for plugin in registry:
        if plugin.id == plugin_id:
            return instantiate_with_options(plugin, options)
    # we should never get here due to any user input, I think....
    raise RuntimeError

def instantiate_with_options(plugin, options):

    kwargs = {}
    for option in getattr(plugin, 'options', ()):
        key = plugin.id + "_" + option.name
        value = getattr(options, key)
        kwargs[option.name] = value
    debug('plugin', 'instantiating', plugin.id, "with args", kwargs)
    return plugin(**kwargs)

class Option (object):

    def __init__(self, name, doc, **kwargs):
        self.name = name
        self.doc = doc
        self.__dict__.update(kwargs)
        # eg:   default, metavar, values

    def add_to_OptionParser(self, plugin, parser, group):

        key = plugin.id + "_" + self.name
        if getattr(self, 'default', None) is not None:
            parser.set_defaults(**{key: self.default})
        kwarg = {}
        if getattr(self, 'metavar', False):
            kwarg['metavar'] = self.metavar
        group.add_option("--"+key,
                          action="store",
                          dest=key,
                          help=self.doc + " [default: %default]",
                          **kwarg)
        
class TextOption (Option):
    pass

class SelectOption (Option):
    pass


class RadioOption (SelectOption):
    """Select one....  radio or drop down?  Depends on what other
    content we have about it?  And how many there are?"""

    pass

class CheckboxOption (SelectOption):
    """Select multiple...
    """
    pass


