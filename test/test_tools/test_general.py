# -*- coding: utf-8 -*-
"""
Created on 05.06.2021 23:17 06
 
@author: Piotr Gradkowski <grotsztaksel@o2.pl>
"""

__date__ = '2021-06-05'
__authors__ = ["Piotr Gradkowski <grotsztaksel@o2.pl>"]

import unittest
from scripts.tixi import Tixi
from scripts.tools.general import escapeQuoteMarks, getDefaultSongAttributes
from scripts.config import epubsongbookconfig  # Only to access the XSD file
import os


class TestGeneral(unittest.TestCase):
    """A class testing the general utilities"""

    def test_escapeQuoteMarks(self):
        references = os.path.join(os.path.abspath(os.path.dirname(__file__)), "resources")
        test_song_src = os.path.join(references, "test_song_src.xml")
        tixi = Tixi()
        tixi.open(test_song_src)
        self.assertEqual("You'll never see me", tixi.getTextAttribute("/songbook/section[3]/song[1]", "title"))
        self.assertEqual("You'll never see me again",
                         tixi.getTextAttribute("/songbook/section[3]/song[2]", "title"))

        tixi.addTextAttribute("/songbook/section[3]/song[1]", "title", "You\"ll never see me")

        escapeQuoteMarks(tixi)
        self.assertEqual("You&quot;ll never see me",
                         tixi.getTextAttribute("/songbook/section[3]/song[1]", "title"))
        self.assertEqual("You&apos;ll never see me again",
                         tixi.getTextAttribute("/songbook/section[3]/song[2]", "title"))

    def test_getDefaultSongAttributes(self):
        xsd = os.path.abspath(os.path.join(os.path.dirname(epubsongbookconfig.__file__), "song_schema.xsd"))
        self.assertTrue(os.path.isfile(xsd))
        self.assertEqual({"include": "true", "lyrics": "trad.", "music": "trad."}, getDefaultSongAttributes(xsd))


if __name__ == '__main__':
    unittest.main()
