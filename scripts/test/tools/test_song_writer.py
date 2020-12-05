# -*- coding: utf-8 -*-
"""
Created on 16.11.2020 22:14
 
@author: piotr
"""

import unittest

from config import EpubSongbookConfig
from tixi import Tixi, TixiException, ReturnCode
from tools.song_writer import SongWriter, LineWithChords


class TestSongWriter(unittest.TestCase):
    def setUp(self):
        # Need a Tixi object to initialize the EpubSongbookConfig
        cfgTixi = Tixi()
        cfgTixi.create("songbook")
        self.settings = EpubSongbookConfig(cfgTixi)
        self.settings.CS = ">"
        self.settings.CI = "|"

    def test_write_chors_above(self):
        src_tixi = Tixi()
        src_tixi.open("test_song.xml")
        writer = SongWriter(src_tixi, self.settings, "/song")
        writer.tixi.createElement("/html", "body")
        # "/html" is ok, because the function doesn't really check where the target is
        writer.write_chords_above("/song/verse[1]", "/html/body")

        expectedTixi = Tixi()
        expectedTixi.open("expected_test_song.xhtml")
        expectedTixi.registerNamespace("http://www.w3.org/1999/xhtml", "x")
        # Need to trim it a little - don't want things we're not checking
        expectedTixi.removeElement("/x:html/x:body/x:h1")
        self.assertTrue(expectedTixi.checkAttribute("/x:html/x:body/x:p[1]", "class"))
        self.assertEqual("authors", expectedTixi.getTextAttribute("/x:html/x:body/x:p[1]", "class"))
        expectedTixi.removeElement("/x:html/x:body/x:p[1]")

        self.assertIn("Now a verse without any chords", expectedTixi.getTextElement("/x:html/x:body/x:p[2]"))
        expectedTixi.removeElement("/x:html/x:body/x:p[2]")
        # Now removing the last <p/> without checking!
        expectedTixi.removeElement("/x:html/x:body/x:p[2]")
        self.assertEqual(1, expectedTixi.getNamedChildrenCount("/x:html/x:body", "x:p"))
        expectedTixi.removeAttribute("/x:html/x:body/x:p", "class")
        texts = []

        td_all = expectedTixi.getPathsFromXPathExpression("//x:td")
        td_txt = expectedTixi.getPathsFromXPathExpression("//x:td[text()]")

        for path in td_all:
            if path in td_txt:
                continue
            expectedTixi.updateTextElement(path, "")

        # If we're still here, the expectedTixi has been properly formed.
        self.assertEqual(expectedTixi.exportDocumentAsString(),
                         writer.tixi.exportDocumentAsString())

    def test_identifyLinesWithChords(self):
        text = "\n".join(["Line 1",
                          "Line 2",
                          "Line 3",
                          "Line 4"])

        # Should basically get the text with <br/> tags in newlines
        self.assertEqual([text.replace("\n", "<br/>\n")], SongWriter._identifyLinesWithChords(text))

        text = "\n".join(["Line 1" + self.settings.CS + "F E E D",
                          "Line 2" + self.settings.CS + "F E E D",
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
