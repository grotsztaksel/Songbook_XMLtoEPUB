# -*- coding: utf-8 -*-
"""
Created on 22.11.2020 17:45
 
@author: Piotr Gradkowski <grotsztaksel@o2.pl>
"""

__authors__ = ['Piotr Gradkowski <grotsztaksel@o2.pl>']
__date__ = '2020-11-22'

import unittest
from src.tixi import Tixi
import os
from src.tools import SectionWriter
from src.tools.song_book_generator import SongBookGenerator


class TestSectionWriter(unittest.TestCase):
    def setUp(self):
        src_xml = os.path.join(os.path.dirname(__file__), "resources", "test_song_src.xml")
        tixi = Tixi()
        tixi.open(src_xml)
        self.sg = SongBookGenerator(src_xml)
        self.sg.tixi = tixi
        self.sg._preprocess()
        self.tixi = self.sg.tixi
        self.test_output = os.path.join(os.path.dirname(__file__), "test_section.xml")

    def tearDown(self):
        if os.path.isfile(self.test_output):
            os.remove(self.test_output)

    def test_write_section_file(self):
        expected = """<?xml version="1.0" encoding='utf-8'?>
        <html xmlns="http://www.w3.org/1999/xhtml">
          <head>
            <title>My Songbook</title>
            <link rel="stylesheet" type="text/css" href="../songbook.css"/>
          </head>
          <body>
            <h2>Section 1</h2>
            <p>
              <ul>
                <li>
                  <a href="sec_section_1.1.xhtml">Section 1.1</a>
                  <ul>
                    <li>
                      <a href="sng_my_test_song.xhtml">My Test Song</a>
                    </li>
                    <li>
                      <a href="sng_song_a.xhtml">Song A</a>
                    </li>
                  </ul>
                </li>
                <li>
                  <a href="sec_section_1.2.xhtml">Section 1.2</a>
                  <ul>
                    <li>
                      <a href="sng_song_b.xhtml">Song B</a>
                    </li>
                    <li>
                      <a href="sng_song_c.xhtml">Song C</a>
                    </li>
                  </ul>
                </li>
              </ul>
            </p>
          </body>
        </html>""".replace("        <", "<").strip()

        sw = SectionWriter(self.tixi, self.sg.settings, "/songbook/section[1]")
        sw.write_section_file(self.test_output)

        self.assertTrue(os.path.isfile(self.test_output))
        with open(self.test_output, "r") as f:
            content = f.read()

        self.assertEqual(expected, content.strip())

    def test_write_toc(self):
        sw = SectionWriter(self.tixi, self.sg.settings, "/songbook/section[1]")
        sw.write_toc()

        expectedTixi = Tixi()
        expectedTixi.openString(
            """<?xml version="1.0"?><html xmlns="http://www.w3.org/1999/xhtml">
               <head><title>My Songbook</title><link rel="stylesheet" type="text/css" href="../songbook.css"/></head>
               <body>
                <h2>Section 1</h2>
                <p>
                  <ul><li><a href="sec_section_1.1.xhtml">Section 1.1</a>
                       <ul><li><a href="sng_my_test_song.xhtml">My Test Song</a></li>
                           <li><a href="sng_song_a.xhtml">Song A</a></li>
                       </ul>
                      </li>
                      <li><a href="sec_section_1.2.xhtml">Section 1.2</a>
                          <ul><li><a href="sng_song_b.xhtml">Song B</a></li>
                              <li><a href="sng_song_c.xhtml">Song C</a></li>
                          </ul>
                      </li>
                  </ul>
                </p>
              </body>
            </html>
            """)
        self.assertEqual(expectedTixi.exportDocumentAsString(),
                         sw.tixi.exportDocumentAsString())

    def test_createUl(self):
        sw = SectionWriter(self.tixi, self.sg.settings, "/songbook/section[1]")
        # Replace writer's tixi with an empty one
        tixi = Tixi()
        tixi.create("root")

        sw.tixi = tixi
        sw._createUl("/root", "/songbook/section[1]")

        expected_str = """<root>
                        <ul><li><a href="sec_section_1.1.xhtml">Section 1.1</a>
                                 <ul><li><a href="sng_my_test_song.xhtml">My Test Song</a></li>
                                     <li><a href="sng_song_a.xhtml">Song A</a></li>
                                 </ul>
                            </li>
                            <li><a href="sec_section_1.2.xhtml">Section 1.2</a>
                                <ul>
                                    <li><a href="sng_song_b.xhtml">Song B</a></li>
                                    <li><a href="sng_song_c.xhtml">Song C</a></li>
                                </ul>
                            </li>
                        </ul>
                        </root>"""
        expectedTixi = Tixi()
        expectedTixi.openString(expected_str)

        self.assertEqual(expectedTixi.exportDocumentAsString(),
                         sw.tixi.exportDocumentAsString())


if __name__ == '__main__':
    unittest.main()
