# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

from tixi3.tixi3wrapper import Tixi3 as Tixi
import os
import sys

class config(object):
    def __init__(self):
        super(config,self).__init__()
        self.outputDir = os.path.abspath("../output")


def main(argv):
    
    cfg = config()
    print(cfg.outputDir)
    

    


main(sys.argv)