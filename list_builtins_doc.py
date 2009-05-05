#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

This is a partial database and generator for the documentation
of builtins.

At this writing, it just has the list builtins.


Domain...

Math...

IEXT(...)
II(...) = t / f


" The value space of xs:string for all arguments. "
Lists, for all arguments

DOMAIN:

  The range of ILIST [BLD 3.2 (item 5)], for all arguments list-1, ... list-n
    
MAPPING:

  Informally: this builtin returns a list containing the elements from
  list-1, ... list-n, in order.

  Formally: IEXT( ?arg1 ?arg2 ; concat (?arg1 ?arg2)) = IEXT(


MEMBER:

   II( ?item ?list ; member ( ?item ?list ) ) = t iff 


  

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

    def str(self, func):
        s = "%s(%s) = %s" % (func, 
                             " ".join([str(x) for x in self.args]), self.result)
        s = s.replace('[', 'List(').replace(']', ')').replace(",", " ")
        s = s.replace('  ', ' ')
        s = s.replace('  ', ' ')
        s = s.replace('  ', ' ')
        s = s.replace('  ', ' ')
        s = s.replace('  ', ' ')
        return s
 
class ManualExample:
    def __init__(self, text, comment=""):
        self.text = text
        self.comment = comment

    def __repr__(self):
        return ('ManulExample('
                +`self.text`+','
                +`self.comment`+')')

    def str(self, func):
        return self.text
        
class Builtin:

    #@classmethod
    #def name(cls):
    #    return cls.__name__.replace('__', '').replace('_', '-')

    def name(self):
        return self.python_name.replace('__', '').replace('_', '-')

    from_xpath = True
    optional = []

class Builtin_Predicate (Builtin) :
    
    is_builtin = True
    is_predicate = True

class Builtin_Function (Builtin) :

    is_builtin = True
    is_predicate = False


nary = ['list-1', '...', 'list-n']

x = Builtin_Function()
concatenate = x
x.python_name = 'concatenate'
x.text = 'Returns a list consisting of all the items in list-1, followed by all the items in list-i, for each i <= n.'
x.from_xpath = True
x.uses_equality = 'False'
x.args = nary
x.examples = [
    Example([[0, 1, 2], [3,4,5]],[0,1,2,3,4,5]),
    Example([[1, 1], [1], [1]],[1,1,1,1]),
    Example([[]],[]),
    Example([[],[1],[],[2]],[1,2]),
    ]

x = Builtin_Function()
count = x
x.python_name = 'count'
x.text = 'Returns the number of entries in the list (the length of the list).'
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
x.text = 'Returns a list which contains all the items in old-list, in the same order, except those which are equal to ?match-value.'
x.from_xpath = True
x.uses_equality = True
x.args = ['list-1', 'match-value']
x.domain = {'match-value': 'unrestricted'}
x.examples = [
    Example([[0,1,2,3,4], 2],[0,1,3,4]),
    Example([[0,1,2,3,4], 10],[0,1,2,3,4]),
    Example([[0,1,1,1,2,1,2], 1],[0,2,2]),
    ]

x = Builtin_Function()
distinct_values = x
x.python_name = 'distinct_values'
x.text = 'Returns a list which contains exactly those items which are in list-1, in the same order, except that additional occurances of any item are deleted.'
x.from_xpath = True
x.uses_equality = True
x.args = ['list-1']
x.examples = [
    Example([[0,1,2,3,4]], [0,1,2,3,4]),
    Example([[0,1,2,3,4,0,4]], [0,1,2,3,4]),
    Example([[3,3,3]], [3]),
    ]

x = Builtin_Function()
except__ = x
x.python_name = 'except__'
x.text = 'Returns a list which contains exactly those items which are in list-1 and not in list-2. The order of the items is the same as in list-1.'
x.from_xpath = True
x.uses_equality = True
x.args = ['list-1', 'list-2']
x.examples = [
    Example([[0,1,2,3,4], [1,3]], [0,2,4]),
    Example([[0,1,2,3,4], []], [0,1,2,3,4]),
    Example([[0,1,2,3,4], [0,1,2,3,4]], []),
    ]

x = Builtin_Function()
get = x
x.python_name = 'get'
x.text = 'Returns the item at the given position in the list'
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
    Example([[0, 1, 2, 3, 4], 5],"(unspecified)",'')]

x = Builtin_Function()
index_of = x
x.python_name = 'index_of'
x.text = 'Returns the ascending list of all integers, i>=0, such that get(list-1,i) = match_value'
x.from_xpath = True
x.uses_equality = True
x.args = ['list', 'match-value']
x.examples = [
    Example([[0, 1, 2, 3, 4], 2],[2],''),
    Example([[0, 1, 2, 3, 4, 5, 2, 2], 2],[2, 6, 7],''),
    Example([[2, 2, 3, 4, 5, 2, 2], 2],[0, 1, 5, 6],''),
    Example([[2, 2, 3, 4, 5, 2, 2], 1],[],'')]

x = Builtin_Function()
insert_before = x
x.python_name = 'insert_before'
x.text = 'Return a list which is ?list-1, except that ?new-item is inserted at the given ?position, with the item (if any) that was at that position, and all following items, shifted down one position.'
x.from_xpath = True
x.uses_equality = 'False'
x.args = ['list-1', 'position', 'new-item']
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
x.text = 'Returns a list which contains exactly those items which are list-i for i <= n. The order of the items in the returned is the same as the order in list-1.'
x.from_xpath = True
x.uses_equality = True
x.args = nary
x.examples = [
    Example([[0,1,2,3,4], [1,3]], [1,3]),
    Example([[0,1,2,3,4], [3,1]], [1,3]),
    Example([[0,1,2,3,4], []], []),
    Example([[0,1,2,3,4], [0,1,2,3,4,5,6]], [0,1,2,3,4]),
    ]

x = Builtin_Function()
remove = x
x.python_name = 'remove'
x.text = 'Returns a list which is list-1 except that the item at the given ?position has been removed.'
x.from_xpath = True
x.uses_equality = 'False'
x.args = ['list-1', 'position']
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
x.text = 'Return a list with all the items in list-1, but in reverse order'
x.from_xpath = True
x.uses_equality = 'False'
x.args = ['list-1']
x.examples = [
    Example([[0, 1, 2, 3, 4]],[4, 3, 2, 1, 0],''),
    Example([[1]],[1],''),
    Example([[]],[],'')]

x = Builtin_Function()
sublist = x
x.python_name = 'sublist'
x.text = "Returns a list, containing (in order) the items starting at position 'start' and continuing up to, but not including, the 'stop' position. The 'stop' position may be omitted, in which case it defaults to the length of the list."
x.optional = ['stop']
x.from_xpath = 'subsequence'
x.uses_equality = 'False'
x.args = ['list', 'start', 'stop']
x.examples = [
    Example([[0, 1, 2, 3, 4], 0, 0],[],''),
    Example([[0, 1, 2, 3, 4], 0, 1],[0],''),
    Example([[0, 1, 2, 3, 4], 0, 4],[0, 1, 2, 3],''),
    Example([[0, 1, 2, 3, 4], 0, 5],[0, 1, 2, 3, 4],''),
    Example([[0, 1, 2, 3, 4], 0, 10],[0, 1, 2, 3, 4],''),
    Example([[0, 1, 2, 3, 4], 0, -2],[0, 1, 2],''),
    Example([[0, 1, 2, 3, 4], 2, 4],[2, 3],''),
    Example([[0, 1, 2, 3, 4], 2, -2],[2],''),
    Example([[0, 1, 2, 3, 4], 0],[0, 1, 2, 3, 4],''),
    Example([[0, 1, 2, 3, 4], 3],[3, 4],''),
    Example([[0, 1, 2, 3, 4], -2],[3, 4],'')]

x = Builtin_Function()
make_list = x
x.python_name = 'make_list'
x.text = "Returns a list of the arguments item-0, ... item-n, in the same order they appear as arguments."
x.note ="This function is useful in RIF Core because the List construction operator is syntactically prohibited from being used with variables."
x.from_xpath = False
x.uses_equality = False
x.args = ['item-0', '...', 'item-n']
x.examples = [
    Example([0,1,2], [0,1,2]),
    Example([], []),
    Example([0], [0]),
    Example([[0,1,[20,21]]], [0,1,[20,21]]),
]


x = Builtin_Function()
union = x
x.python_name = 'union'
x.text = 'Returns a list containing all the items in list-1, ..., list-n, in the same order, but with all duplicates removed.   Equivalent to distinct_values(concatenate(list-1, ..., list-n)).'
x.from_xpath = True
x.uses_equality = True
x.args = ['list-1', '...', 'list-n']
x.examples = [
    Example([[0, 1, 2, 4], [3, 4, 5, 6]],[0, 1, 2, 4, 3, 5, 6]),
    Example([[0, 1, 2, 3], [4]],[0, 1, 2, 3, 4]),
    Example([[0, 1, 2, 3], [3]],[0, 1, 2, 3]),
]

# NO LONGER USED.
x = Builtin_Predicate()
deep_equal = x
x.python_name = 'deep_equal'
x.text = 'True only if list_1 and list_2 are both lists, are both the\n same length, and each item (in order) compares as equal using\n the proper datatype equality predicate (for the list_1 item).'
x.from_xpath = True
x.uses_equality = 'False'
x.args = ['list_1', 'list_2']
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
x.text = 'True only if ?item is in ?list.'
x.from_xpath = False
x.uses_equality = True
x.args = ['list', 'match-value']
x.examples = [
    Example([[0, 1, 2, 3, 4], 2],True,''),
    Example([[0, 1, 2, 3, 4, 5, 2, 2], 2],True,''),
    Example([[2, 2, 3, 4, 5, 2, 2], 1],False,''),
    Example([[], 1],False,''),
    Example([[0, 1, 2, 3, [7, 8]], [7, 8]],True,''),
    Example([[0, 1, 2, 3, [7, 8]], [7, 7]],False,'')]

predicates.append(is_list)

predicates.append(list_contains)   # member


functions.append(make_list)
functions.append(count)
functions.append(get)    # nth
functions.append(sublist)
functions.append(concatenate)
functions.append(insert_before)
functions.append(remove)
functions.append(reverse)
functions.append(index_of)
#functions.append(delete)
functions.append(union)
functions.append(distinct_values)     # 1-ary union?
functions.append(intersect)
functions.append(except__)



# compare
# sort --- needed to compare output of union?
#    count(a union b) == count(distinct_values(a)) == count(distinct_values(b))
#    

# implementation note: implementations may use a different data
# structure for the return value of the 'set operations', converting
# back to a list only when needed.  for instance, member, remove, and
# count do not require conversion to list.  The set representation
# could be something like a b-tree using the collation, or a hash
# table iff the collation provides a 'fold' operation which maps
# equivalent values onto the same output value.
#        for user-defined collations, you need a compare, and
#        it's also nice to have a 'fold'.


# min
# max
#   ... sort.get(0),   sort.get(-1)

# zip(list_1, ... list_n)    returns list of n-tuples
# range(start, stop, step)   returns list of start, start+step, etc, <stop
# codepoints(string, list_of_codepoints)

#  codepoints-to-string
#  string-to-codepoints

# map
# filter
# reduce

################################################################

################################################################

def sub(s):
    return s.replace('list-1', 'list<sub>1</sub>').replace('list-2', 'list<sub>2</sub>').replace('list-n', 'list<sub>n</sub>').replace('list-i', 'list<sub>i</sub>')

def qm(s):
    if s.startswith('?'):
        return s
    if s == "...":
        return s
    return '?'+s

def h(i, func="func"):

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
    print "==== <tt>"+func+":%s</tt> %s====" % (i.name(), adapted)
    print "<ul>"
    print "  <li>"
    print "    <em>Schema</em>:"
    print sub(("      <p><tt>(%s; "+func+":%s(%s))</tt></p>") % (args, i.name(), args))

    if i.optional:
        args2 = " ".join([qm(str(x)) for x in i.args if x not in i.optional])
        print sub(("      <p><tt>(%s; "+func+":%s(%s))</tt></p>") % (args2, i.name(), args2))

    print "  </li>"
    print "  <li>"
    print "    <em>Domains</em>:"
    #print "      <table>"
    print "      <p>"
    restricted = False
    for a in i.args:
        if a.startswith('list') or a.endswith('list'):
            domain = """[[BLD#def-Dlist|'''''D'''''<sub>list</sub>]]"""
            restricted = True
        elif a == "...":
            print "...<br/>"
            continue
            domain = "..."
        elif a == "position" or a=="start" or a=="stop":
            domain = "value space of xs:int"
            restricted = True
        elif a == "object" or a == "match-value" or a.startswith('item') or a.endswith('item'):
            domain = "unrestricted"
        elif a in getattr(i, 'domain', []):
            domain = i.domain[a]
            restricted = True
        else:
            domain = "<strong>ERROR!<strong>"

        #print "        <tr><th align=left>?%s</th><td>%s</td></tr>" % (a, domai)
        print "        ?%s: %s<br/>" % (a, domain)
    #print "      </table>"
    print "      </p>"
    print "  </li>"
    print "  <li>"
    print "    <em>Informal Mapping</em>"
    print "      <p>"+sub(str(i.text))+"</p>"

    if restricted:
        print "      <p>If an argument value is outside of its domain, the value of the function is left unspecified.</p>"

    if hasattr(i, 'note'):
        print "  </li>"
        print "  <li>"
        print "    <em>Note</em>"
        print "      <p>"+sub(str(i.note))+"</p>"


    print "  </li>"
    if getattr(i, 'examples', False):
        print "  <li>"
        print "    <em>Examples</em>"
        lines = []
        for e in getattr(i, 'examples', []):
            lines.append(e.str(i.name()))
        print "      <pre>%s</pre>" % ('\n'.join(lines))
        print "  </li>"
    print "</ul>"


if True:

    print "=== Predicates on RIF Lists ==="
    for i in predicates:
        h(i, "pred")
    print


    print ""
    print "=== Functions on RIF Lists ==="
    for i in functions:
        h(i)

