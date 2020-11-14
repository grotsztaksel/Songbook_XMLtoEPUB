# -*- coding: utf-8 -*-
"""
Created on Sat Nov 14 17:56:39 2020

@author: piotr
"""
__all__=['HtmlWriter']

import os

from tixi import Tixi
from config import CFG
from .utf_simplifier import UtfSimplifier

class HtmlWriter():
    def __init__(self, tixi:Tixi, path, settings=None):
        super(HtmlWriter, self).__init__()
        self.settings = settings
        self.src_tixi = tixi
        self.src_path = path
        self.dir = CFG.SONG_HTML_DIR

        self.root = "html"
        
        self.tixi = Tixi()
        
        self.tixi.create(self.root)
        self.root = "/"+self.root
        self.tixi.registerNamespace("http://www.w3.org/2001/XMLSchema-instance", 'xsd')
        
    def write_song_file(self) -> bool:
        """
        Read the xml node in song_path and write a valid HTML file out of it in the desired location
        """
        if not self.src_tixi.checkElement(self.src_path):
            return False
        title = self.src_tixi.getTextAttribute(self.src_path, "title")
        
        file_name_base = UtfSimplifier.toAscii(title).replace(" ", "_").lower()
        suffix=""
        ext = ".xhtml"
        fileNameTaken = True
        
        while fileNameTaken:
            fileName = file_name_base + suffix + ext
            fileNameTaken = os.path.isfile(os.path.join(CFG.SONG_HTML_DIR ,fileName))
            if not suffix:
                number = 0
            number += 1
            suffix = "_" + str(number)

        print ("Saving song: {}\n  -- to file {}".format(title, fileName))
        
        self.write_html_header()
        self.write_song_header(title)
        
        outputFile = os.path.join(CFG.SONG_HTML_DIR ,fileName)
        self.tixi.saveCompleteDocument(outputFile)
        
    def write_html_header(self):
        self.tixi.createElement(self.root, "head")
        headPath = self.root + "/head"
        
        
        self.tixi.addTextElement(headPath, "title", "Śpiewnik")
        self.tixi.createElement(headPath, "link")
        
        linkPath = headPath + "/link"
        
        
        attrs = {"rel" : "stylesheet",
                 "type":"text/css",
                 "href": "../songbook.css"}
        for a in attrs.keys():
            self.tixi.addTextAttribute(linkPath, a, attrs[a])
        
    def write_song_header(self, title):
        if self.src_tixi.checkAttribute(self.src_path, "music"):
            music = self.src_tixi.getTextAttribute(self.src_path, "music")
        else:
            music = "trad."
        if self.src_tixi.checkAttribute(self.src_path, "lyrics"):
            lyrics = self.src_tixi.getTextAttribute(self.src_path, "lyrics")
        else:
            lyrics = "trad."
            
        # <body/>    
        self.tixi.createElement(self.root, "body")
        bpath = self.root + "/body"
        
        
        # <h1>[title]</h1>
        self.tixi.addTextElement(bpath,"h1", title)
        
        
        # <p class="authors">sł. [lyrics], muz. [music]</p>
        self.tixi.addTextElement(bpath,"p", 
                                    "s&#x142;. {}, muz. {}".format(lyrics, music))
        self.tixi.addTextAttribute(bpath+"/p", "class", "authors")
        
        