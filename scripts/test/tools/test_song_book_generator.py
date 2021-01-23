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
        self.test_song_src = os.path.join(os.path.abspath(os.path.dirname(__file__)), "resources", "test_song_src.xml")
        self.test_src2 = self.test_song_src + "2"
        self.test_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "test_dir")
        self.sg = SongBookGenerator(self.test_song_src)
        # Overwrite the output directory
        self.sg.settings.dir_out = self.test_dir


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

        opf_expected = os.path.join(self.test_dir, "expected_opf.opf")


        self.assertFalse(os.path.isfile(opf_expected))


        self.sg.write_metadata()
        self.assertTrue(os.path.isfile(opf_expected))

        tixi_expected = Tixi()
        tixi_expected.open(opf_expected)
        tixi_result = Tixi()
        tixi_result.open(opf_target)

        self.assertEqual(tixi_expected.exportDocumentAsString(),
                         tixi_result.exportDocumentAsString())
        os.remove(opf_target)

    def test_write_toc(self):
        # First copy the toc.ncx to the test dir and use it.
        toc_original = os.path.join(CFG.OUTPUT_DIR, "toc.ncx")
        toc_expected = os.path.join(os.path.dirname(__file__), "expected_toc.ncx")
        test_dir = os.path.dirname(CFG.SONG_SRC_XML)
        CFG.OUTPUT_DIR = test_dir
        self.assertTrue(os.path.isfile(toc_original))
        self.assertTrue(os.path.isfile(toc_expected))
        self.assertTrue(os.path.isdir(test_dir))
        toc_target = os.path.join(test_dir, "toc.ncx")
        shutil.copyfile(toc_original, toc_target)
        self.sg.write_toc()

        tixi_expected = Tixi()
        tixi_expected.open(toc_expected)
        tixi_result = Tixi()
        tixi_result.open(toc_target)

        self.assertEqual(tixi_expected.exportDocumentAsString(),
                         tixi_result.exportDocumentAsString())

        os.remove(toc_target)


if __name__ == '__main__':
    unittest.main()
