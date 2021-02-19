# -*- coding: utf-8 -*-
"""
Created on 16.11.2020 22:14
 
@author: Piotr Gradkowski <grotsztaksel@o2.pl>
"""

__authors__ = ['Piotr Gradkowski <grotsztaksel@o2.pl>']
__date__ = '2020-11-16'


import unittest
import os

from scripts.config import EpubSongbookConfig, ChordMode
from scripts.tixi import Tixi, TixiException, ReturnCode
from scripts.tools.song_writer import SongWriter, LineWithChords


class TestSongWriter(unittest.TestCase):
    def setUp(self):
        # Need a Tixi object to initialize the EpubSongbookConfig
        self.src_file = os.path.join(os.path.dirname(__file__), "resources", "test_song.xml")
        self.src_all_songs = os.path.join(os.path.dirname(__file__), "resources", "test_song_src.xml")
        self.src_tixi = Tixi()
        self.src_tixi.open(self.src_file)

        cfgTixi = Tixi()
        cfgTixi.create("songbook")

        self.settings = EpubSongbookConfig(cfgTixi)
        self.settings.dir_text = os.path.dirname(__file__)
        self.settings.CS = ">"
        self.settings.CI = "|"
        self.testFile = os.path.join(os.path.dirname(__file__), "test_output_song.xhtml")

        self.expectedTixi = Tixi()
        self.expected_output = os.path.join(os.path.dirname(__file__), "resources", "expected_test_song.xhtml")
        self.expectedTixi.open(self.expected_output)
        self.expectedTixi.registerNamespace("http://www.w3.org/1999/xhtml", "x")

        self.writer = SongWriter(self.src_tixi, self.settings, "/song")

    def tearDown(self):
        if os.path.isfile(os.path.join(self.settings.dir_text, self.testFile)):
            os.remove(self.testFile)

    def test_write_song_file(self):
        self.writer.settings.encoding = None  # Otherwise the HtmlWriter.saveFile() will append an " encoding='utf-8'"
        self.writer.write_song_file(self.testFile)

        self.assertTrue(os.path.isfile(self.testFile))

        actualTixi = Tixi()
        actualTixi.open(self.testFile)

        self.assertEqual(self.expectedTixi.exportDocumentAsString(),
                         actualTixi.exportDocumentAsString())

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

    def test_write_song_part(self):
        self.writer.tixi.createElement("/html", "body")
        # "/html" is ok, because the function doesn't really check where the target is

        # Need to trim it a little - don't want things we're not checking
        self.expectedTixi.removeElement("/x:html/x:body/x:h1")
        self.expectedTixi.removeElement("/x:html/x:body/x:p[1]")

        self.writer.write_song_part("/song/verse[1]")
        self.writer.write_song_part("/song/verse[2]")
        self.writer.write_song_part("/song/chorus")

        self.assertEqual(self.expectedTixi.exportDocumentAsString(),
                         self.writer.tixi.exportDocumentAsString().replace("&amp;", "&"))

    def test_format_song_part(self):
        writer = SongWriter(self.src_tixi, self.settings, "/song")
        writer.tixi.createElement("/html", "body")
        # "/html" is ok, because the function doesn't really check where the target is

        # Need to trim it a little - don't want things we're not checking
        self.expectedTixi.removeElement("/x:html/x:body/x:h1")
        self.expectedTixi.removeElement("/x:html/x:body/x:p[1]")
        self.expectedTixi.removeAttribute("/x:html/x:body/x:p[1]", "class")
        self.expectedTixi.removeAttribute("/x:html/x:body/x:p[2]", "class")
        self.expectedTixi.removeAttribute("/x:html/x:body/x:p[3]", "class")

        writer.format_song_part("/song/verse[1]", "/html/body")
        writer.format_song_part("/song/verse[2]", "/html/body")
        writer.format_song_part("/song/chorus", "/html/body", mode=ChordMode.CHORDS_BESIDE)

        self.assertEqual(self.expectedTixi.exportDocumentAsString(),
                         writer.tixi.exportDocumentAsString().replace("&amp;", "&"))

    def test_write_chords_above(self):
        self.writer.tixi.createElement("/html", "body")
        # "/html" is ok, because the function doesn't really check where the target is
        self.writer.write_chords_above("/song/verse[1]", "/html/body")

        # Need to trim it a little - don't want things we're not checking
        self.expectedTixi.removeElement("/x:html/x:body/x:h1")
        self.assertTrue(self.expectedTixi.checkAttribute("/x:html/x:body/x:p[1]", "class"))
        self.assertEqual("authors", self.expectedTixi.getTextAttribute("/x:html/x:body/x:p[1]", "class"))
        self.expectedTixi.removeElement("/x:html/x:body/x:p[1]")

        self.assertIn("Now a verse without any chords",
                      self.expectedTixi.getTextElement("/x:html/x:body/x:p[2]/x:span[1]"))
        self.expectedTixi.removeElement("/x:html/x:body/x:p[2]")
        # Now removing the last <p/> without checking!
        self.expectedTixi.removeElement("/x:html/x:body/x:p[2]")
        self.assertEqual(1, self.expectedTixi.getNamedChildrenCount("/x:html/x:body", "x:p"))
        # The class="chorus" attribute is assigned by another function. So, remove it from the expected
        self.expectedTixi.removeAttribute("/x:html/x:body/x:p", "class")

        # If we're still here, the expectedTixi has been properly formed.
        self.assertEqual(self.expectedTixi.exportDocumentAsString(),
                         self.writer.tixi.exportDocumentAsString().replace("&amp;", "&"))

    def test_write_chors_beside(self):
        self.writer.tixi.createElement("/html", "body")
        # "/html" is ok, because the function doesn't really check where the target is
        self.writer.write_chords_beside("/song/chorus", "/html/body")

        # Need to trim it a little - don't want things we're not checking
        self.expectedTixi.removeElement("/x:html/x:body/x:h1")
        self.assertTrue(self.expectedTixi.checkAttribute("/x:html/x:body/x:p[1]", "class"))
        self.assertEqual("authors", self.expectedTixi.getTextAttribute("/x:html/x:body/x:p[1]", "class"))
        self.expectedTixi.removeElement("/x:html/x:body/x:p[1]")

        for path in reversed(self.expectedTixi.xPathExpressionGetAllXPaths('//*[@class="verse"]')):
            self.expectedTixi.removeElement(path)

        self.assertEqual(1, self.expectedTixi.getNamedChildrenCount("/x:html/x:body", "x:p"))

        # The class="chorus" attribute is assigned by another function. So, remove it from the expected
        self.expectedTixi.removeAttribute("/x:html/x:body/x:p", "class")

        # If we're still here, the expectedTixi has been properly formed.
        self.assertEqual(self.expectedTixi.exportDocumentAsString(),
                         self.writer.tixi.exportDocumentAsString())

    def test_write_without_chords(self):
        self.writer.tixi.createElement("/html", "body")
        # "/html" is ok, because the function doesn't really check where the target is
        self.writer.write_without_chords("/song/verse[2]", "/html/body")

        # Need to trim it a little - don't want things we're not checking
        self.expectedTixi.removeElement("/x:html/x:body/x:h1")
        self.assertTrue(self.expectedTixi.checkAttribute("/x:html/x:body/x:p[1]", "class"))
        self.assertEqual("authors", self.expectedTixi.getTextAttribute("/x:html/x:body/x:p[1]", "class"))

        # After the following removals, only the, what used to be p[3] should remain
        self.expectedTixi.removeElement("/x:html/x:body/x:p[1]")  # authors
        self.expectedTixi.removeElement("/x:html/x:body/x:p[1]")  # verse 1
        self.expectedTixi.removeElement("/x:html/x:body/x:p[2]")  # chorus
        self.assertEqual(1, self.expectedTixi.getNamedChildrenCount("/x:html/x:body", "x:p"))

        # The class="chorus" attribute is assigned by another function. So, remove it from the expected
        self.expectedTixi.removeAttribute("/x:html/x:body/x:p", "class")

        # If we're still here, the expectedTixi has been properly formed.
        self.assertEqual(self.expectedTixi.exportDocumentAsString(),
                         self.writer.tixi.exportDocumentAsString())

    def test_write_links(self):
        expected_html = """
        <?xml version="1.0"?>
        <html xmlns="http://www.w3.org/1999/xhtml">
        <head>
        <title>My Songbook</title>
        <link rel="stylesheet" type="text/css" href="../songbook.css"/>
        </head>
        <body>
        <h3>See also:</h3>
        <p class="links">
            <ul>
                <li><a href="song_file_3.xhtml">Song A</a><span style="font-size:12px">(John Doe)</span></li>
                <li><a href="song_file_6.xhtml">Song A</a><span style="font-size:12px">(Mike Moo)</span></li>
                <li><a href="song_file_9.xhtml">Song ABBA</a><span style="font-size:12px">(John Doe)</span></li>
            </ul>
        </p>
        </body>
        </html>
        """

        src_tixi = Tixi()
        src_tixi.open(self.src_all_songs, recursive=True)
        songPath = "/songbook/section[1]/section[1]/song[2]"
        writer = SongWriter(src_tixi, self.settings, songPath)
        writer.tixi.createElement(writer.root, "body")
        empty_html = writer.tixi.exportDocumentAsString()

        # There are no links defined in the song. Should do nothing
        writer.write_links()
        self.assertEqual(empty_html, writer.tixi.exportDocumentAsString())

        # Add links in the investigated song
        lPath = src_tixi.createElementAtIndex(songPath, "link", 1)
        src_tixi.addTextAttribute(lPath, "title", "Song A")
        lPath = src_tixi.createElementAtIndex(songPath, "link", 2)
        src_tixi.addTextAttribute(lPath, "title", "Song ABBA")

        # Need to add fake xhtml attributes, otherwise the AuthorsWriter will bomb out
        i = 0
        for path in src_tixi.xPathExpressionGetAllXPaths("//song"):
            i += 1
            src_tixi.addTextAttribute(path, "xhtml", "song_file_{}.xhtml".format(i))

        expectedTixi = Tixi()
        self.expectedTixi.openString(expected_html.strip())
        writer.write_links()
        self.assertEqual(self.expectedTixi.exportDocumentAsString(),
                         writer.tixi.exportDocumentAsString())

    def test_identifyLinesWithChords(self):
        # Need to initialize the writer to access the self.CS; Tixi and target path to not matter
        text = "\n".join(["Line 1",
                          "Line 2",
                          "Line 3",
                          "Line 4"])
        expected = ["Line 1", "Line 2", "Line 3", "Line 4"]
        # Should basically get the text with <br/> tags in newlines
        self.assertEqual([expected], self.writer._identifyLinesWithChords(text))

        text = "\n".join(["Line 1" + self.settings.CS + "F E E D",
                          "Line 2" + self.settings.CS + "F E E D",
                          "Line 3",
                          "Line 4"])
        expected = [
            LineWithChords("Line 1", ["F E E D"]),
            LineWithChords("Line 2", ["F E E D"]),
            ["Line 3", "Line 4"]
        ]
        self.assertEqual(expected, self.writer._identifyLinesWithChords(text))

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
