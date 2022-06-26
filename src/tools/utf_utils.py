# -*- coding: utf-8 -*-
"""
Created on Sat Nov 14 18:03:55 2020

@author: Piotr Gradkowski <grotsztaksel@o2.pl>
"""
__authors__ = ['Piotr Gradkowski <grotsztaksel@o2.pl>']
__date__ = '2020-11-14'
__all__ = ['UtfUtils']

import re


class UtfUtils():
    """
    A bunch of tools for manipulating the strings containing UTF characters (like diacritic letters)
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
        """
        Simplifies the input string by replacing diacritic letters with ASCII characters taken from the maps.
        Can be used, for example, to create reasonable file names that will not confuse the OS
        """
        output = ""
        otherchars = re.compile("[^A-Za-z0-9 \.]")

        for char in input:
            if char in UtfUtils.map_pl.keys():
                output += UtfUtils.map_pl[char]
            elif char in UtfUtils.map_de.keys():
                output += UtfUtils.map_de[char]
            else:
                output += char
        # Simply remove characters that do not match the regexp otherchars
        output = otherchars.sub("", output)
        return output
