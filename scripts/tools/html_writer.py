# -*- coding: utf-8 -*-
"""
Created on 27.11.2020 20:34
 
@author: piotr
"""
import os
import re

from typing import Tuple

from tixi import Tixi


class HtmlWriter(object):
    """A generic class used to write the xhtml files."""

    def __init__(self, tixi: Tixi):
        self.src_tixi = tixi
        self.tixi = Tixi()
        self.tixi.create("html")
        self.tixi.addTextAttribute("/html", "xmlns", "http://www.w3.org/1999/xhtml")
        self.tixi.createElement("/html", "head")

        headPath = "/html/head"

        self.tixi.addTextElement(headPath, "title", "Śpiewnik")
        self.tixi.createElement(headPath, "link")

        linkPath = headPath + "/link"

        attrs = {"rel": "stylesheet",
                 "type": "text/css",
                 "href": "../songbook.css"}
        for a in attrs:
            self.tixi.addTextAttribute(linkPath, a, attrs[a])

        self.root = "/html"

    def saveFile(self, fileName):
        """Apply specific formatting and save the content of the self.self.tixi to a file filename"""
        text = self.tixi.exportDocumentAsString()
        replaceRules = {
            "&lt;br/&gt;": "<br/>",
            "&amp;": "&"
        }
        for rr in replaceRules:
            text = text.replace(rr, replaceRules[rr])
        # Now regular expressions

        # fold the table rows <tr><td></td></tr>into a single line
        text = re.sub(r"(<\/?t[dr].*?>)\s*(<\/?t[dr])", r"\1\2", text)

        file = open(os.path.join(fileName), "w", encoding='utf8')
        file.write(text)
        file.close()