# -*- coding: utf-8 -*-
"""
Created on 20.11.2020 19:02
 
@author: piotr
"""
__all__ = ["Song"]

from collections import namedtuple

Song = namedtuple("Song", ["file", "title", "xml"])