#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

This is a partial database and generator for the documentation
of builtins.

At this writing, it just has the list builtins.


"""


functions = []
predicates = []

class Example:
    def __init__(self, args, result, comment=""):
        self.args = args
        self.result = result
        self.comment = comment

    def __repr__(self):
        return ('Example('
                +`self.args`+','
                +`self.result`+','
                +`self.comment`+')')
class Builtin:

    @classmethod
    def name(cls):
        return cls.__name__.replace('__', '').replace('_', '-')

    from_xpath = True
    optional = []

class Builtin_Predicate (Builtin) :
    
    is_builtin = True
    is_predicate = True

class Builtin_Function (Builtin) :

    is_builtin = True
    is_predicate = False


x = Builtin_Function()
concatenate = x
x.python_name = 'concatenate'
x.text = 'Returns a new list consisting of all the items in list-1 followed by all the items in list-2.'
x.optional = []
x.from_xpath = True
x.uses_equality = 'False'
x.args = ['list-1', 'list-2']
x.examples = [
    ]

x = Builtin_Function()
count = x
x.python_name = 'count'
x.text = 'Return the number of items in the list (the length of the list).'
x.optional = []
x.from_xpath = True
x.uses_equality = 'False'
x.args = ['list']
x.examples = [
    Example([[0, 1, 2, 3, 4]],5,''),
    Example([[0]],1,''),
    Example([[0, 0, 0]],3,''),
    Example([[]],0,'')]

x = Builtin_Function()
delete = x
x.python_name = 'delete'
x.text = 'Return a list which contains all item in old-list,\n in the same order except those which are datatype-equal to\n ?match-value.'
x.optional = ['collation']
x.from_xpath = True
x.uses_equality = True
x.args = ['old-list', 'match-value', 'collation']
x.examples = [
    ]

x = Builtin_Function()
distinct_values = x
x.python_name = 'distinct_values'
x.text = 'Returns a new list which contains exactly those items which are in list-1, but without any two items being equal. The order of the items in the new list is not specified.'
x.optional = []
x.from_xpath = True
x.uses_equality = True
x.args = ['old-list', 'collation']
x.examples = [
    ]

x = Builtin_Function()
except__ = x
x.python_name = 'except__'
x.text = 'Returns a new list which contains exactly those items which are in list-1 and not in list-2. The order of the items in the new list is not specified.'
x.optional = ['collation']
x.from_xpath = True
x.uses_equality = True
x.args = ['list-1', 'list-2', 'collation']
x.examples = [
    ]

x = Builtin_Function()
get = x
x.python_name = 'get'
x.text = 'Return the item at the given position in the list'
x.optional = []
x.from_xpath = False
x.uses_equality = 'False'
x.args = ['list', 'position']
x.examples = [
    Example([[0, 1, 2, 3, 4], 0],0,''),
    Example([[0, 1, 2, 3, 4], 1],1,''),
    Example([[0, 1, 2, 3, 4], 4],4,''),
    Example([[0, 1, 2, 3, 4], -1],4,''),
    Example([[0, 1, 2, 3, 4], -5],0,''),
    Example([[0, 1, 2, 3, 4], -10],0,''),
    Example([[0, 1, 2, 3, 4], 5],'<em>unspecified</em>','')]

x = Builtin_Function()
index_of = x
x.python_name = 'index_of'
x.text = 'result is a list of integers i where compare_literal(get(list_1,i), match_value, collation)'
x.optional = []
x.from_xpath = True
x.uses_equality = True
x.args = ['list', 'match-value', 'collation']
x.examples = [
    Example([[0, 1, 2, 3, 4], 2],[2],''),
    Example([[0, 1, 2, 3, 4, 5, 2, 2], 2],[2, 6, 7],''),
    Example([[2, 2, 3, 4, 5, 2, 2], 2],[0, 1, 5, 6],''),
    Example([[2, 2, 3, 4, 5, 2, 2], 1],[],'')]

x = Builtin_Function()
insert_before = x
x.python_name = 'insert_before'
x.text = 'Return a new list which is ?old-list with ?new-item being inserted at the given ?position. The item in ?old-list which was at that position (if any) and any following items are shifted down one position.'
x.optional = []
x.from_xpath = True
x.uses_equality = 'False'
x.args = ['old-list', 'position', 'new-item']
x.examples = [
    Example([[0, 1, 2, 3, 4], 0, 99],[99, 0, 1, 2, 3, 4],''),
    Example([[0, 1, 2, 3, 4], 1, 99],[0, 99, 1, 2, 3, 4],''),
    Example([[0, 1, 2, 3, 4], 5, 99],[0, 1, 2, 3, 4, 99],''),
    Example([[0, 1, 2, 3, 4], 6, 99],[0, 1, 2, 3, 4, 99],''),
    Example([[0, 1, 2, 3, 4], 10, 99],[0, 1, 2, 3, 4, 99],''),
    Example([[0, 1, 2, 3, 4], -1, 99],[0, 1, 2, 3, 99, 4],''),
    Example([[0, 1, 2, 3, 4], -5, 99],[99, 0, 1, 2, 3, 4],''),
    Example([[0, 1, 2, 3, 4], -10, 99],[99, 0, 1, 2, 3, 4],'')]

x = Builtin_Function()
intersect = x
x.python_name = 'intersect'
x.text = 'Returns a new list which contains exactly those items which are in list-1 and in list-2. The order of the items in the new list is not specified.'
x.optional = ['collation']
x.from_xpath = True
x.uses_equality = True
x.args = ['list-1', 'list-2', 'collation']
x.examples = [
    ]

x = Builtin_Function()
remove = x
x.python_name = 'remove'
x.text = 'Return a new list which is old-list except that the item at the given ?position has been removed.'
x.optional = []
x.from_xpath = True
x.uses_equality = 'False'
x.args = ['old-list', 'position']
x.examples = [
    Example([[0, 1, 2, 3, 4], 0],[1, 2, 3, 4],''),
    Example([[0, 1, 2, 3, 4], 1],[0, 2, 3, 4],''),
    Example([[0, 1, 2, 3, 4], 4],[0, 1, 2, 3],''),
    Example([[0, 1, 2, 3, 4], 5],[0, 1, 2, 3, 4],''),
    Example([[0, 1, 2, 3, 4], 6],[0, 1, 2, 3, 4],''),
    Example([[0, 1, 2, 3, 4], -1],[0, 1, 2, 3],''),
    Example([[0, 1, 2, 3, 4], -5],[1, 2, 3, 4],''),
    Example([[0, 1, 2, 3, 4], -6],[1, 2, 3, 4],'')]

x = Builtin_Function()
reverse = x
x.python_name = 'reverse'
x.text = 'Return a new list, with all the items in reverse order'
x.optional = []
x.from_xpath = True
x.uses_equality = 'False'
x.args = ['old-list']
x.examples = [
    Example([[0, 1, 2, 3, 4]],[4, 3, 2, 1, 0],''),
    Example([[1]],[1],''),
    Example([[]],[],'')]

x = Builtin_Function()
sublist = x
x.python_name = 'sublist'
x.text = "Return a new list, containing (in order) the items starting at position 'start' and continuing up to, but not including, the 'stop' position. The 'stop' position may be omitted, in which case it defaults to the length of the list."
x.optional = ['stop']
x.from_xpath = True
x.uses_equality = 'False'
x.args = ['list', 'start', 'stop']
x.examples = [
    Example([[0, 1, 2, 3, 4], 0, 0],[],''),
    Example([[0, 1, 2, 3, 4], 0, 1],[0],''),
    Example([[0, 1, 2, 3, 4], 0, 4],[0, 1, 2, 3],''),
    Example([[0, 1, 2, 3, 4], 0, -2],[0, 1, 2],''),
    Example([[0, 1, 2, 3, 4], 2, 4],[2, 3],''),
    Example([[0, 1, 2, 3, 4], 2, -2],[2],''),
    Example([[0, 1, 2, 3, 4], 0],[0, 1, 2, 3, 4],''),
    Example([[0, 1, 2, 3, 4], 3],[3, 4],''),
    Example([[0, 1, 2, 3, 4], -2],[3, 4],'')]

x = Builtin_Function()
union = x
x.python_name = 'union'
x.text = 'Returns a new list which contains exactly those items which are in list-1 or in list-2. The order of the items in the new list is not specified.'
x.optional = ['collation']
x.from_xpath = True
x.uses_equality = True
x.args = ['list-1', 'list-2', 'collation']
x.examples = [
    Example([[0, 1, 2, 4], [3, 4, 5, 6]],[0, 1, 2, 4, 3, 5, 6],"But output order isn't specified")]

x = Builtin_Predicate()
deep_equal = x
x.python_name = 'deep_equal'
x.text = 'True only if list_1 and list_2 are both lists, are both the\n same length, and each item (in order) compares as equal using\n the proper datatype equality predicate (for the list_1 item).'
x.optional = ['collation']
x.from_xpath = True
x.uses_equality = 'False'
x.args = ['list_1', 'list_2', 'collation']
x.examples = [
    Example([[0, 1, 2, 3, 4], []],False,''),
    Example([[0, 1, 2, 3, 4], [1]],False,''),
    Example([[0, 1, 2, 3, 4], [0, 1, 2, 3, 4]],True,''),
    Example([[0, 1, 2, 3, 4], [0, 1, 2, 3, 4, 5]],False,''),
    Example([[0, 1, 2, 3, [0, 1, 2], 4], [0, 1, 2, 3, [0, 1, 2], 4]],True,''),
    Example([[0, 1, 2, 3, [0, 1, 2], 4], [0, 1, 2, 3, [0, 1, 3], 4]],False,'')]

x = Builtin_Predicate()
is_list = x
x.python_name = 'is_list'
x.text = 'A guard predicate, true if ?object is a list, and false otherwise.'
x.optional = []
x.from_xpath = False
x.uses_equality = 'False'
x.args = ['object']
x.examples = [
    Example([[0, 1, 2, 3]],True,''),
    Example([1],False,''),
    Example([[0, 1, 2, [3, 4]]],True,'')]

x = Builtin_Predicate()
list_contains = x
x.python_name = 'list_contains'
x.text = 'True only if ?item is datatype-equal some item in ?list (using the given ?collation, if provided.'
x.optional = ['collation']
x.from_xpath = True
x.uses_equality = True
x.args = ['list', 'item', 'collation']
x.examples = [
    Example([[0, 1, 2, 3, 4], 2],True,''),
    Example([[0, 1, 2, 3, 4, 5, 2, 2], 2],True,''),
    Example([[2, 2, 3, 4, 5, 2, 2], 1],False,''),
    Example([[], 1],False,''),
    Example([[0, 1, 2, 3, [7, 8]], [7, 8]],True,''),
    Example([[0, 1, 2, 3, [7, 8]], [7, 7]],False,'')]

functions.append(count)
functions.append(get)    # nth
functions.append(sublist)
functions.append(concatenate)
functions.append(insert_before)
functions.append(delete)
functions.append(reverse)

functions.append(index_of)
functions.append(remove)

functions.append(union)
functions.append(distinct_values)
functions.append(intersect)
functions.append(except__)

predicates.append(is_list)
predicates.append(list_contains)
predicates.append(deep_equal)


################################################################

################################################################

def sub(s):
    return s.replace('list-1', 'list<sub>1</sub>').replace('list-2', 'list<sub>2</sub>').replace('old-list', 'list<sub>1</sub>')

def qm(s):
    if s.startswith('?'):
        return s
    return '?'+s

def h(i):

    if i.from_xpath:
        if i.from_xpath == True:
            xname = i.name()
        else:
            xname = i.from_xpath
        adapted = "(adapted from <tt>[http://www.w3.org/TR/xpath-functions/#func-%s fn:%s]</tt>) " % (xname, xname)
    else:
        adapted = ""

    args = " ".join([qm(str(x)) for x in i.args])

    print ""
    print ""
    print ""
    print ""
    print "==== <tt>func:%s</tt> %s====" % (i.name(), adapted)
    print "<ul>"
    print "  <li>"
    print "    <em>Schema</em>:"
    print sub("      <p><tt>(%s; func:%s(%s))</tt></p>" % (args, i.name(), args))

    if i.optional:
        args2 = " ".join([qm(str(x)) for x in i.args if x not in i.optional])
        print sub("      <p><tt>(%s; func:%s(%s))</tt></p>" % (args2, i.name(), args2))

    print "  </li>"
    print "  <li>"
    print "    <em>Domains</em>:"
    print "      <p>... (to do)</p>"
    print "  </li>"
    print "  <li>"
    print "    <em>Informal Mapping</em>"
    print "      <p>"+sub(str(i.__doc__))+"</p>"


    print "      <p>If an argument value is outside of its domain, the value of the function is left unspecified.</p>"
    print "  </li>"
    if getattr(i, 'examples', False):
        print "  <li>"
        print "    <em>Examples</em>"
        lines = []
        for e in getattr(i, 'examples', []):
            s = "%s(%s) = %s" % (i.name(), " ".join([str(x) for x in e.args]), e.result)
            s = s.replace('[', 'list(').replace(']', ')').replace(",", " ")
            lines.append(s)
        print "      <pre>%s</pre>" % "\n".join(lines)
        print "  </li>"
    print "</ul>"


if True:


    print ""
    print ""
    print "=== Functions on RIF Lists ==="
    print ""
    print ""
    for i in functions:
        h(i)

    print ""
    print "=== Predicates on RIF Lists ==="
    print ""
    print ""
    for i in predicates:
        h(i)
    print

