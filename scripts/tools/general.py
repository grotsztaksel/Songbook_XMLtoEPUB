# -*- coding: utf-8 -*-
"""
Created on 05.06.2021 22:37 06
 
@author: Piotr Gradkowski <grotsztaksel@o2.pl>

A collection of general purpose utils that can be used in each class

"""

__all__ = ['escapeQuoteMarks']
__date__ = '2021-06-05'
__authors__ = ["Piotr Gradkowski <grotsztaksel@o2.pl>"]

from scripts.tixi import Tixi


def escapeQuoteMarks(tixi: Tixi):
    """
    Replace all single and double quotes in attributes with &apos; and &quot; , respectively
    """
    for path in tixi.xPathExpressionGetAllXPaths("//*[@*]"):
        # xpath expression means all elements that have any attributes
        for i in range(tixi.getNumberOfAttributes(path)):
            attr = tixi.getAttributeName(path, i + 1)
            value = tixi.getTextAttribute(path, attr)
            value1 = value.replace("'", "&apos;")
            value1 = value1.replace('"', "&quot;")
            if value == value1:
                continue
            tixi.addTextAttribute(path, attr, value1)
