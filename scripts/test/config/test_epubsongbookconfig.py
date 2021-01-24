# -*- coding: utf-8 -*-
"""
Created on 23.01.2021 20:00
 
@author: piotr
"""

import getpass
import os
import shutil
import unittest

from tixi import Tixi
from config import ChordMode, EpubSongbookConfig, epubsongbookconfig


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
        self.test_dir_abs = os.path.join(os.path.abspath(os.path.dirname(__file__)), "test_dir")
        self.test_dir_rel = os.path.abspath(os.path.join(os.path.dirname(self.text_xml), "..", "test_dir"))
        self.tixi.open(self.text_xml, recursive=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir_abs, ignore_errors=True)
        shutil.rmtree(self.test_dir_rel, ignore_errors=True)

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
        self.assertEqual(os.path.abspath(os.path.join(epubsongbookconfig.__file__, "..", "..", "template")),
                         cfg.template_dir)
        self.assertEqual(">", cfg.CS)
        self.assertEqual("|", cfg.CI)

    def test_getSettings(self):
        # Change one entry to test max_songs
        self.tixi.addTextElement("/songbook/settings", "max_songs", "blah")

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
        self.assertEqual(os.path.abspath(os.path.join(epubsongbookconfig.__file__, "..", "..", "template")),
                         cfg.template_dir)
        self.assertEqual(">", cfg.CS)
        self.assertEqual("|", cfg.CI)

        self.tixi.updateTextElement("/songbook/settings/max_songs", "14")
        cfg._getSettings()
        self.assertEqual(14, cfg.maxsongs)

    def test_createOutputDir(self):
        cfg = EpubSongbookConfig(self.tixi)

        self.assertFalse(os.path.isdir(self.test_dir_rel))
        cfg.defineOutputDir()
        self.assertEqual(os.path.abspath(self.test_dir_rel),
                         os.path.abspath(cfg.dir_out))
        self.assertFalse(os.path.isdir(self.test_dir_rel))

        self.assertFalse(os.path.isdir(self.test_dir_abs))
        cfg.dir_out = self.test_dir_abs
        cfg.defineOutputDir()
        self.assertFalse(os.path.isdir(self.test_dir_abs))

    def test_placeEssentialFiles(self):
        cfg = EpubSongbookConfig(self.tixi)
        cfg.dir_out = self.test_dir_abs
        cfg.dir_text = os.path.join(cfg.dir_out, "text")
        self.assertFalse(os.path.isdir(self.test_dir_rel))
        cfg.placeEssentialFiles()
        self.assertTrue(os.path.isdir(self.test_dir_abs))
        path = os.path.abspath(os.path.join(self.test_dir_abs, "mimetype"))
        self.assertTrue(os.path.isfile(path))
        with open(path) as f:
            mimefile = f.read()
        self.assertEqual("application/epub+zip", mimefile)

        path = os.path.abspath(os.path.join(self.test_dir_abs, "metadata.opf"))
        self.assertTrue(os.path.isfile(path))

        tixi_actual = Tixi()
        tixi_actual.open(path)

        expected_meta = """<?xml version="1.0" encoding="utf-8"?>
            <package xmlns="http://www.idpf.org/2007/opf">
            <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
            <dc:title>My Songbook</dc:title>
            <dc:creator opf:file-as="Unknown" opf:role="aut">${user}</dc:creator>
            <dc:language>en</dc:language>
            </metadata>
            <guide/>
            </package>""".replace("${user}", getpass.getuser())
        tixi_expected = Tixi()
        tixi_expected.openString(expected_meta)

        self.assertEqual(tixi_expected.exportDocumentAsString(),
                         tixi_actual.exportDocumentAsString())

    def test_setupAttributes(self):
        attributes = {
            "/section[1]": ChordMode.CHORDS_BESIDE,
            "/section[1]/section[1]": ChordMode.CHORDS_BESIDE,
            "/section[1]/section[1]/song[1]": None,
            "/section[1]/section[1]/song[2]": ChordMode.CHORDS_ABOVE,
            "/section[1]/section[1]/song[3]": None,
            "/section[1]/section[2]": None,
            "/section[1]/section[2]/song[1]": None,
            "/section[1]/section[2]/song[2]": None,
            "/section[2]": None,
            "/section[2]/song[1]": None,
            "/section[2]/song[2]": None,
            "/section[2]/song[3]": None,
            "/section[2]/song[4]": ChordMode.NO_CHORDS,
            "/section[3]": None,
            "/section[3]/song[1]": None,
            "/section[3]/song[2]": None
        }
        cfg = EpubSongbookConfig(self.tixi)

        self.assertEqual(ChordMode.CHORDS_BESIDE, cfg.chordType)
        # Check before
        for p, chmode in attributes.items():
            path = "/songbook" + p
            self.assertTrue(cfg.tixi.checkElement(path), path)
            self.assertEqual(bool(chmode), cfg.tixi.checkAttribute(path, "chord_mode"))
            if chmode:
                self.assertEqual(str(chmode), cfg.tixi.getTextAttribute(path, "chord_mode"))

        cfg.setupAttributes()

        # Check after
        attributes["/section[2]"] = ChordMode.CHORDS_BESIDE
        attributes["/section[3]"] = ChordMode.CHORDS_BESIDE

        # Note that the cfg didn't have _getSettings called before, so it used the default CHORDS_BESIDE, and not the
        # value from the test xml file.
        for p, chmode in attributes.items():
            path = "/songbook" + p
            self.assertTrue(cfg.tixi.checkElement(path), path)
            self.assertEqual(bool(chmode), cfg.tixi.checkAttribute(path, "chord_mode"), path)
            if chmode:
                self.assertEqual(str(chmode), cfg.tixi.getTextAttribute(path, "chord_mode"), path)

if __name__ == '__main__':
    unittest.main()
