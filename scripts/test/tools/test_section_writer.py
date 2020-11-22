# -*- coding: utf-8 -*-
"""
Created on 22.11.2020 17:45
 
@author: piotr
"""

import unittest
from tixi import  Tixi
import os
from tools import SectionWriter
from tools.song_book_generator import SongBookGenerator


class TestSectionWriter(unittest.TestCase):
    def setUp(self):
        src_xml = os.path.join(os.path.dirname(__file__), "test_song_src.xml")
        tixi = Tixi()
        tixi.open(src_xml)
        self.sg = SongBookGenerator()
        self.sg.tixi = tixi
        self.sg.getBasicSongInfo()
        self.tixi = self.sg.tixi

    def test_write_html_header(self):
        sw = SectionWriter(self.tixi, "/songbook/section[1]")
        sw.write_html_header()

        expectedTixi = Tixi()
        expectedTixi.openString("""<?xml version="1.0"?><html><head><title>&#x15A;piewnik</title>
                                    <link rel="stylesheet" type="text/css" href="../songbook.css"/>
                                    </head></html>""")

        self.assertEqual(expectedTixi.exportDocumentAsString(),
                         sw.tixi.exportDocumentAsString())
    def test_write_toc(self):
        sw = SectionWriter(self.tixi, "/songbook/section[1]")
        sw.write_toc()

        expectedTixi = Tixi()
        expectedTixi.openString(
        """<?xml version="1.0"?>
        <html>
          <body>
            <h2>Section 1</h2>
            <p>
              <ul><li><a href="sec_section_1.1.xhtml">Section 1.1</a>
                      <ul><li><a href="sng_song_a.xhtml">Song A</a></li></ul>
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

if __name__ == '__main__':
    unittest.main()
