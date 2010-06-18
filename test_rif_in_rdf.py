#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""

"""

import sys
from cStringIO import StringIO
import re
import os

import rif_in_rdf


def test2():
    
    tc = "/home/sandro/5/rules/test/repository/tc"
    
    for root, dirs, files in os.walk(tc):
        for filename in files:
            if filename.endswith("-premise.rif"):
                
                absf = root+"/"+filename
                print absf

                rif_in_rdf.from_file(absf)

if __name__=="__main__":
    test2()                    
