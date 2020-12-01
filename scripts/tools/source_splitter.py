# -*- coding: utf-8 -*-
"""
Created on 01.12.2020 18:52
 
@author: piotr
"""
import os
import re


class SourceSplitter(object):
    """Read in the source song file and produce a number of smaller song out of it.
    Might be useful, if your songbook source becomes large and your text edior
    gets sluggish with it.
    """

    def __init__(self, src):
        self.src = src
        self.dir = os.path.dirname(self.src)

    @staticmethod
    def deIndent(text):
        """Find the beginning of the first xml tag, count the number of preceding spaces
        and remove the same number of spaces from the beginning of each line"""

        n_spaces = text.find("<")
        if n_spaces < 0:
            return text

        output = []
        for line in text.split("\n"):
            output.append(line[n_spaces:])

        return "\n".join(output)
