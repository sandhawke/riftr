#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

Find a list of RDF Nodes from which an entire RDF graph can be reached
by forward arcs.

The nodes returned will either be nodes with no arcs pointing to them
(parentless nodes), or nodes somewhere in a ring and otherwise
unreachable.

Results are sorted in descending order of the number of other nodes
reachable from this one.

"""
import itertools

def find_roots(graph):
    roots = []
    already_reached = set()
    while True:
        (root, this_can_reach) = best_root(graph, already_reached)
        if root is None:
            break
        roots.append(root)
        already_reached.update(this_can_reach)
    return roots
       

def parentless_nodes(graph):
    result = set(graph.subjects())
    for parent, child in graph.subject_objects():
        result.discard(child)
    return result

def best_root(graph, ignore):
    """Find the root that can reach the most nodes, and return it and
    a set of all the nodes it can reach, which might not be all of
    them.  Ignore all the nodes in .ignore for this.  Return
    root==None if all nodes in the graph are ignored.

    (BUG: We can handle parentless nodes more efficiently than we do
    here.  This will evaluate them repeatedly.)
    """
    disqualified = set()
    best_reachable = set()
    best_node = None
    for node in itertools.chain(parentless_nodes(graph),graph.subjects()):
        if node in ignore:
            continue
        if node in disqualified:
            continue
        reachable = set()
        flood(node, graph, reachable, ignore)

        # Everything in 'reachable' is either a descendent of this node
        # (in which case it'll never be better) or we're in a loop with
        # it, in which case we're as good as it.  So, rule it out of
        # consideration.  This is what gives this algorithm some chance of
        # performing; we should only need to do a few floods.
        disqualified.update(reachable) 
        if len(reachable) > len(best_reachable):
            best_reachable = reachable
            best_node = node
    return best_node, best_reachable
    
def flood(node, graph, reachable, ignore):
    """Update reachable to also include all the nodes in the graph
    that are reachable from node, via forward arcs.  Ignore anything
    in ignore.
    """
    for obj in graph.objects(node):
        if obj not in reachable and obj not in ignore:
            reachable.add(obj)
            flood(obj, graph, reachable, ignore)
