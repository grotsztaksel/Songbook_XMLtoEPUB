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
    """A set of common (static) methods allowing to write and save the XHTML files in a similar way"""

    @staticmethod
    def prepare_html_tixi() -> Tuple[Tixi, str]:
        tixi = Tixi()
        tixi.create("html")
        tixi.addTextAttribute("/html", "xmlns", "http://www.w3.org/1999/xhtml")
        tixi.createElement("/html", "head")

        headPath = "/html/head"

        tixi.addTextElement(headPath, "title", "Śpiewnik")
        tixi.createElement(headPath, "link")

        linkPath = headPath + "/link"

        attrs = {"rel": "stylesheet",
                 "type": "text/css",
                 "href": "../songbook.css"}
        for a in attrs:
            tixi.addTextAttribute(linkPath, a, attrs[a])

        return tixi, "/html"

    def saveFile(tixi, fileName):
        """Apply specific formatting and save the content of the self.tixi to a file filename"""
        text = tixi.exportDocumentAsString()
        replaceRules = {
            "&lt;br/&gt;": "<br/>",
            "&amp;nbsp;": "&nbsp;",
            "&amp;apos;": "&apos;",
            "&amp;quot;": "&quot;"
        }
        for rr in replaceRules.keys():
            text = text.replace(rr, replaceRules[rr])
        # Now regular expressions

        # fold the table rows <tr><td></td></tr>into a single line
        text = re.sub(r"(<\/?t[dr].*?>)\s*(<\/?t[dr])", r"\1\2", text)

        file = open(os.path.join(fileName), "w", encoding='utf8')
        file.write(text)
        file.close()
