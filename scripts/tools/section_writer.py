# -*- coding: utf-8 -*-
"""
Created on 22.11.2020 17:05
 
@author: piotr
"""

__all__ = ['SectionWriter']

import os
import re

from config import CFG
from tixi import Tixi, tryXPathEvaluateNodeNumber, elementName


class SectionWriter(object):
    def __init__(self, tixi: Tixi, path: str, settings=None):
        super(SectionWriter, self).__init__()
        self.settings = settings
        self.src_tixi = tixi
        self.src_path = path
        self.dir = CFG.SONG_HTML_DIR

        self.root = "html"

        self.tixi = Tixi()

        self.tixi.create(self.root)

        self.root = "/" + self.root
        self.tixi.addTextAttribute(self.root, "xmlns", "http://www.w3.org/1999/xhtml")

    def write_section_file(self, fileName):
        """
        Read the xml node for the section in and write a valid HTML file out of it in the desired location
        """
        title = self.src_tixi.getTextAttribute(self.src_path, "title")
        print("Saving section: {}\n  -- to file {}".format(title, fileName))

        self.write_html_header()
        self.write_toc()

        self.saveFile(fileName)

    def saveFile(self, fileName):
        """Apply specific formatting andf save the content of the self.tixi to a file filename"""
        text = self.tixi.exportDocumentAsString()
        replaceRules = {
            "&lt;br/&gt;": "<br/>",
            "&amp;nbsp;": "&nbsp;"
        }
        for rr in replaceRules.keys():
            text = text.replace(rr, replaceRules[rr])

        # Now regular expressions
        #  .. Nothing to do here for now
        # text = re.sub(r"(<\/?t[dr].*?>)\s*(<\/?t[dr])", r"\1\2", text)

        file = open(os.path.join(CFG.SONG_HTML_DIR, fileName), "w", encoding='utf8')
        file.write(text)
        file.close()

    def write_html_header(self):
        self.tixi.createElement(self.root, "head")
        headPath = self.root + "/head"

        self.tixi.addTextElement(headPath, "title", "Śpiewnik")
        self.tixi.createElement(headPath, "link")

        linkPath = headPath + "/link"

        attrs = {"rel": "stylesheet",
                 "type": "text/css",
                 "href": "../songbook.css"}
        for a in attrs.keys():
            self.tixi.addTextAttribute(linkPath, a, attrs[a])

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

        for i in range(tryXPathEvaluateNodeNumber(self.src_tixi, xPath)):
            path = self.src_tixi.xPathExpressionGetXPath(xPath, i + 1)
            title = self.src_tixi.getTextAttribute(path, "title")
            xhtml = self.src_tixi.getTextAttribute(path, "xhtml")

            self.tixi.createElement(ulPath, "li")
            nli = self.tixi.getNamedChildrenCount(ulPath, "li")
            liPath = "{}/li[{}]".format(ulPath, nli)
            self.tixi.addTextElement(liPath, "a", title)
            aPath = "{}/a".format(liPath)

            self.tixi.addTextAttribute(aPath, "href", xhtml)
            if elementName(path) == "section":
                self._createUl(liPath, path)
