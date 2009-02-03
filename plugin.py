#!/usr/bin/env python2.5
#      -*-mode: python -*-    -*- coding: utf-8 -*-



registry = []


class Plugin (object):
    """Must have a doc attribute
    """

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class InputPlugin (Plugin):
    """Must have a parse() method"""
    pass

class OutputPlugin (Plugin):
    """Must have a serialize() method"""
    pass


def register(p):
    """

    """
    assert p.__doc__
    assert p.id
    assert hasattr(p, 'parse') or hasattr(p, 'serialize')
    registry.append(p)


