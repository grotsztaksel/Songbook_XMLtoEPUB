# -*- coding: utf-8 -*-
"""
Created on 24.01.2021 00:47
 
@author: piotr
"""

import os
import unittest

from config import EpubSongbookConfig
from tixi import Tixi
from tools.html_writer import HtmlWriter


class TestHtmlWriter(unittest.TestCase):
    def setUp(self):
        self.src_file = os.path.join(os.path.dirname(__file__), "resources", "test_song_src.xml")
        self.tixi = Tixi()
        self.tixi.open(self.src_file)
        self.settings = EpubSongbookConfig(self.tixi)
        self.writer = HtmlWriter(self.tixi, self.settings)
        self.test_output = os.path.join(os.path.dirname(self.src_file), "test_output.xhtml")

    def tearDown(self):
        if os.path.isfile(self.test_output):
            os.remove(self.test_output)

    def test_init(self):
        expected_html = """
        <?xml version="1.0"?>
         <html xmlns="http://www.w3.org/1999/xhtml">
             <head>
                <title>My Songbook</title>
                <link rel="stylesheet" type="text/css" href="../songbook.css"/>
             </head>
        </html>
        """.strip()
        expected_tixi = Tixi()
        expected_tixi.openString(expected_html)
        self.assertEqual(expected_tixi.exportDocumentAsString(),
                         self.writer.tixi.exportDocumentAsString())

    def test_saveFile(self):
        # First add some stuff that will have to be modified:
        tixi = self.writer.tixi
        path = tixi.getNewElementPath("/html", "body")
        tixi.addTextElement(path, "p", "some text<br/>and a new line&nbsp;")
        path = tixi.getNewElementPath(path, "table")
        path = tixi.getNewElementPath(path, "tr")
        tixi.addTextElement(path, "td", "blah")
        tixi.addTextElement(path, "td", "glah")
        tixi.addTextElement(path, "td", "meeh")
        tixi.createElement(path, "td")

        html_before = """
        <?xml version="1.0"?>
        <html xmlns="http://www.w3.org/1999/xhtml">
            <head>
                <title>My Songbook</title>
                <link rel="stylesheet" type="text/css" href="../songbook.css"/>
            </head>
            <body>
                <p>some text&lt;br/&gt;and a new line&amp;nbsp;</p>
                <table>
                    <tr>
                        <td>blah</td>
                        <td>glah</td>
                        <td>meeh</td>
                        <td/>
                    </tr>
                </table>
            </body>
        </html>""".strip().replace("        <", "<").replace("    ", "  ")
        self.assertEqual(html_before, tixi.exportDocumentAsString().strip())

        html_after = """
        <?xml version="1.0" encoding='utf-8'?>
        <html xmlns="http://www.w3.org/1999/xhtml">
            <head>
                <title>My Songbook</title>
                <link rel="stylesheet" type="text/css" href="../songbook.css"/>
            </head>
            <body>
                <p>some text<br/>and a new line&nbsp;</p>
                <table>
                    <tr><td>blah</td><td>glah</td><td>meeh</td><td/></tr>
                </table>
            </body>
        </html>""".strip().replace("        <", "<").replace("    ", "  ")

        self.writer.saveFile(self.test_output)
        with open(self.test_output, "r", encoding='utf8') as f:
            expected = f.read()

        self.assertEqual(html_after, expected.strip())


if __name__ == '__main__':
    unittest.main()
