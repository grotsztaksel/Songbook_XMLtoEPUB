# -*- coding: utf-8 -*-
"""
Created on Sat Nov 14 18:03:55 2020

@author: piotr
"""

__all__ = ['UtfSimplifier']

import re


class UtfSimplifier():
    """A class that converts a UTF string to ASCII
        - for example, to create reasonable file names
            
    """

    map_pl = {"Ą": "A",
              "ą": "a",
              "Ć": "C",
              "ć": "c",
              "Ę": "E",
              "ę": "e",
              "Ł": "L",
              "ł": "l",
              "Ń": "N",
              "ń": "n",
              "Ó": "O",
              "ó": "o",
              "Ś": "S",
              "ś": "s",
              "Ź": "z",
              "ź": "z",
              "Ż": "Z",
              "ż": "z"
              }
    map_de = {
        "Ä": "AE",
        "ä": "ae",
        "Ö": "OE",
        "ö": "oe",
        "Ü": "UE",
        "ü": "ue",
        "ß": "ss",
    }

    @staticmethod
    def toAscii(input: str) -> str:
        output = ""
        othersigns = re.compile("[^A-Za-z0-9 ]")

        for char in input:
            if char in UtfSimplifier.map_pl.keys():
                output += UtfSimplifier.map_pl[char]
            elif char in UtfSimplifier.map_de.keys():
                output += UtfSimplifier.map_de[char]
            else:
                output += char
        output = othersigns.sub("", output)
        return output
