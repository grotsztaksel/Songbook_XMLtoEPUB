# -*- coding: utf-8 -*-
"""
Created on 27.11.2020 20:34
 
@author: Piotr Gradkowski <grotsztaksel@o2.pl>
"""

__authors__ = ['Piotr Gradkowski <grotsztaksel@o2.pl>']
__date__ = '2020-11-27'
__all__ = ['HtmlWriter']

import logging
import os
import re

from scripts.config import EpubSongbookConfig
from scripts.tixi import Tixi


class HtmlWriter(object):
    """A generic class used to write the xhtml files."""

    def __init__(self, tixi: Tixi, settings: EpubSongbookConfig):
        self.src_tixi = tixi
        self.settings = settings
        self.tixi = Tixi()
        self.tixi.create("html")
        self.tixi.addTextAttribute("/html", "xmlns", "http://www.w3.org/1999/xhtml")
        self.tixi.createElement("/html", "head")

        headPath = "/html/head"

        self.tixi.addTextElement(headPath, "title", self.settings.title)
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

        # First of all, add encoding if present
        if self.settings.encoding is not None:
            text = text[:19] + " encoding='{}'".format(self.settings.encoding) + text[19:]
        replaceRules = {
            "&lt;br/&gt;": "<br/>",
            "&amp;": "&"
        }
        for rr in replaceRules:
            text = text.replace(rr, replaceRules[rr])
        # Now regular expressions

        # fold the table rows <tr><td></td></tr>into a single line
        text = re.sub(r"(<\/?t[dr].*?>)\s+(<\/?t[dr])", r"\1\2", text)
        # repeat to catch also the overlapping tokens: possible if td is empty (<td/>)
        text = re.sub(r"(<\/?t[dr].*?>)\s+(<\/?t[dr])", r"\1\2", text)

        logging.debug("Writing HTML file: {}".format(os.path.abspath(fileName)))
        file = open(os.path.join(fileName), "w", encoding='utf8')
        file.write(text)
        file.close()
        logging.debug("   -- OK")
