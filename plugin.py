#!/usr/bin/env python2.5
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

This module provides a fairly general plugin interface.  Each plugin
has an id, some documentation, zero of more configuration options, and
one or more functions, such as "parse" or "transform".  What we factor
out here, mostly, is the user interface for those configuration
options.  We provide both a unix command line interface and a web
forms interface.

(This really belongs in a toolkit; it has nothing to do with riftr,
except that's where I first used it.)

Every plugin should:

   1.  Be a class defined in a .py file in the plugins subdirectory

   2.  Be a subclass of plugin.Plugin; maybe also of InputPlugin,
       OutputPlugin, etc.

   3.  Have some class attributes:

        id

                Some short unique identifier-syntax string

                Typically like <language_name>_in,
                <language_name>_out, etc.

                If there's only one plugin in a module, it's
                reasonable to use __name__, so the plugin id is the
                module name.

        __doc__

                The documentation for that plugin -- ie what we print
                out to describe it

        spec  (optional)

                A string with the URL of the spec for the implemented
                language.

        options

                A list of options which this plugin supports.  They'll
                turn into keyword parameters to the plugin, when it is
                instantiated.

                Each item in the list is a plugin.Option 

        parse(str)
        serialize(node)
        transform(node)
        analyze(node)

                implement the appropriate one of these functions        



Design Note:

   I was on the fence about whether what's registered as a plugin
   should be a class or an instance.  I settled on "class" when I
   added options, because it seems pretty nice to have the options
   turn into attributes of the instance and/or arguments.

   (Maybe there should be some flag about whether you want them passed
   in, or want us to set them, after init and before calling your
   execution method.   pass_options_to_init ? )

"""

import os
import optparse
from debugtools import debug
from cStringIO import StringIO

#import debugtools
#debugtools.tags.add("plugin")

registry = []


class Plugin (object):
    """Each plugin should provide its own __doc__ string, used in
    displaying information about the plugin.
    """


    @classmethod
    def add_to_OptionParser(cls, parser, group):

        try:
            action_word = cls.action_word()+" "
        except AttributeError:
            action_word = ""
        group.add_option("--"+cls.id,
                         action="callback",
                         callback=append_plugin_instance,
                         callback_args= (cls,),
                         help= ( ("Use this %splugin. " % action_word)+
                                 cls.__doc__ 
                                 ))

def append_plugin_instance(option, opt, value, parser, cls):
    p = instantiate_with_options(cls, parser.values)
    parser.values.ensure_value("plugins", []).append(p)

class InputPlugin (Plugin):
    """Must have a parse() method"""

    def parse(self, input_text):
        raise RuntimeError("Not implemented")

    def parse_file(self, filename):
        stream = open(filename, "r")
        input_text = stream.read()
        stream.close()
        return self.parse(input_text)

class OutputPlugin (Plugin):
    """Must have a serialize() method"""

    def serialize(self, root_node, output_stream):
        raise RuntimeError("Not implemented")

    def serialize_to_string(self, root_node):
        buffer = StringIO()
        self.serialize(root_node, buffer)
        return buffer.getvalue()

class TransformPlugin (Plugin):
    """Must have a transform() method"""

    def transform(self, root_node):
        raise RuntimeError("Not implemented")

class AnalysisPlugin (Plugin):
    """Must have a transform() method"""

    def analyze(self, root_node):
        raise RuntimeError("Not implemented")



def register(p):
    """

    """
    assert p.__doc__
    assert p.id
    if isinstance(p, Plugin):
        # we had some old code that did this...
        raise RuntimeError("Plugin %s passed instance instead of class")
    if p.id not in [x.id for x in registry]:
        registry.append(p)

def import_all():
    """note that dir is BOTH a directory name and a module name"""
    import sys

    # obviously this is a hack for now...    What's the right way to learn
    # the directory that holds the plugins directory?   I don't want the
    # directory itself, because I *think* we might get name conflicts if we
    # import them directly.  (I'm fuzzy about how that works.  Can you
    # import "x" from one path and "x" from another path, and have them both
    # around with the same name?   sys.modules suggests no.
    pdir = "/home/sandro/riftr"
    sys.path.append(pdir)
    
    dir = "plugins"
    ids = {}
    for filename in os.listdir(pdir + "/" + dir):
        if filename.endswith(".py") and not filename[0] == "_":
            local = filename[0:-3]
            module_name = dir + "." + local
            #print 
            #print module_name
            m = __import__(module_name)
            mm = getattr(m, local)
            #print "=> ", mm
            for (name, entry) in mm.__dict__.items():
                if getattr(entry, "__doc__", False) and getattr(entry, "id", False):
                    if entry.id.startswith(dir+"."):
                        # because they used "__name__"
                        entry.id = entry.id[len(dir+"."):]
                    if entry.id in ids:
                        raise RuntimeError, ("Duplicate id: %s used in %s and %s" %
                                             entry.id, ids[entry.id], filename)
                    ids[entry.id] = filename
                    #print "registering", name, entry
                    register(entry)
                
                # I wonder why issubclass doesn't work for me like this.
                #if type(entry).__name__ in [ "classobj", "type" ]:
                #    print "is type/class", name, entry
                #    print issubclass(entry, object)
                #    print issubclass(entry, Plugin)
                #    print issubclass(entry, InputPlugin)


    sys.path.pop(-1)

################################################################

# OPTIONS PROCESSING

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
        #print "add to option parse", plugin.id
        group = optparse.OptionGroup(parser,
                                     "For %s plugin (modify settings BEFORE calling plugin)" % (plugin.id))

        plugin.add_to_OptionParser(parser, group)

        for option in getattr(plugin, 'options', ()):
            option.add_to_OptionParser(plugin, parser, group)
        parser.add_option_group(group)

def plugin_by_id(id):
    for plugin in registry:
        if plugin.id == id:
            return plugin
    return None

def XXXget_plugins(actions, options):
    """ Yields sequence of INSTANTIATIONS of plugins which:
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

class Collection (object):
    def __init__(self, plugins=None):
        self.plugins = plugins or []
    def can_run(self, attr):
        matches = [p for p in self.plugins if hasattr(p, attr)]
        return len(matches) == 1
    def __getattr__(self, attr):
        matches = [p for p in self.plugins if hasattr(p, attr)]
        if len(matches) == 1:
            return getattr(p, attr)
        if matches:
            raise RuntimeError("Too many plugins (%d) offering %s." % (
                    len(matches), attr))
        raise RuntimeError("No plugins offering %s." % attr)

def combined(options):
    return Collection(getattr(options, "plugins", []))

def get_plugins(actions, options):
    for p in options.plugins:
        for action in actions:
            if hasattr(p, action):
                yield p
                break

def get_one_plugin(actions, options):
    p = [x for x in get_plugins(actions, options)]
    if len(p) < 1:
        raise RuntimeError("No %s plugin selected." % actions )
    if len(p) > 1:
        raise RuntimeError("More than one %s plugin selected." % actions)
    return p[0]

def instantiate_with_options(plugin, options):

    kwargs = {}
    for option in getattr(plugin, 'options', ()):
        key = plugin.id + "_" + option.name
        if getattr(option, "values", []):
            value = []
            for provided in getattr(options, key).split(","):
                found = False
                for v in option.values:
                    if v.id == provided:
                        value.append(v)
                        found = True
                if not found:
                    raise optparse.OptionValueError("--%s value %s not one of %s" % (key, repr(provided), [v.id for v in option.values]))
            if getattr(option, "maxcard", None) == 1:
                if len(value) > 1:
                    raise optparse.OptionValueError("--%s can only have ONE of the values %s" % (key, [v.id for v in option.values]))
        else:
            value = getattr(options, key)
        kwargs[option.name] = value
    debug('plugin', 'instantiating', plugin.id, "with args", kwargs)
    return plugin(**kwargs)

class Option (object):

    def __init__(self, name, doc, **kwargs):
        self.name = name
        self.doc = doc
        self.__dict__.update(kwargs)
        # kwargs:
        #  - default is (obviously) the default value
        #  - metavar is an OptionParser thing, it's like FILE or something, used
        #    in the automatic documentation
        #  - values is a list of allowed values (for constrained options)
        #  - maxcard is 1 or None, indicating how many values are allowed

    def add_to_OptionParser(self, plugin, parser, group):

        key = plugin.id + "_" + self.name
        if getattr(self, 'default', None) is not None:
            parser.set_defaults(**{key: self.default})
        kwarg = {}
        if getattr(self, 'metavar', False):
            kwarg['metavar'] = self.metavar
            
        if getattr(self, "values", []):
            allowed_values = "; allowed: " 
            if getattr(self, "maxcard", None) is None:
                allowed_values += "zero or more of "
            allowed_values += ", ".join([v.id for v in self.values])
        else:
            allowed_values = ""

        # it's tempting to use "choices", but that can't handle our comma-separated thing;
        # and the error messages are confusing if people get the wrong cardinality.

        # shall we do special handling for boolean values, recognized by default of True or False?

        group.add_option("--"+key,
                          action="store",      
                          dest=key,
                          help=self.doc + " [default: %default" + allowed_values+"]",
                          **kwarg)

    def html(self):
        
        pass

class TextOption (Option):
    """Multiline or one line?    int value, etc?"""
    pass

class SelectOption (Option):
    pass

class RadioOption (SelectOption):   #SelectOne
    """Select one....  radio or drop down?  Depends on what other
    content we have about it?  And how many there are?"""

    pass

class CheckboxOption (SelectOption):    #SelectMulti
    """Select multiple...
    """
    pass



