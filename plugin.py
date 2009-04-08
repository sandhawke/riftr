#!/usr/bin/env python2.5
#      -*-mode: python -*-    -*- coding: utf-8 -*-

"""

TODO: 

     -- use a plugins directory, so they don't need to be enumerated
        somewhere?

     -- find a way to allow the same intermediate plugin to be used
        multiple times with different options...?  (and in the XML
        form?)  In the cmdline form, we could exec something which
        which attaches the argument's affect to a prior compatible
        plugin.

     -- html for options.

Every plugin should:

   1.  import this module (plugin)

   2.  create an plugin class which is subclass of one of the below
       plugin subclasses (InputPlugin, OutputPlugin, etc) and give it:

        plugin.id

                Some short unique identifier-syntax string

                Typically like <language_name>_in,
                <language_name>_out, etc.

                If there's only one plugin in a module, it's
                reasonable to use __name__, so the plugin id is the
                module name.

        plugin.__doc__

                The documentation for that plugin -- ie what we print
                out to describe it

        plugin.spec  (optional)

                A string with the URL of the spec for the implemented
                language.

        plugin.options

                A list of options which this plugin supports.  They'll
                turn into keyword parameters to the plugin, when it is
                instantiated.

                Each item in the list is a plugin.Option 

        plugin.parse(str)
        plugin.serialize(node)
        plugin.transform(node)
        plugin.analyze(node)

                implement to appropriate one of these functions        

   3.  Toward the end of your module, call:   

           plugin.register(your_plugin_class)


Design Note:

   I was on the fence about whether what's registered as a plugin
   should be a class or an instance.  I settled on "class" when I
   added options, because it seems pretty nice to have the options
   turn into attributes of the instance and/or arguments.

   (Maybe there should be some flag about whether you want them passed
   in, or want us to set them, then call init2?)


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
                         action="append_const",
                         const=cls.id,
                         dest="plugins",
                         help= ( ("Use this %s plugin. " % cls.action_word())+
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

class TransformPlugin (Plugin):
    """Must have a transform() method"""

    def transform(self, root_node):
        raise RuntimeError("Not implemented")

    @classmethod
    def action_word(cls):
        return "transform"

class AnalysisPlugin (Plugin):
    """Must have a transform() method"""

    def analyze(self, root_node):
        raise RuntimeError("Not implemented")

    @classmethod
    def action_word(cls):
        return "analysis"



def register(p):
    """

    """
    assert p.__doc__
    assert p.id
    if isinstance(p, Plugin):
        raise RuntimeError("Plugin %s passed instance instead of class")
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

def get_plugins(actions, options):
    """ Yields sequence of INSTANTIATIONS of plugins which which:
            1.  have their id present in the list options.plugins
                (and use this order for results); and
            2.  have an action word ("input", "transform", etc]
                in the collection you provide as "actions";
     """
    
    for plugin_id in getattr(options, "plugins"):
        for plugin in registry:
            if plugin.action_word() in actions:
                if plugin.id == plugin_id:
                    yield instantiate_with_options(plugin, options)


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


