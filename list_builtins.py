"""
==== <tt>func:numeric-add</tt> (adapted from <tt>[http://www.w3.org/TR/xpath-functions/#func-numeric-add  op:numeric-add]</tt>) ====
<ul>
  <li>
     <em>Schema</em>: 
     <p>
       <tt>(?arg<sub>1</sub> ?arg<sub>2</sub>; func:numeric-add(?arg<sub>1</sub> ?arg<sub>2</sub>))</tt>
     </p>
  </li>
  <li>
    <em>Domains</em>:
    <p>
       The value spaces of <tt>xs:integer</tt>, <tt>xs:double</tt>, or <tt>xs:decimal</tt> for both arguments.
    </p>
  </li>
  <li>  
    <em>Mapping:</em> 
    <p>'''''I'''''<sub>external</sub>( (?arg<sub>1</sub> ?arg<sub>2</sub>; func:numeric-add(?arg<sub>1</sub> ?arg<sub>2</sub>) )(a<sub>1</sub> a<sub>2</sub>) = ''res'' such that ''res'' is the result of [http://www.w3.org/TR/xpath-functions/#func-numeric-add  op:numeric-add](a<sub>1</sub>, a<sub>2</sub>) as defined in <nowiki>[</nowiki>[[#ref-xpath-functions|XPath-Functions]]], in case both a<sub>1</sub> and a<sub>2</sub> belong to their domains.
    </p>
    <p>
       If an argument value is outside of its domain, the value of the function is left unspecified.
    </p>
  </li>
</ul>

"""

import sys

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


class is_list ( Builtin_Predicate ):
    """A guard predicate, true if ?object is a list, and false otherwise."""
    args = ['object']

    from_xpath = False

    examples = [
        Example([[0,1,2,3]], True),
        Example([1], False),
        Example([[0,1,2,[3,4]]], True),
        ]

    @classmethod
    def run(self, object, collation=None):
        return type(object) == type([])


class deep_equal ( Builtin_Predicate ):

    """True only if list_1 and list_2 are both lists, are both the
    same length, and each item (in order) compares as equal using
    the proper datatype equality predicate (for the list_1 item).
    """

    issue = """What if the datatype of list_1[i] says they are equal and the datatype of list_2[i] says they are not?"""

    args = ['list_1', 'list_2', 'collation']
    optional = ['collation']

    examples = [
        Example([[0,1,2,3,4], []], False),
        Example([[0,1,2,3,4], [1]], False),
        Example([[0,1,2,3,4], [0,1,2,3,4]], True),
        Example([[0,1,2,3,4], [0,1,2,3,4,5]], False),
        Example([[0,1,2,3,[0,1,2], 4], [0,1,2,3,[0,1,2], 4]], True),
        Example([[0,1,2,3,[0,1,2], 4], [0,1,2,3,[0,1,3], 4]], False),
        ]

    @classmethod
    def run(self, list_1, list_2, collation=None):
        if len(list_1) == len(list_2) :
            for i in range(0, len(list_1)):
                if 0==compare_literal.run(list_1[i],
                                          list_2[i]):
                    pass
                else:
                    return False
            return True
        return False

class concatenate ( Builtin_Function ):
    """
    Returns a new list consisting of all the items in list-1 followed by all the items in list-2.
    """

    args = ['list-1', 'list-2']
    result = 'new-list'
    issue="This is a poor name.   'concat' is used for strings; perhaps 'list-concat' would be better, but XPath uses 'concatenate'"

    @classmethod
    def run(self, first_list, second_list):
        return first_list + second_list

class insert_before ( Builtin_Function ):
    """Return a new list which is ?old-list with ?new-item being inserted at the given ?position.  The item in ?old-list which was at that position (if any) and any following items are shifted down one position."""

    args =  ['old-list', 'position', 'new-item']
    result = 'new-list'

    examples = [
        Example([[0,1,2,3,4], 0, 99], [99, 0,1,2,3,4]),
        Example([[0,1,2,3,4], 1, 99], [0,99, 1, 2,3,4]),
        Example([[0,1,2,3,4], 5, 99], [0,1, 2,3,4, 99]),
        Example([[0,1,2,3,4], 6, 99], [0,1, 2,3,4, 99]),
        Example([[0,1,2,3,4], 10, 99], [0,1, 2,3,4, 99]),
        Example([[0,1,2,3,4], -1, 99], [0,1, 2,3, 99, 4]),
        Example([[0,1,2,3,4], -5, 99], [99, 0, 1, 2,3,4]),
        Example([[0,1,2,3,4], -10, 99], [99, 0, 1, 2,3,4]),
        ]

    @classmethod
    def run(self, old_list, position, new_item):
        return old_list[0:position] + [new_item] + old_list[position:]

class remove ( Builtin_Function ):
    """Return a new list which is old-list except that the item at the given ?position has been removed."""

    args =  ['old-list', 'position']
    result = 'new-list'

    examples = [
        Example([[0,1,2,3,4], 0], [1,2,3,4]),
        Example([[0,1,2,3,4], 1], [0,2,3,4]),
        Example([[0,1,2,3,4], 4], [0,1,2,3]),
        Example([[0,1,2,3,4], 5], [0,1,2,3,4]),
        Example([[0,1,2,3,4], 6], [0,1,2,3,4]),
        Example([[0,1,2,3,4], -1], [0,1,2,3]),
        Example([[0,1,2,3,4], -5], [1,2,3,4]),
        Example([[0,1,2,3,4], -6], [1,2,3,4]),
        ]

    @classmethod
    def run(self, old_list, position):
        if position < 0:
            position = len(old_list) + position
            if position  < 0:
                position = 0
        return old_list[0:position] + old_list[position+1:]

class count( Builtin_Function ):
    """Return the number of items in the list (the length of the list)."""
    
    args =  ['list']
    result = 'numberOfItems'

    examples = [
        Example([[0,1,2,3,4]], 5),
        Example([[0]], 1),
        Example([[0,0,0]], 3),
        Example([[]], 0),
        ]


    @classmethod
    def run(self, list):
        return len(list)

class get ( Builtin_Function ):
    """Return the item at the given position in the list"""

    args =  ['list', 'position']
    result = 'item'

    from_xpath = False

    examples = [
        Example([[0,1,2,3,4], 0], 0),
        Example([[0,1,2,3,4], 1], 1),
        Example([[0,1,2,3,4], 4], 4),
        Example([[0,1,2,3,4], -1], 4),
        Example([[0,1,2,3,4], -5], 0),
        Example([[0,1,2,3,4], -10], 0),
        Example([[0,1,2,3,4], 5], "<em>unspecified</em>"),
        ]

    @classmethod
    def run(self, list, position):
        if position < 0:
            position = len(list) + position
            if position  < 0:
                position = 0
        return list[position]

class reverse ( Builtin_Function ):
    """Return a new list, with all the items in reverse order"""

    args =  ['old-list']
    result = 'new-list'
    
    examples = [
        Example([[0,1,2,3,4]], [4,3,2,1,0]),
        Example([[1]], [1]),
        Example([[]], []),
    ]

    @classmethod
    def run(self, old_list):
        l = old_list[:]
        l.reverse()
        return l

class sublist ( Builtin_Function ):
    """Return a new list, containing (in order) the items starting at position 'start' and continuing up to, but not including, the 'stop' position.   The 'stop' position may be omitted, in which case it defaults to the length of the list."""

    note = "sublist differs from xpath's subsequence function in using a 'stop' position parameter instead of a 'length' parameter (in addition to the name change, and the zero-based indexing."

    args =  ['list', 'start', 'stop']
    optional = ['stop']
    result = 'new-list'

    examples = [
        Example([[0,1,2,3,4], 0, 0], []),
        Example([[0,1,2,3,4], 0,1], [0]),
        Example([[0,1,2,3,4], 0, 4], [0,1,2,3]),
        Example([[0,1,2,3,4], 0, -2], [0,1,2]),
        Example([[0,1,2,3,4], 2, 4], [2,3]),
        Example([[0,1,2,3,4], 2, -2], [2]),
        Example([[0,1,2,3,4], 0], [0,1,2,3,4]),
        Example([[0,1,2,3,4], 3], [3,4]),
        Example([[0,1,2,3,4], -2], [3,4]),
    ]

    @classmethod
    def run(self, list, start, stop=None):
        if stop is None:
            return list[start:]
        else:
            return list[start:stop]



class index_of ( Builtin_Function ):
    """result is a list of integers i where compare_literal(get(list_1,i), match_value, collation)"""

    args =  ['list', 'match-value', 'collation']
    result = 'listOfIndices'

    uses_equality = True

    examples = [
        Example([[0,1,2,3,4], 2], [2]),
        Example([[0,1,2,3,4,5,2,2], 2], [2,6,7]),
        Example([[2,2,3,4,5,2,2], 2], [0,1,5,6]),
        Example([[2,2,3,4,5,2,2], 1], []),
        ]

    @classmethod
    def run(self, list, match_value, collation=None):
        result = []
        for position in range(0, len(list)):
            if 0==compare_literal.run(list[position], match_value, collation):
                result.append(position)
        return result
        
class list_contains  ( Builtin_Predicate ):
    """True only if ?item is datatype-equal some item in ?list (using the given ?collation, if provided."""

    args = ['list', 'item', 'collation']
    optional = ['collation']


    examples = [
        Example([[0,1,2,3,4], 2], True),
        Example([[0,1,2,3,4,5,2,2], 2], True),
        Example([[2,2,3,4,5,2,2], 1], False),
        Example([[], 1], False),
        Example([[0,1,2,3,[7,8]], [7,8]], True),
        Example([[0,1,2,3,[7,8]], [7,7]], False),
        ]

    @classmethod
    def run(self, list, match_value, collation=None):
        for position in range(0, len(list)):
            if 0==compare_literal.run(list[position], match_value, collation):
                return True
        return False

    uses_equality = True


class union ( Builtin_Function ):
    """Returns a new list which contains exactly those items which are in list-1 or in list-2.   The order of the items in the new list is not specified."""

    args =  ['list-1', 'list-2', 'collation']
    optional = ['collation']
    result = 'new-list'

    uses_equality = True

    examples = [
        Example([[0,1,2,4], [3,4,5,6]], [0,1,2,4,3,5,6], "But output order isn't specified"),
        ]

    @classmethod
    def run(self, list_1, list_2, collation=None):
        """
        We might want to try sometimes keeping lists in a sorted order,
        or even some hash'd structure.

        Of course we should do a sort-and-compare-in-order to get to n-log-n
        performance...
        """
        return distinct_values.run(list_1 + list_2, collation)

class intersect ( Builtin_Function ):
    """Returns a new list which contains exactly those items which are in list-1 and in list-2.   The order of the items in the new list is not specified."""

    args =  ['list-1', 'list-2', 'collation']
    optional = ['collation']
    result = 'new-list'

    uses_equality = True

    @classmethod
    def run(self, list_1, list_2, collation=None):
        result = []
        for item in list_1:
            if list_contains.run(list_2, item, collation):
                result.append(item)
        return result

class except__ ( Builtin_Function ):
    """Returns a new list which contains exactly those items which are in list-1 and not in list-2.   The order of the items in the new list is not specified."""

    args =  ['list-1', 'list-2', 'collation']
    optional = ['collation']
    result = 'new-list'

    uses_equality = True

    @classmethod
    def run(self, list_1, list_2, collation=None):
        result = []
        for item in list_1:
            if not list_contains.run(list_2, item, collation):
                result.append(item)
        return result


class distinct_values ( Builtin_Function ):
    """Returns a new list which contains exactly those items which are in list-1, but without any two items being equal.   The order of the items in the new list is not specified."""

    args =  ['old-list', 'collation']
    result = 'new-list'

    uses_equality = True

    @classmethod
    def run(self, list_1, list_2, collation=None):
        result = []
        for item in list_1:
            if not list_contains.run(result, item, collation):
                result.append(item)
        return result

class delete( Builtin_Function ):

    """Return a list which contains all item in old-list,
    in the same order except those which are datatype-equal to
    ?match-value."""

    args =  ['old-list', 'match-value', 'collation']
    optional = ['collation']
    result = 'new-list'

    from_xpath = True

    uses_equality = True

    @classmethod
    def run(self, list, match_value, collation=None):
        
        result = []
        for item in list:
            if 0==compare_literal.run(item, match_value, collation):
                pass
            else:
                result.append(item)
                return True
        return False

    uses_equality = True



class compare_literal : # DONT CALL IT A ( Builtin_Predicate ):


    args =  ['value_1', 'value_2', 'collation']

    uses_equality = True

    examples = [
        Example([[0,1,2,3,4], []], 1),
        Example([[0,1,2,3,4], [1]], 1),
        Example([[0,1,2,3,4], [0,1,2,3,4,4]], 1),
        Example([[0,1,2,3,4], [0,1,2,3,4]], 0),
        Example([[0,1,2,3,4], [0,1,2,3,4,6]], -1),
        Example([[0,1,2,3,4], [2]], -1),
        Example([[0,1,2,3,[0,1,2], 4], [0,1,2,3,[0,1,1], 4]], 1),
        Example([[0,1,2,3,[0,1,2], 4], [0,1,2,3,[0,1,2], 4]], 0),
        Example([[0,1,2,3,[0,1,2], 4], [0,1,2,3,[0,1,3], 4]], -1),

        ]



    @classmethod
    def run(self, value_1, value_2, collation=None):
        
        # we assign a total order over all literals.

        # what if the types are different?

        # maybe cmp does it for us, already?

        if collation is not None:
            raise RuntimeError('string compare with collation - not implemented')
        return cmp(value_1, value_2)

    uses_equality = True


# what if it's not a string....???
#
#   Each collation defines a total order on literals.
#
class codepoint_collation :

    @classmethod
    def run(self, a, b):
        
        return cmp(a,b)
    
class case_insensitive_collation :
    
    @classmethod
    def run(self, a, b):
        return cmp(a.lower(),b.lower())


predicates = []
functions = []
mod = sys.modules["__main__"]
for x in dir(mod):
    if x is "Builtin_Function" or x is "Builtin_Predicate":
        continue
    y = getattr(mod, x)
    if getattr(y, 'is_builtin', False):
        if getattr(y, 'is_predicate', False):
            predicates.append(y)
        else:
            functions.append(y)

def p(i):
    print '  ', i.name(),
    print '(',
    for a in i.args:
        print a,
    print ')'

    print '  ==> ', getattr(i, '__doc__', '(no documentation)')

    for e in getattr(i, 'examples', []):
        print "        %s(%s) = %s" % (i.name(), " ".join([str(x) for x in e.args]), e.result),
        result = i.run(*e.args)
        if result == e.result:
            print
        else:
            print '  ** really', result
        

if False:
    print 'predicates:'
    for i in predicates:
        q(i)
    print

    print 'functions:'
    for i in functions:
        p(i)

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
    print "<li>"
    print "<em>Schema</em>:"
    print sub("<p><tt>(%s; func:%s(%s))</tt></p>" % (args, i.name(), args))

    if i.optional:
        args2 = " ".join([qm(str(x)) for x in i.args if x not in i.optional])
        print sub("<p><tt>(%s; func:%s(%s))</tt></p>" % (args2, i.name(), args2))

    print "</li>"
    print "<li>"
    print "<em>Domains</em>:"
    print "<p>... (to do)</p>"
    print "</li>"
    print "<li>"
    print "<em>Informal Mapping</em>"
    print "<p>"+sub(str(i.__doc__))+"</p>"


    print "<p>If an argument value is outside of its domain, the value of the function is left unspecified.</p>"
    print "</li>"
    if getattr(i, 'examples', False):
        print "<li>"
        print "<em>Examples</em>"
        print "<pre>"
        for e in getattr(i, 'examples', []):
            s = "%s(%s) = %s" % (i.name(), " ".join([str(x) for x in e.args]), e.result)
            s = s.replace('[', 'list(').replace(']', ')').replace(",", " ")
            print s

            try:
                result = i.run(*e.args)
            except IndexError:
                result = "<em>unspecified</em>"

            if result != e.result:
                print >>sys.stderr, s, '  ** really', result
        print "</pre>"
        print "</li>"
    print "</ul>"


if False:


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


def pp(x):

    name = "x"
    if x.is_predicate:
        print name+" = Builtin_Predicate()"
    else:
        print name+" = Builtin_Function()"
    print x.__name__ + " = x"
    print name+".python_name = "+`x.__name__`
    # print name+".name = "+`x.name()`
    print name+".text = "+`x.__doc__.strip().replace('    ', ' ').replace('  ', ' ').replace('  ', ' ').replace('  ', ' ')`
    print name+'.optional = '+`x.optional`
    print name+'.from_xpath = '+`x.from_xpath`
    print name+'.uses_equality = '+`getattr(x, 'uses_equality', 'False')`
    print name+".args = "+`x.args`
    print name+".examples = [\n    "+",\n    ".join([repr(y) for y in getattr(x, 'examples', [])])+"]"
    print 

if True:
    for i in functions + predicates:
        pp(i)
    for x in functions:
        print "functions.append(%s)" % x.__name__
    print
    for x in predicates:
        print "predicates.append(%s)" % x.__name__
