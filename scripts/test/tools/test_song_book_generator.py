# -*- coding: utf-8 -*-
"""
Created on 21.11.2020 17:10
 
@author: piotr
"""

from config import CFG
import os
import unittest
from tixi import Tixi, TixiException, ReturnCode, tryXPathEvaluateNodeNumber

from tools.song_book_generator import SongBookGenerator
from config import CFG
from tools.song_tuple import Song


class TestSongBookGenerator(unittest.TestCase):
    def setUp(self):
        tixi = Tixi()
        test_song_src = os.path.join(os.path.abspath(os.path.dirname(__file__)), "test_song_src.xml")
        CFG.SONG_SRC_XML = test_song_src

        self.sg = SongBookGenerator()

    def test_init(self):
        tixi = self.sg.tixi
        self.assertEqual(2, tixi.getNamedChildrenCount("/songbook", "section"))

        xPath = "//*[self::verse or self::chorus]"

        n = tryXPathEvaluateNodeNumber(tixi, xPath)
        self.assertEqual(15, n)
        for i in range(n):
            # There should be only "La La La" in the lyrics
            path = tixi.xPathExpressionGetXPath(xPath, i + 1)
            text = tixi.getTextElement(path).replace("La", "").strip()
            self.assertEqual("", text)

    def test_getBasicSongInfo(self):
        # The getBasicSongInfo has already been called in __init__
        expected = [Song("song_a.xhtml", "Song A", "/songbook/section[1]/section[1]/song"),
                    Song("song_b.xhtml", "Song B", "/songbook/section[1]/section[2]/song[1]"),
                    Song("song_c.xhtml", "Song C", "/songbook/section[1]/section[2]/song[2]"),
                    Song("song_a_1.xhtml", "Song A", "/songbook/section[2]/song[1]"),
                    Song("song_abba.xhtml", "Song ABBA", "/songbook/section[2]/song[2]")]

        self.assertEqual(expected, self.sg.songs)

    def test_createTwoWayLinks(self):
        links_start = {"/songbook/section[1]/section[1]/song[1]/link": "Song B",
                       "/songbook/section[1]/section[2]/song[1]/link": None,
                       "/songbook/section[1]/section[2]/song[2]/link": "No Such Title",
                       "/songbook/section[2]/song[1]/link": None,
                       "/songbook/section[2]/song[2]/link": "Song A"}

        links_end = {"/songbook/section[1]/section[1]/song[1]/link[1]": "Song B",
                     "/songbook/section[1]/section[1]/song[1]/link[2]": "Song ABBA",
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
                self.assertEqual(link_exists, tixi.checkElement(path), "Run: {}, path {}".format(run, i + 1))
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


if __name__ == '__main__':
    unittest.main()
