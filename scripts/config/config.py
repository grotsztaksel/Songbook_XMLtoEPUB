# -*- coding: utf-8 -*-
"""
Created on Sat Nov 14 17:32:27 2020

@author: piotr
"""

__all__ = ['ChordMode', 'CFG']

import os
from enum import Enum


class ChordMode(Enum):
    """
    CHORD_ABOVE - the chords will be written above the text, indicating the place, where the chord should be played
    CHORD_BESIDE - the chords will be listed to the right of the line
    NO_CHORD - the chords will not be written alltogether
    """
    CHORDS_ABOVE = 0
    CHORDS_BESIDE = 1
    NO_CHORDS = 2


class config():
    ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../")
    OUTPUT_DIR = os.path.join(ROOT_DIR, "output")
    SONG_SRC_DIR = os.path.join(ROOT_DIR, "song_src")
    SONG_SRC_XML = os.path.join(SONG_SRC_DIR, "songs_src.xml")
    SONG_HTML_DIR = os.path.join(OUTPUT_DIR, "text")
    MODE = ChordMode.CHORDS_BESIDE

    CS = ">"  # [C]hord [S]eparator: character that separates the text from chords lists
    CI = "|"  # [C]hord [I]nsertion point: character indicating the location where the chord should be changed
    #                                      while performing the song


CFG = config()
