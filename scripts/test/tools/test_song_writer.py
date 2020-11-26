# -*- coding: utf-8 -*-
"""
Created on 16.11.2020 22:14
 
@author: piotr
"""

import unittest

from config import CFG
from tools.song_writer import SongWriter, LineWithChords


class TestSongWriter(unittest.TestCase):
    def test_identifyLinesWithChords(self):
        text = "\n".join(["Line 1",
                          "Line 2",
                          "Line 3",
                          "Line 4"])

        # Should basically get the text with <br/> tags in newlines
        self.assertEqual([text.replace("\n", "<br/>\n")], SongWriter._identifyLinesWithChords(text))

        text = "\n".join(["Line 1" + CFG.CS + "F E E D",
                          "Line 2" + CFG.CS + "F E E D",
                          "Line 3",
                          "Line 4"])
        expected = [
            LineWithChords("Line 1", ["F E E D"]),
            LineWithChords("Line 2", ["F E E D"]),
            "Line 3<br/>\nLine 4"
        ]
        self.assertEqual(expected, SongWriter._identifyLinesWithChords(text))


if __name__ == '__main__':
    unittest.main()
