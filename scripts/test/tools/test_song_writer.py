# -*- coding: utf-8 -*-
"""
Created on 16.11.2020 22:14
 
@author: piotr
"""

import unittest

from config import EpubSongbookConfig, ChordMode
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

    def test_write_song_header(self):
        src_tixi = Tixi()
        src_tixi.create("song")
        writer = SongWriter(src_tixi, self.settings, "/song")

        # ------------------
        attrs = {
            "lyrics": "J. Doe",
            "music": "Sam Composer",
            "band": "The Developers"
        }
        TestSongWriter.updateAttributes(src_tixi, "/song", attrs)

        writer.write_song_header("My Lovely Song")

        self.assertEqual("lyrics by: J. Doe, music by: Sam Composer (The Developers)",
                         writer.tixi.getTextElement("/html/body/p"))
        writer.tixi.removeElement("/html/body")

        # ------------------
        attrs = {
            "lyrics": None,
            "music": "Sam Composer",
            "band": "The Developers"
        }
        TestSongWriter.updateAttributes(src_tixi, "/song", attrs)

        writer.write_song_header("My Lovely Song")

        self.assertEqual("lyrics by: ?, music by: Sam Composer (The Developers)",
                         writer.tixi.getTextElement("/html/body/p"))
        writer.tixi.removeElement("/html/body")

        # ------------------
        attrs = {
            "lyrics": None,
            "music": None,
            "band": "The Developers"
        }
        TestSongWriter.updateAttributes(src_tixi, "/song", attrs)

        writer.write_song_header("My Lovely Song")

        self.assertEqual("The Developers",
                         writer.tixi.getTextElement("/html/body/p"))
        writer.tixi.removeElement("/html/body")

        # ------------------
        attrs = {
            "lyrics": "J. Doe",
            "music": None,
            "band": None
        }
        TestSongWriter.updateAttributes(src_tixi, "/song", attrs)

        writer.write_song_header("My Lovely Song")

        self.assertEqual("lyrics by: J. Doe, music by: ?",
                         writer.tixi.getTextElement("/html/body/p"))
        writer.tixi.removeElement("/html/body")

        # ------------------
        attrs = {
            "lyrics": None,
            "music": None,
            "band": None
        }
        TestSongWriter.updateAttributes(src_tixi, "/song", attrs)

        writer.write_song_header("My Lovely Song")

        self.assertEqual("lyrics by: ?, music by: ?",
                         writer.tixi.getTextElement("/html/body/p"))
        writer.tixi.removeElement("/html/body")

    def test_format_song_part(self):
        src_tixi = Tixi()
        src_tixi.open("test_song.xml")
        writer = SongWriter(src_tixi, self.settings, "/song")
        writer.tixi.createElement("/html", "body")
        # "/html" is ok, because the function doesn't really check where the target is

        expectedTixi = Tixi()
        expectedTixi.open("expected_test_song.xhtml")
        expectedTixi.registerNamespace("http://www.w3.org/1999/xhtml", "x")
        # Need to trim it a little - don't want things we're not checking
        expectedTixi.removeElement("/x:html/x:body/x:h1")
        expectedTixi.removeElement("/x:html/x:body/x:p[1]")
        expectedTixi.removeAttribute("/x:html/x:body/x:p[1]", "class")
        expectedTixi.removeAttribute("/x:html/x:body/x:p[2]", "class")
        expectedTixi.removeAttribute("/x:html/x:body/x:p[3]", "class")

        writer.format_song_part("/song/verse[1]", "/html/body")
        writer.format_song_part("/song/verse[2]", "/html/body")
        writer.format_song_part("/song/chorus", "/html/body", mode=ChordMode.CHORDS_BESIDE)

        self.assertEqual(expectedTixi.exportDocumentAsString(),
                         writer.tixi.exportDocumentAsString())

    def test_write_chords_above(self):
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

        self.assertIn("Now a verse without any chords", expectedTixi.getTextElement("/x:html/x:body/x:p[2]/x:span[1]"))
        expectedTixi.removeElement("/x:html/x:body/x:p[2]")
        # Now removing the last <p/> without checking!
        expectedTixi.removeElement("/x:html/x:body/x:p[2]")
        self.assertEqual(1, expectedTixi.getNamedChildrenCount("/x:html/x:body", "x:p"))
        # The class="chorus" attribute is assigned by another function. So, remove it from the expected
        expectedTixi.removeAttribute("/x:html/x:body/x:p", "class")

        # If we're still here, the expectedTixi has been properly formed.
        self.assertEqual(expectedTixi.exportDocumentAsString(),
                         writer.tixi.exportDocumentAsString())

    def test_write_chors_beside(self):
        src_tixi = Tixi()
        src_tixi.open("test_song.xml")
        writer = SongWriter(src_tixi, self.settings, "/song")
        writer.tixi.createElement("/html", "body")
        # "/html" is ok, because the function doesn't really check where the target is
        writer.write_chords_beside("/song/chorus", "/html/body")

        expectedTixi = Tixi()
        expectedTixi.open("expected_test_song.xhtml")
        expectedTixi.registerNamespace("http://www.w3.org/1999/xhtml", "x")
        # Need to trim it a little - don't want things we're not checking
        expectedTixi.removeElement("/x:html/x:body/x:h1")
        self.assertTrue(expectedTixi.checkAttribute("/x:html/x:body/x:p[1]", "class"))
        self.assertEqual("authors", expectedTixi.getTextAttribute("/x:html/x:body/x:p[1]", "class"))
        expectedTixi.removeElement("/x:html/x:body/x:p[1]")

        for path in reversed(expectedTixi.getPathsFromXPathExpression('//*[@class="verse"]')):
            expectedTixi.removeElement(path)

        self.assertEqual(1, expectedTixi.getNamedChildrenCount("/x:html/x:body", "x:p"))

        # The class="chorus" attribute is assigned by another function. So, remove it from the expected
        expectedTixi.removeAttribute("/x:html/x:body/x:p", "class")

        # If we're still here, the expectedTixi has been properly formed.
        self.assertEqual(expectedTixi.exportDocumentAsString(),
                         writer.tixi.exportDocumentAsString())

    def test_write_without_chords(self):
        src_tixi = Tixi()
        src_tixi.open("test_song.xml")
        writer = SongWriter(src_tixi, self.settings, "/song")
        writer.tixi.createElement("/html", "body")
        # "/html" is ok, because the function doesn't really check where the target is
        writer.write_without_chords("/song/verse[2]", "/html/body")

        expectedTixi = Tixi()
        expectedTixi.open("expected_test_song.xhtml")
        expectedTixi.registerNamespace("http://www.w3.org/1999/xhtml", "x")
        # Need to trim it a little - don't want things we're not checking
        expectedTixi.removeElement("/x:html/x:body/x:h1")
        self.assertTrue(expectedTixi.checkAttribute("/x:html/x:body/x:p[1]", "class"))
        self.assertEqual("authors", expectedTixi.getTextAttribute("/x:html/x:body/x:p[1]", "class"))

        # After the following removals, only the, what used to be p[3] should remain
        expectedTixi.removeElement("/x:html/x:body/x:p[1]")  # authors
        expectedTixi.removeElement("/x:html/x:body/x:p[1]")  # verse 1
        expectedTixi.removeElement("/x:html/x:body/x:p[2]")  # chorus
        self.assertEqual(1, expectedTixi.getNamedChildrenCount("/x:html/x:body", "x:p"))

        # The class="chorus" attribute is assigned by another function. So, remove it from the expected
        expectedTixi.removeAttribute("/x:html/x:body/x:p", "class")

        # If we're still here, the expectedTixi has been properly formed.
        self.assertEqual(expectedTixi.exportDocumentAsString(),
                         writer.tixi.exportDocumentAsString())

    def test_identifyLinesWithChords(self):
        # Need to initialize the writer to access the self.CS; Tixi and target path to not matter
        src_tixi = Tixi()
        src_tixi.open("test_song.xml")
        writer = SongWriter(src_tixi, self.settings, "/song")

        text = "\n".join(["Line 1",
                          "Line 2",
                          "Line 3",
                          "Line 4"])
        expected = ["Line 1", "Line 2", "Line 3", "Line 4"]
        # Should basically get the text with <br/> tags in newlines
        self.assertEqual([expected], writer._identifyLinesWithChords(text))

        text = "\n".join(["Line 1" + self.settings.CS + "F E E D",
                          "Line 2" + self.settings.CS + "F E E D",
                          "Line 3",
                          "Line 4"])
        expected = [
            LineWithChords("Line 1", ["F E E D"]),
            LineWithChords("Line 2", ["F E E D"]),
            ["Line 3", "Line 4"]
        ]
        self.assertEqual(expected, writer._identifyLinesWithChords(text))

    @staticmethod
    def updateAttributes(tixi: Tixi, path: str, attrs: dict) -> None:
        """Helper function to quickly update the attributes in path
            the attrs holds attribute name and value. If value is None, the attribute is removed
        """
        for attr, value in attrs.items():
            if value is None:
                if tixi.checkAttribute(path, attr):
                    tixi.removeAttribute(path, attr)
            else:
                tixi.addTextAttribute(path, attr, str(value))


if __name__ == '__main__':
    unittest.main()
