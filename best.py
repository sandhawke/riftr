#!/usr/bin/env python2.5
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

Support AST2 with a "best value" function, a bit like "the", but
allowing there to be multiple values (maybe even pushing for inference
of additional values), and picking the best one for your purpose.

(Could, alternatively, work against a triplestore.  Hrm....  In that
case we'd want a graph...)


    VERY ROUGH SKETCH, now add inference....

       * while backward chaining is good, I think we want
         to keep the results....

         (do it all in prolog?)

      * selection of rules / rulesets includes product of impact.

           just have a cost of the rule and do iterative deepening?

"""


class UsageContext (object):

    def __init__(self, **kwargs):
        self.good_enough = 0.99
        self.__dict__.update(kwargs)

    def best(self, inst, prop):

        best_value = None
        best_quality = -1
        for value in getattr(inst, prop).values:
            q = self.quality(inst, prop, value)
            if q > best_quality:
                best_quality = q
                best_value = value
                if q > self.good_enough:
                    return value
        if value is None:
            raise Exception
        return value

    def quality(self, inst, prop, value):
        """Return a score 0..1 indicating how good this
        triple is, in this usage context.
        
        Override this, for different usage contexts?
        """
        return 1.00
