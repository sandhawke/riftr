"""

Fairly simple implementation of all the RIF list-handling builtins.

"""

def is_list(object):
    return type(object) == type([])

def list_contains(list, match_value):
    return match_value in list

def make_list(*args):
    return [x for x in args]

def append(list, *args):
    return list + [x for x in args]

def count(list):
    return len(list)

def get(list, position):
    return list[position]

def sublist(list, start, stop=None):
    if stop is None:
        return list[start:]
    else:
        return list[start:stop]

def concatenate(*args):
    result = []
    for arg in args:
        result.extend(arg)
    return result

def insert_before(old_list, position, new_item):
    dummy = old_list[position]  # raise an index error if no such element
    return old_list[0:position] + [new_item] + old_list[position:]

def remove(old_list, position):
    if position < 0:
        position += len(old_list)
        if position < 0:
            raise IndexError
    dummy = old_list[position]  # raise an index error if no such element
    return old_list[0:position] + old_list[position+1:]

def reverse(old_list):
    l = old_list[:]
    l.reverse()
    return l

def index_of(list, match_value):
    result = []
    for position in range(0, len(list)):
        if list[position] ==  match_value:
            result.append(position)
    return result


def union(*args):
    return distinct_values(concatenate(*args))

def intersect(*args):

    # convert all the args after the first into sets, since we'll
    # have to check for membership in each of them many times.
    sets = []
    for other in args[1:]:
        sets.append(set(other))

    result = []
    for item in args[0]:
        in_all = True
        for other in sets:
            if item not in other:
                in_all = False
        if in_all:
            result.append(item)
    return result

def except__(list_1, list_2):
    result = []
    set_2 = set(list_2)
    for item in list_1:
        if item not in set_2:
            result.append(item)
    return result


def distinct_values(list_1):
    result = []
    s = set()
    for item in list_1:
        if item not in s:
            result.append(item)
            s.add(item)
    return result

def delete(list, match_value):
    result = []
    for item in list:
        if item != match_value:
            result.append(item)
    return result


def _run_examples(i):

    import list_builtins
    passed = 0
    failed = 0

    for e in getattr(i, 'examples', []):
        f = getattr(list_builtins, i.python_name)
        try:
            result = f(*e.args)
        except IndexError:
            result = "(unspecified)"
        if result == e.result:
            pass
            passed += 1
        else:
            failed += 1
            print >>sys.stderr, "        %s(%s) = %s" % (i.name(), " ".join([str(x) for x in e.args]), e.result),
            print >>sys.stderr, '  ** but got', result

    return (passed, failed)

if __name__ == "__main__":

    import sys
    import list_builtins_doc

    print "Running tests"
    for i in list_builtins_doc.predicates + list_builtins_doc.functions:
        (p, f) = _run_examples(i)
        print "* %-16s passed=%3i  failed=%3i" % (i.name(), p, f)
    print "Done."
