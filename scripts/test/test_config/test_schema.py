# -*- coding: utf-8 -*-
"""
Created on 20.11.2020 20:42
 
@author: Piotr Gradkowski <grotsztaksel@o2.pl>
"""

__authors__ = ['Piotr Gradkowski <grotsztaksel@o2.pl>']
__date__ = '2020-11-20'

import os
import unittest

from config import epubsongbookconfig
from tixi import Tixi, TixiException, ReturnCode


class TestSchema(unittest.TestCase):
    def setUp(self):
        self.xsdpath = os.path.join(os.path.dirname(os.path.abspath(epubsongbookconfig.__file__)), "source_schema.xsd")

    def test_xsd(self):
        """Check if the XSD file is there at all and can be opened"""
        self.assertTrue(os.path.isfile(self.xsdpath))
        tixi = Tixi()
        tixi.openDocument(self.xsdpath)

    def test_xsd_valid(self):
        """Check if the XSD file can even be used for validation"""
        tixi = Tixi()
        string = '<?xml version="1.0"?><root><child/></root>'
        tixi.openString(string)

        self.assertNonSchemaCompliant(tixi)

    def test_empty_src(self):
        tixi = Tixi()
        tixi.create("songbook")
        tixi.registerNamespace("http://www.w3.org/2001/XMLSchema", "xsd")

        tixi.schemaValidateFromFile(self.xsdpath)

    def test_cascade_of_chapters(self):
        tixi = Tixi()
        tixi.create("songbook")
        tixi.registerNamespace("http://www.w3.org/2001/XMLSchema", "xsd")

        path = "/songbook"
        for i in range(4):
            tixi.createElement(path, "section")
            path += "/section"
            tixi.addTextAttribute(path, "title", "someTitle")
            tixi.schemaValidateFromFile(self.xsdpath)

        tixi.createElement(path, "song")
        tixi.addTextAttribute(path + "/song", "title", "Song Title")
        tixi.schemaValidateFromFile(self.xsdpath)

        # Should be illegal to place a song AND section on the same level
        tixi.createElement(path, "section")
        tixi.addTextAttribute(path + "/section", "title", "Illegal section title")

        self.assertNonSchemaCompliant(tixi)

    def test_testXMLschemaCompliant(self):
        test_xml_file = os.path.join(os.path.dirname(__file__),
                                     "..", "test_tools", "resources", "test_song_src.xml")
        self.assertTrue(os.path.isfile(test_xml_file))
        tixi = Tixi()
        tixi.open(test_xml_file, recursive=True)
        tixi.removeExternalLinks()
        tixi.schemaValidateFromFile(self.xsdpath)

    def assertNonSchemaCompliant(self, tixi):
        try:
            tixi.schemaValidateFromFile(self.xsdpath)
        except TixiException as e:
            self.assertEqual(ReturnCode.NOT_SCHEMA_COMPLIANT, e.code)


if __name__ == '__main__':
    unittest.main()
