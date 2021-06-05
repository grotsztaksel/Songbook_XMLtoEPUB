# -*- coding: utf-8 -*-
"""
Created on 21.11.2020 17:10

@author: Piotr Gradkowski <grotsztaksel@o2.pl>
"""

__authors__ = ['Piotr Gradkowski <grotsztaksel@o2.pl>']
__date__ = '2020-11-21'

import os
import shutil
import unittest
from collections import namedtuple

from scripts.config import EpubSongbookConfig
from scripts.tixi import Tixi
from scripts.tools.song_book_generator import SongBookGenerator

Song = namedtuple("Song", ["file", "title", "xml"])


class TestSongBookGenerator(unittest.TestCase):
    def setUp(self):
        self.references = os.path.join(os.path.abspath(os.path.dirname(__file__)), "resources")
        self.test_song_src = os.path.join(self.references, "test_song_src.xml")
        self.test_src2 = self.test_song_src + "2"
        self.test_dir = os.path.abspath(os.path.join(os.path.dirname(self.test_song_src), "..", "test_dir"))
        shutil.rmtree(self.test_dir, ignore_errors=True)
        self.sg = SongBookGenerator(self.test_song_src, preprocess=False)
        # Overwrite the output directory
        self.sg.settings.dir_out = self.test_dir

        # The constructor should have created the dir
        self.assertTrue(os.path.isdir(self.test_dir))
        self.fhandle = None
        self.newDirs = []

        # Copy the test_song.xml to a backup file
        self.test_song = os.path.join(self.references, "test_song.xml")
        self.test_song_bak = os.path.join(self.references, "test_song.xml.bak")

        shutil.copy(self.test_song, self.test_song_bak)

    def tearDown(self):
        for path in self.newDirs:
            shutil.rmtree(path, ignore_errors=True)
        shutil.rmtree(self.test_dir, ignore_errors=True)

        if os.path.isfile(self.test_src2):
            os.remove(self.test_src2)
        if self.fhandle is not None:
            try:
                self.fhandle.close()
            except:
                pass

        # If the test file has been changed, bring back the old version
        shutil.copy(self.test_song_bak, self.test_song)
        os.remove(self.test_song_bak)

    def test_init(self):
        self.sg._preprocess()
        tixi = self.sg.tixi

        # One section should be completely ignored
        self.assertEqual(2, tixi.getNamedChildrenCount("/songbook", "section"))

        self.assertEqual(6, self.sg.N)  # The total number of songs that are kept in the tixi

        xPath = "//*[self::verse or self::chorus]"

        n = tixi.xPathEvaluateNodeNumber(xPath)
        self.assertEqual(15, n)  # The total number of verses and choruses in the songs

    def test_preprocess(self):
        self.sg._preprocess()
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

        self.sg._preprocess()
        self.assertFalse(self.sg.tixi.checkElement("/songbook/section[2]"))
        for item in expected:
            self.assertEqual(item.title, self.sg.tixi.getTextAttribute(item.xml, "title"))
            self.assertEqual(item.file, self.sg.tixi.getTextAttribute(item.xml, "xhtml"))

        # Reset the whole tixi
        tixi = Tixi()
        tixi.open(self.test_song_src)
        self.sg.tixi = tixi
        # Break it to get the error messages
        # 1. Content both in source file and in the <song> element itself
        song = "/songbook/section[1]/section[1]/song[2]"
        self.sg.tixi.addTextElement(song, "verse", "La la la\n I shouldn't be here!")
        self.sg.tixi.addTextElement(song, "chorus", "Oh Oh Oh\n I shouldn't be here!")
        self.sg.tixi.addTextElement(song, "verse", "La la la\n I shouldn't be here!")

        # 2. File exists, but not a valid XML
        dummyfile = os.path.abspath(os.path.join(self.test_dir, "dummy.xml"))
        with open(dummyfile, 'w') as f:
            f.write("This won't make a valid XML file")
            f.write("Tixi should fail trying to open it")
        self.assertTrue(os.path.isfile(dummyfile))
        self.sg.tixi.addTextAttribute("/songbook/section[1]/section[1]/song[1]", "src", dummyfile)
        # 3. File does not exist
        self.sg.tixi.addTextAttribute("/songbook/section[1]/section[1]/song[3]", "src", "./non_existent_file")

        # 4. Attributes that are different in the <song> element and in the source file
        self.sg.tixi.addTextAttribute(song, "title", "This title will not match")
        self.sg.tixi.addTextAttribute(song, "band", "Another band")

        try:
            self.sg._preprocess()
            self.assertFalse(True, "Did not raise error, although one was expected")
        except ValueError as e:
            expectedMessage = """The following songs have both content in master XML and source defined:
- "This title will not match" (/songbook/section/section[1]/song[1])
- "Song A" (/songbook/section/section[1]/song[2])
----------------------------------------

The following songs source files not found:
- ./non_existent_file ("Song A")
----------------------------------------

The following songs have their attributes defined in both master XML and in source file, and they are not the same:
- /songbook/section/section[1]/song[1], title: 'My Test Song' vs 'This title will not match'
- /songbook/section/section[1]/song[1], band: 'The Developers' vs 'Another band'
----------------------------------------
"""
            self.assertEqual(expectedMessage, str(e))

    def test_removeIgnoredContent(self):
        titles_to_exclude = {"Song to exclude 1": 1 + 1 + 2 + 1,  # 1 song, 1 link, 2 verse, 1 chorus
                             "Song to exclude 2": 1 + 1 + 2 + 1,
                             "Song to exclude 3": 1 + 1 + 2 + 1,
                             "You'll never see me": 1 + 1 + 1 + 0,
                             "You'll never see me again": 1 + 1 + 1 + 0}

        section_to_exclude = "/songbook/section[3]"
        self.assertTrue(self.sg.tixi.checkElement(section_to_exclude))

        for title in titles_to_exclude:
            xPath = "//song[@title=\"{}\"]".format(title)
            self.assertEqual(1, self.sg.tixi.xPathEvaluateNodeNumber(xPath))

        self.assertEqual(55, self.sg.tixi.xPathEvaluateNodeNumber("//*"))
        self.sg._removeIgnoredContent()

        self.assertFalse(self.sg.tixi.checkElement(section_to_exclude))

        for title in titles_to_exclude:
            xPath = "//song[@title=\"{}\"]".format(title)
            self.assertEqual([], self.sg.tixi.xPathExpressionGetAllXPaths(xPath))

        self.assertEqual(55 - (sum(titles_to_exclude.values()) + 1), self.sg.tixi.xPathEvaluateNodeNumber("//*"))

    def test_findAmbiguousSongsContent(self):

        self.assertEqual({}, self.sg._findAmbiguousSongsContent())

        # Now break the test data
        song = "/songbook/section[1]/section[1]/song[2]"
        self.sg.tixi.addTextElement(song, "verse", "La la la\n I shouldn't be here!")
        self.sg.tixi.addTextElement(song, "chorus", "Oh Oh Oh\n I shouldn't be here!")
        self.sg.tixi.addTextElement(song, "verse", "La la la\n I shouldn't be here!")
        self.assertEqual({song: "My Test Song"}, self.sg._findAmbiguousSongsContent())

    def test_pullAttributesFromSRCs(self):
        song = "/songbook/section[1]/section[1]/song[2]"
        attributes = {"title": "My Test Song",
                      "band": "The Developers",
                      "src": "./test_song.xml"}
        for attr, value in attributes.items():
            self.assertEqual(value, self.sg.tixi.getTextAttribute(song, attr), attr)
        self.assertEqual(len(attributes), self.sg.tixi.getNumberOfAttributes(song))

        self.assertEqual(({}, {}), self.sg._pullAttributesFromSRCs())

        newAttributes = {"lyrics": "P. Gradkowski",
                         "music": "Sam Composer",
                         "band": "The Developers",
                         "chord_mode": "CHORDS_ABOVE"}

        attributes.update(newAttributes)

        for attr, value in attributes.items():
            self.assertEqual(value, self.sg.tixi.getTextAttribute(song, attr), attr)
        self.assertEqual(len(attributes), self.sg.tixi.getNumberOfAttributes(song))

        dummyfile = os.path.abspath(os.path.join(self.test_dir, "dummy.xml"))
        with open(dummyfile, 'w') as f:
            f.write("This won't make a valid XML file")
            f.write("Tixi should fail trying to open it")

        self.assertTrue(os.path.isfile(dummyfile))

        # Now check missing and wrong files and non-matching attributes
        wrong_files = {"/songbook/section[1]/section[1]/song[1]": "./non_existent_file",
                       "/songbook/section[1]/section[1]/song[3]": dummyfile}
        for path, file in wrong_files.items():
            self.sg.tixi.addTextAttribute(path, "src", file)
        self.sg.tixi.addTextAttribute(song, "title", "This title will not match")
        self.sg.tixi.addTextAttribute(song, "band", "Another band")

        wrong_attributes = {song + ", title": ["My Test Song", "This title will not match"],
                            song + ", band": ["The Developers", "Another band"]}

        output = self.sg._pullAttributesFromSRCs()

        self.assertEqual((wrong_files, wrong_attributes), output)

    def test_assignXHTMLattributes(self):
        expected = [
            Song("sng_song_to_exclude_1.xhtml", "Song to exclude 1", "/songbook/section[1]/section[1]/song[1]"),
            Song("sng_my_test_song.xhtml", "My Test Song", "/songbook/section[1]/section[1]/song[2]"),
            Song("sng_song_a.xhtml", "Song A", "/songbook/section[1]/section[1]/song[3]"),
            Song("sng_song_b.xhtml", "Song B", "/songbook/section[1]/section[2]/song[1]"),
            Song("sng_song_c.xhtml", "Song C", "/songbook/section[1]/section[2]/song[2]"),
            Song("sng_song_a_1.xhtml", "Song A", "/songbook/section[2]/song[1]"),
            Song("sng_song_to_exclude_2.xhtml", "Song to exclude 2", "/songbook/section[2]/song[2]"),
            Song("sng_song_to_exclude_3.xhtml", "Song to exclude 3", "/songbook/section[2]/song[3]"),
            Song("sng_song_abba.xhtml", "Song ABBA", "/songbook/section[2]/song[4]"),
            Song("sng_youll_never_see_me.xhtml", "You'll never see me", "/songbook/section[3]/song[1]"),
            Song("sng_youll_never_see_me_again.xhtml", "You'll never see me again", "/songbook/section[3]/song[2]")
        ]

        for item in expected:
            self.assertEqual(item.title, self.sg.tixi.getTextAttribute(item.xml, "title"))
            self.assertFalse(self.sg.tixi.checkAttribute(item.xml, "xhtml"))

        self.sg._assignXHTMLattributes()

        for item in expected:
            self.assertEqual(item.title, self.sg.tixi.getTextAttribute(item.xml, "title"))
            self.assertEqual(item.file, self.sg.tixi.getTextAttribute(item.xml, "xhtml"))



    def test_write_indexes(self):
        self.sg._preprocess()
        self.assertEqual(self.test_dir, self.sg.settings.dir_out)
        expected_files = ["idx_authors.xhtml", "idx_songs.xhtml"]
        for file in expected_files:
            self.assertFalse(os.path.isfile(os.path.join(self.test_dir, file)))

        self.sg.write_indexes()

        for file in expected_files:
            self.assertTrue(os.path.isfile(os.path.join(self.test_dir + "/text", file)))

    def test_write_songs(self):
        self.sg._preprocess()
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

    def test_setHTMLtitle(self):
        # Prepare some files
        badfile = os.path.join(self.test_dir, "bad.html")
        goodfile = os.path.join(self.test_dir, "good.html")
        with open(badfile, 'w') as h:
            h.write('<?xml version="1.0"?>')
            h.write('<html>')
            h.write('</wrong_html>')
        tixi = Tixi()
        tixi.create("html")
        head = tixi.createElement("/html", "head")
        tixi.addTextElement(head, "title", "HTML Title")
        tixi.setElementNamespace("/html", 'http://www.w3.org/1999/xhtml', None)
        tixi.saveCompleteDocument(goodfile)

        self.assertTrue(os.path.isfile(badfile))
        self.assertTrue(os.path.isfile(goodfile))

        html_path = self.sg.tixi.createElement("/songbook/section[3]", "html")

        # File does not exist
        self.sg.tixi.addTextAttribute(html_path, "src", "./non_existent_file.html")
        self.assertEqual(r'- /songbook/section[3]/html  src="./non_existent_file.html" - file not found!',
                         self.sg.setHTMLtitle(html_path))

        # File as absolute path
        self.sg.tixi.addTextAttribute(html_path, "src", os.path.abspath(goodfile))
        # Should be OK
        self.assertEqual('', self.sg.setHTMLtitle(html_path))
        self.assertEqual("HTML Title", self.sg.tixi.getTextAttribute(html_path, "title"))

        self.sg.tixi.addTextAttribute(html_path, "title", "Non Matching")
        self.assertEqual('- /songbook/section[3]/html - title mismatch! '
                         '("Non Matching" vs "HTML Title" in {})'.format(os.path.abspath(goodfile)),
                         self.sg.setHTMLtitle(html_path))
        self.assertEqual("Non Matching", self.sg.tixi.getTextAttribute(html_path, "title"))

        # Break the good html - will have no title
        tixi.open(goodfile)
        tixi.registerNamespace("http://www.w3.org/1999/xhtml", "h")
        tixi.removeElement("/h:html/h:head/h:title")
        tixi.saveCompleteDocument(goodfile)

        self.assertEqual('- /songbook/section[3]/html - undefined document title '
                         'in {}!'.format(os.path.abspath(goodfile)), self.sg.setHTMLtitle(html_path))
        self.assertEqual("Non Matching", self.sg.tixi.getTextAttribute(html_path, "title"))

        # Now define the file as relative path
        rel = os.path.relpath(badfile, self.test_song_src)[3:]
        self.sg.tixi.addTextAttribute(html_path, "src", rel)

        self.assertEqual(
            '- /songbook/section[3]/html Non Matching src="{}" - source is not a valid HTML file!'.format(rel),
            self.sg.setHTMLtitle(html_path))
        self.assertEqual("Non Matching", self.sg.tixi.getTextAttribute(html_path, "title"))

    def test_copyHTML_resources(self):
        # First prepare some HTML
        htmlfile = os.path.join(self.test_dir, "good.html")
        tixi = Tixi()
        tixi.create("html")
        head = tixi.createElement("/html", "head")
        tixi.addTextElement(head, "title", "HTML Title")
        linkpath = tixi.createElement(head, "link")
        tixi.addTextAttribute(linkpath, "rel", "stylesheet")
        tixi.addTextAttribute(linkpath, "href", "../songbook.css")

        bpath = tixi.createElement("/html", "body")
        path = tixi.createElement(bpath, "img")
        tixi.addTextAttribute(path, "src", "./missing.txt")  # txt, because we don't care if these are real pictures
        path = tixi.createElement(bpath, "img")
        tixi.addTextAttribute(path, "src", "./res/ok.txt")
        path = tixi.createElement(bpath, "img")
        tixi.addTextAttribute(path, "src", "../text/samefile.txt")
        tixi.saveCompleteDocument(htmlfile)

        # Now create the files
        for path in [
            ["res"],
            ["text"],
            ["..", "text"],
            ["text", "res"]
        ]:
            dirpath = [self.test_dir] + path
            newPath = os.path.join(*dirpath)
            os.makedirs(newPath, exist_ok=True)
            self.newDirs.append(newPath)

        with open(os.path.join(self.test_dir, "res", "ok.txt"), 'w') as f:
            f.write("Some text that pretends to be a picture")
        with open(os.path.join(self.test_dir, "..", "text", "samefile.txt"), 'w') as f:
            f.write("Some text that pretends to be a picture")

        tixi.open(htmlfile)
        # ToDo: Find a way to trigger the other shutil.copy errors inside the function
        res = self.sg._copyHTML_resources(tixi)

        expected = "\n".join([
            "Following problems in HTML file {}:".format(htmlfile),
            "  - Resource file ../songbook.css not found",
            "  - Resource file ./missing.txt not found"
        ])
        self.assertEqual(expected, res)

    def test_write_sections(self):
        self.sg._preprocess()
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

        tixi = self.sg.tixi
        # Add a song that will have dead links:
        new_song = tixi.createElement("/songbook/section[1]/section[2]", "song")
        tixi.addTextAttribute(new_song, "title", "Song D")
        new_link = tixi.createElement(new_song, "link")
        tixi.addTextAttribute(new_link, "title", "No Such Title")
        self.sg._preprocess()
        links_start = {"/songbook/section[1]/section[1]/song[1 and @title='My Test Song']/link": None,
                       "/songbook/section[1]/section[1]/song[2 and @title='Song A']/link": "Song B",
                       "/songbook/section[1]/section[2]/song[1 and @title='Song B']/link": None,
                       "/songbook/section[1]/section[2]/song[2 and @title='Song C']/link": "No Such Title",
                       "/songbook/section[1]/section[2]/song[2 and @title='Song D']/link": "No Such Title",
                       "/songbook/section[2]/song[1 and @title='Song A']/link": None,
                       "/songbook/section[2]/song[2 and @title='Song ABBA']/link": "Song A"}

        links_end = {"/songbook/section[1]/section[1]/song[1 and @title='My Test Song']/link": "Song C",
                     "/songbook/section[1]/section[1]/song[2 and @title='Song A']/link[1]": "Song B",
                     "/songbook/section[1]/section[1]/song[2 and @title='Song A']/link[2]": "Song ABBA",
                     "/songbook/section[1]/section[2]/song[1 and @title='Song B']/link": "Song A",
                     "/songbook/section[1]/section[2]/song[2 and @title='Song C']/link": "My Test Song",
                     "/songbook/section[1]/section[2]/song[2 and @title='Song D']/link": None,
                     "/songbook/section[2]/song[1 and @title='Song A']/link[1]": "Song ABBA",
                     "/songbook/section[2]/song[1 and @title='Song A']/link[2]": "Song B",
                     "/songbook/section[2]/song[2 and @title='Song ABBA']/link": "Song A"}


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
        self.sg._preprocess()
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
        self.sg._preprocess()
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
        self.sg._preprocess()
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
        <navPoint id="num_374" playOrder="374"><navLabel><text>HTML Subdocument</text></navLabel><content src="text/test_html.xhtml"/></navPoint>
        <navPoint id="num_375" playOrder="375"><navLabel><text>Song ABBA</text></navLabel><content src="text/sng_song_abba.xhtml"/></navPoint>
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

    def test_getDefaultSongAttributes(self):
        self.assertEqual({"include": "true", "lyrics": "trad.", "music": "trad."}, self.sg._getDefaultSongAttributes())


if __name__ == '__main__':
    unittest.main()
