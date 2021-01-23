# -*- coding: utf-8 -*-
"""
Created on 23.01.2021 20:00
 
@author: piotr
"""

import getpass
import os
import unittest

from tixi import Tixi
from ...config import ChordMode, EpubSongbookConfig, epubsongbookconfig


class TestChordMode(unittest.TestCase):

    def test_get(self):
        self.assertEqual(ChordMode.CHORDS_ABOVE, ChordMode.get("CHORDS_ABOVE"))
        self.assertEqual(ChordMode.CHORDS_BESIDE, ChordMode.get("CHORDS_BESIDE"))
        self.assertEqual(ChordMode.NO_CHORDS, ChordMode.get("NO_CHORDS"))

    def test_str(self):
        self.assertEqual("CHORDS_ABOVE", str(ChordMode.CHORDS_ABOVE))
        self.assertEqual("CHORDS_BESIDE", str(ChordMode.CHORDS_BESIDE))
        self.assertEqual("NO_CHORDS", str(ChordMode.NO_CHORDS))


class TestEpubSongbookConfig(unittest.TestCase):
    def setUp(self):
        self.text_xml = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "tools", "resources",
                                     "test_song_src.xml")

        self.assertTrue(os.path.isfile(self.text_xml))
        self.tixi = Tixi()
        self.tixi.open(self.text_xml, recursive=True)

    def test_defaults(self):
        # Clear all settings
        self.tixi.removeElement("/songbook/settings")
        self.tixi.createElementAtIndex("/songbook", "settings", 1)
        cfg = EpubSongbookConfig(self.tixi)

        self.assertEqual("My Songbook", cfg.title)
        self.assertEqual("Alphabetical index of songs", cfg.alphabedical_index_title)
        self.assertEqual("Index of authors", cfg.authors_index_title)
        self.assertEqual("Section", cfg.default_section_title)
        self.assertEqual("See also:", cfg.links_header)
        self.assertEqual("lyrics by:", cfg.lyrics_string)
        self.assertEqual("music by:", cfg.music_string)
        self.assertEqual("?", cfg.unknown_author)
        self.assertEqual(getpass.getuser(), cfg.user)
        self.assertEqual("en", cfg.lang)
        self.assertEqual(0, cfg.maxsongs)
        self.assertEqual(ChordMode.CHORDS_BESIDE, cfg.chordType)
        self.assertEqual("output", cfg.dir_out)
        self.assertEqual(None, cfg.dir_text)
        self.assertEqual(os.path.abspath(os.path.join(epubsongbookconfig.__file__, "..","..", "template")),
                         cfg.template_dir)
        self.assertEqual(">", cfg.CS)
        self.assertEqual("|", cfg.CI)

    def test_getSettings(self):
        # Change one entry to test max_songs
        self.tixi.addTextElement("/songbook/settings","max_songs", "blah")

        cfg = EpubSongbookConfig(self.tixi)
        self.assertEqual("My Songbook", cfg.title)
        self.assertEqual("Alphabetical index of songs", cfg.alphabedical_index_title)
        self.assertEqual("Index of authors", cfg.authors_index_title)
        self.assertEqual("Section", cfg.default_section_title)
        self.assertEqual("See also:", cfg.links_header)
        self.assertEqual("lyrics by:", cfg.lyrics_string)
        self.assertEqual("music by:", cfg.music_string)
        self.assertEqual("?", cfg.unknown_author)
        self.assertEqual(getpass.getuser(), cfg.user)
        self.assertEqual("en", cfg.lang)
        self.assertEqual(0, cfg.maxsongs)
        self.assertEqual(ChordMode.CHORDS_BESIDE, cfg.chordType)
        self.assertEqual("../test_dir", cfg.dir_out)
        self.assertEqual(None, cfg.dir_text)
        self.assertEqual(os.path.abspath(os.path.join(epubsongbookconfig.__file__, "..","..", "template")),
                         cfg.template_dir)
        self.assertEqual(">", cfg.CS)
        self.assertEqual("|", cfg.CI)

        self.tixi.updateTextElement("/songbook/settings/max_songs", "14")
        cfg._getSettings()
        self.assertEqual(14, cfg.maxsongs)

if __name__ == '__main__':
    unittest.main()
