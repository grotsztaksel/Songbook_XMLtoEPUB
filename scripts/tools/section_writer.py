# -*- coding: utf-8 -*-
"""
Created on 22.11.2020 17:05
 
@author: piotr
"""

__all__ = ['SectionWriter']

import os

from config import CFG
from tixi import Tixi
from .html_writer import HtmlWriter


class SectionWriter(object):
    def __init__(self, tixi: Tixi, path: str):
        super(SectionWriter, self).__init__()

        self.src_tixi = tixi
        self.src_path = path
        self.dir = CFG.SONG_HTML_DIR

        self.tixi, self.root = HtmlWriter.prepare_html_tixi()

    def write_section_file(self, fileName):
        """
        Read the xml node for the section in and write a valid HTML file out of it in the desired location
        """
        title = self.src_tixi.getTextAttribute(self.src_path, "title")
        print("Saving section: {}\n  -- to file {}".format(title, fileName))

        self.write_toc()

        HtmlWriter.saveFile(self.tixi, os.path.join(CFG.SONG_HTML_DIR, fileName))

    def write_toc(self):
        # <body/>
        self.tixi.createElement(self.root, "body")
        bpath = self.root + "/body"
        if self.src_tixi.getTextAttribute(self.src_path, "title"):
            title = self.src_tixi.getTextAttribute(self.src_path, "title")
        else:
            title = "Spis piosenek"

        self.tixi.addTextElement(bpath, "h2", title)

        self.tixi.createElement(bpath, "p")

        ppath = bpath + "/p"
        self._createUl(ppath, self.src_path)

    def _createUl(self, targetPath, sourcePath):
        """Recursively create the <li> and nested <ul> elements for each
           item in section"""
        self.tixi.createElement(targetPath, "ul")
        nul = self.tixi.getNamedChildrenCount(targetPath, "ul")
        ulPath = "{}/ul[{}]".format(targetPath, nul)
        xPath = sourcePath + "/*[self::section or self::song]"

        for path in self.src_tixi.getPathsFromXPathExpression(xPath):
            title = self.src_tixi.getTextAttribute(path, "title")
            xhtml = self.src_tixi.getTextAttribute(path, "xhtml")

            self.tixi.createElement(ulPath, "li")
            nli = self.tixi.getNamedChildrenCount(ulPath, "li")
            liPath = "{}/li[{}]".format(ulPath, nli)
            self.tixi.addTextElement(liPath, "a", title)
            aPath = "{}/a".format(liPath)

            self.tixi.addTextAttribute(aPath, "href", xhtml)
            if Tixi.elementName(path) == "section":
                self._createUl(liPath, path)
