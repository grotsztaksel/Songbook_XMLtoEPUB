# -*- coding: utf-8 -*-
"""
Created on 21.11.2020 17:10
 
@author: piotr
"""

import os
import shutil
import unittest
from collections import namedtuple

from config import EpubSongbookConfig
from tixi import Tixi
from tools.song_book_generator import SongBookGenerator

Song = namedtuple("Song", ["file", "title", "xml"])


class TestSongBookGenerator(unittest.TestCase):
    def setUp(self):
        self.references = os.path.join(os.path.abspath(os.path.dirname(__file__)), "resources")
        self.test_song_src = os.path.join(self.references, "test_song_src.xml")
        self.test_src2 = self.test_song_src + "2"
        self.test_dir = os.path.abspath(os.path.join(os.path.dirname(self.test_song_src), "..", "test_dir"))
        shutil.rmtree(self.test_dir, ignore_errors=True)
        self.sg = SongBookGenerator(self.test_song_src)
        # Overwrite the output directory
        self.sg.settings.dir_out = self.test_dir

        # The constructor should have created the dir
        self.assertTrue(os.path.isdir(self.test_dir))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        if os.path.isfile(self.test_src2):
            os.remove(self.test_src2)

    def test_init(self):
        tixi = self.sg.tixi

        # One section should be completely ignored
        self.assertEqual(2, tixi.getNamedChildrenCount("/songbook", "section"))

        self.assertEqual(6, self.sg.N)  # The total number of songs that are kept in the tixi

        xPath = "//*[self::verse or self::chorus]"

        n = tixi.tryXPathEvaluateNodeNumber(xPath)
        self.assertEqual(18, n)  # The total number of verses and choruses in the songs

    def test_getBasicSongInfo(self):
        # The getBasicSongInfo has already been called in __init__
        expected = [Song("sng_my_test_song.xhtml", "My Test Song", "/songbook/section[1]/section[1]/song[1]"),
                    Song("sng_song_a.xhtml", "Song A", "/songbook/section[1]/section[1]/song[2]"),
                    Song("sng_song_b.xhtml", "Song B", "/songbook/section[1]/section[2]/song[1]"),
                    Song("sng_song_c.xhtml", "Song C", "/songbook/section[1]/section[2]/song[2]"),
                    Song("sng_song_a_1.xhtml", "Song A", "/songbook/section[2]/song[1]"),
                    Song("sng_song_abba.xhtml", "Song ABBA", "/songbook/section[2]/song[2]")]

        for item in expected:
            self.assertEqual(item.title, self.sg.tixi.getTextAttribute(item.xml, "title"))
            self.assertEqual(item.file, self.sg.tixi.getTextAttribute(item.xml, "xhtml"))

        # Now make some empty sections (by adding new and removing songs from exisiting). Rerun the function
        # and see if these sections are removed.
        # Use a modified input file
        preparing_tixi = Tixi()
        preparing_tixi.open(self.test_song_src, recursive=True)
        preparing_tixi.removeElement("/songbook/section/section[1]/song[2]")
        preparing_tixi.addTextElement("/songbook/settings", "max_songs", "3")
        preparing_tixi.saveCompleteDocument(self.test_src2)

        self.sg = SongBookGenerator(self.test_src2)
        expected = [Song("sng_song_a.xhtml", "Song A", "/songbook/section/section[1]/song"),
                    Song("sng_song_b.xhtml", "Song B", "/songbook/section/section[2]/song[1]"),
                    Song("sng_song_c.xhtml", "Song C", "/songbook/section/section[2]/song[2]")]

        for item in expected:
            self.assertEqual(item.title, self.sg.tixi.getTextAttribute(item.xml, "title"))
            self.assertEqual(item.file, self.sg.tixi.getTextAttribute(item.xml, "xhtml"))

        self.assertFalse(self.sg.tixi.checkElement("/songbook/section[2]"))

        # Add some cascade of sections that should eventually be removed - check if tixi removes them
        # in the right order without bombing out

        self.sg.tixi.createElement("/songbook", "section")
        self.sg.tixi.createElement("/songbook", "section")
        self.sg.tixi.createElement("/songbook/section[3]", "section")
        self.sg.tixi.createElement("/songbook/section[2]", "section")
        self.sg.tixi.createElement("/songbook/section[2]/section", "section")
        self.sg.tixi.createElement("/songbook/section[2]/section", "section")
        self.sg.tixi.createElement("/songbook/section[2]/section[1]/section[2]", "section")

        self.sg.getBasicSongInfo()
        self.assertFalse(self.sg.tixi.checkElement("/songbook/section[2]"))
        for item in expected:
            self.assertEqual(item.title, self.sg.tixi.getTextAttribute(item.xml, "title"))
            self.assertEqual(item.file, self.sg.tixi.getTextAttribute(item.xml, "xhtml"))

    def test_write_indexes(self):
        self.assertEqual(self.test_dir, self.sg.settings.dir_out)
        expected_files = ["idx_authors.xhtml", "idx_songs.xhtml"]
        for file in expected_files:
            self.assertFalse(os.path.isfile(os.path.join(self.test_dir, file)))

        self.sg.write_indexes()

        for file in expected_files:
            self.assertTrue(os.path.isfile(os.path.join(self.test_dir, file)))

    def test_write_songs(self):
        self.assertEqual(os.path.join(self.test_dir, "text"), self.sg.settings.dir_text)
        expected_files = ["sec_section_1.xhtml",
                          "sec_section_1.1.xhtml",
                          "sng_my_test_song.xhtml",
                          "sng_song_a.xhtml",
                          "sec_section_1.2.xhtml",
                          "sng_song_b.xhtml",
                          "sng_song_c.xhtml",
                          "sec_section_2.xhtml",
                          "sng_song_a_1.xhtml",
                          "sng_song_abba.xhtml"]
        for file in expected_files:
            self.assertFalse(os.path.isfile(os.path.join(self.test_dir, "text", file)))

        self.sg.write_songs()

        for file in expected_files:
            self.assertEqual(file[:3] == "sng", os.path.isfile(os.path.join(self.test_dir, "text", file)))

    def test_write_sections(self):
        self.assertEqual(os.path.join(self.test_dir, "text"), self.sg.settings.dir_text)
        expected_files = ["sec_section_1.xhtml",
                          "sec_section_1.1.xhtml",
                          "sng_my_test_song.xhtml",
                          "sng_song_a.xhtml",
                          "sec_section_1.2.xhtml",
                          "sng_song_b.xhtml",
                          "sng_song_c.xhtml",
                          "sec_section_2.xhtml",
                          "sng_song_a_1.xhtml",
                          "sng_song_abba.xhtml"]
        for file in expected_files:
            self.assertFalse(os.path.isfile(os.path.join(self.test_dir, "text", file)))

        self.sg.write_sections()

        for file in expected_files:
            self.assertEqual(file[:3] == "sec", os.path.isfile(os.path.join(self.test_dir, "text", file)))

    def test_createTwoWayLinks(self):
        links_start = {"/songbook/section[1]/section[1]/song[2]/link": "Song B",
                       "/songbook/section[1]/section[2]/song[1]/link": None,
                       "/songbook/section[1]/section[2]/song[2]/link": "No Such Title",
                       "/songbook/section[2]/song[1]/link": None,
                       "/songbook/section[2]/song[2]/link": "Song A"}

        links_end = {"/songbook/section[1]/section[1]/song[2]/link[1]": "Song B",
                     "/songbook/section[1]/section[1]/song[2]/link[2]": "Song ABBA",
                     "/songbook/section[1]/section[2]/song[1]/link": "Song A",
                     "/songbook/section[1]/section[2]/song[2]/link": None,
                     "/songbook/section[2]/song[1]/link[1]": "Song ABBA",
                     "/songbook/section[2]/song[1]/link[2]": "Song B",
                     "/songbook/section[2]/song[2]/link": "Song A"}

        tixi = self.sg.tixi
        run = "start"
        for links_dict in [links_start, links_end]:
            for i, path in enumerate(links_dict.keys()):
                link_exists = bool(links_dict[path])
                self.assertEqual(link_exists, tixi.checkElement(path), "Run: {}, path {}: {}".format(run, i + 1, path))
                if link_exists:
                    title = links_dict[path]
                    try:
                        self.assertEqual(title, tixi.getTextAttribute(path, "title"))
                    except AssertionError as e:
                        uu = tixi.exportDocumentAsString()
                        pass
                        raise e
            self.sg.createTwoWayLinks()
            run = "end"

    def test_write_metadata(self):
        opf_expected = os.path.join(self.references, "expected_opf.opf")
        opf_created = os.path.join(self.test_dir, "metadata.opf")
        self.assertTrue(os.path.isfile(opf_expected))
        # Should have already copied the file from template by the initializer
        self.assertTrue(os.path.isfile(opf_created))

        self.sg.write_metadata()

        self.assertTrue(os.path.isfile(opf_expected))

        tixi_expected = Tixi()
        tixi_expected.open(opf_expected)
        tixi_result = Tixi()
        tixi_result.open(opf_created)

        # Clean comments from the tixi - some items may have been commented out
        for tixi in [tixi_expected, tixi_result]:
            tixi.clearComments()
        self.assertEqual(tixi_expected.exportDocumentAsString(),
                         tixi_result.exportDocumentAsString())
        os.remove(opf_created)

    def test_write_toc(self):
        # First copy the toc.ncx to the test dir and use it.
        toc_expected = os.path.join(self.references, "expected_toc.ncx")
        toc_created = os.path.join(self.test_dir, "toc.ncx")
        self.assertTrue(os.path.isfile(toc_expected))
        self.assertFalse(os.path.isfile(toc_created))

        self.sg.write_toc()
        self.assertTrue(os.path.isfile(toc_created))
        tixi_expected = Tixi()
        tixi_expected.open(toc_expected)
        tixi_result = Tixi()
        tixi_result.open(toc_created)

        self.assertEqual(tixi_expected.exportDocumentAsString(),
                         tixi_result.exportDocumentAsString())

        os.remove(toc_created)

    def test_createNavPoint(self):
        tixi_ncx = Tixi()
        tixi_ncx.create("root")

        self.sg.id = 365
        self.sg._createNavPoint("/songbook", "/root", tixi_ncx)

        expected = """
        <?xml version='1.0'?>
        <root>
        <navPoint id="num_365" playOrder="365"><navLabel><text>Section 1</text></navLabel><content src="text/sec_section_1.xhtml"/>
        <navPoint id="num_366" playOrder="366"><navLabel><text>Section 1.1</text></navLabel><content src="text/sec_section_1.1.xhtml"/>
        <navPoint id="num_367" playOrder="367"><navLabel><text>My Test Song</text></navLabel><content src="text/sng_my_test_song.xhtml"/></navPoint>
        <navPoint id="num_368" playOrder="368"><navLabel><text>Song A</text></navLabel><content src="text/sng_song_a.xhtml"/></navPoint>
        </navPoint>
        <navPoint id="num_369" playOrder="369"><navLabel><text>Section 1.2</text></navLabel><content src="text/sec_section_1.2.xhtml"/>
        <navPoint id="num_370" playOrder="370"><navLabel><text>Song B</text></navLabel><content src="text/sng_song_b.xhtml"/></navPoint>
        <navPoint id="num_371" playOrder="371"><navLabel><text>Song C</text></navLabel><content src="text/sng_song_c.xhtml"/></navPoint>
        </navPoint>
        </navPoint>
        <navPoint id="num_372" playOrder="372"><navLabel><text>Section 2</text></navLabel><content src="text/sec_section_2.xhtml"/>
        <navPoint id="num_373" playOrder="373"><navLabel><text>Song A</text></navLabel><content src="text/sng_song_a_1.xhtml"/></navPoint>
        <navPoint id="num_374" playOrder="374"><navLabel><text>Song ABBA</text></navLabel><content src="text/sng_song_abba.xhtml"/></navPoint>
        </navPoint>
        </root>""".strip()
        expected_tixi = Tixi()
        expected_tixi.openString(expected)

        self.assertEqual(expected_tixi.exportDocumentAsString(),
                         tixi_ncx.exportDocumentAsString())

    def test_createEmptyToc(self):
        expected = """
        <?xml version='1.0'?>
        <ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" xml:lang="en">
        <head/><docTitle><text>My Songbook</text></docTitle>
        </ncx>""".strip()

        etixi = Tixi()
        etixi.openString(expected)
        output = self.sg._createEmptyToC()

        self.assertEqual(etixi.exportDocumentAsString(),
                         output.exportDocumentAsString())


if __name__ == '__main__':
    unittest.main()