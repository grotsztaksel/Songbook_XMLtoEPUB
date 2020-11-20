# -*- coding: utf-8 -*-
"""
Created on 20.11.2020 18:35
 
@author: piotr
"""
import os

from config import CFG
from tixi import Tixi, tryXPathEvaluateNodeNumber
from .utf_simplifier import UtfSimplifier
from .html_writer import HtmlWriter
from .song_tuple import Song


class SongBookGenerator(object):
    def __init__(self, max_n=0):
        """

        :param max_n: Maximal number of songs to be processed from the source file. If not given,
                      all available songs will be processed
        """
        self.tixi = Tixi()
        self.tixi.open(CFG.SONG_SRC_XML, recursive=True)
        self.tixi.registerNamespacesFromDocument()
        self.N = max_n
        self.songs = []

        self.getBasicSongInfo()

    def getBasicSongInfo(self):

        xPath = "//song[@title]"

        n = tryXPathEvaluateNodeNumber(self.tixi, xPath)
        print("Found {} songs".format(n))
        if self.N > 0 and n < self.N:
            self.N = n

        print("Will process {} songs".format(self.N))

        for i in range(1, self.N + 1):
            xmlPath = self.tixi.xPathExpressionGetXPath(xPath, i)

            if not self.tixi.checkElement(xmlPath):
                return False
            title = self.tixi.getTextAttribute(xmlPath, "title")

            file_name_base = UtfSimplifier.toAscii(title).replace(" ", "_").lower()
            suffix = ""
            ext = ".xhtml"
            fileNameTaken = True

            while fileNameTaken:
                fileName = file_name_base + suffix + ext
                fileNameTaken = os.path.isfile(os.path.join(CFG.SONG_HTML_DIR, fileName))
                if not suffix:
                    number = 0
                number += 1
                suffix = "_" + str(number)

            self.songs.append(Song(fileName, title, xmlPath))

    def write_songs(self):
        """
        Read the source file and for each song defined, write a properly formatted
        song xml file in the required location
        """

        for song in self.songs:
            writer = HtmlWriter(self.tixi, song.xml)
            writer.write_song_file(song.file)

    def write_metadata(self):
        """Cleanup and rewrite the metadata.opf"""
        tixi = Tixi()
        opf = os.path.join(CFG.OUTPUT_DIR, "metadata.opf")
        opfuri = "http://www.idpf.org/2007/opf"
        tixi.open(opf)
        tixi.registerNamespacesFromDocument()
        tixi.registerNamespace(opfuri, "opf")
        tixi.registerNamespace("http://purl.org/dc/elements/1.1/", "dc")

        ns = dict()

        for p in [
            "/package",
            "/opf:package",
        ]:
            ns[p] = tixi.checkElement(p)

        # Clean the contents of specified elements to recreate them from scratch
        nodes = ["manifest", "spine", "guide"]
        for node in nodes:
            path = "/opf:package/opf:{}[1]".format(node)
            while tixi.checkElement(path):
                tixi.removeElement(path)

        for node in nodes:
            tixi.createElementNS("/opf:package", node, opfuri)

        manifest = "/opf:package/opf:manifest"
        spine = "/opf:package/opf:spine"

        tixi.addTextAttribute(spine, "toc", "ncx")

        itemAttributes = [{"href": "start.xhtml", "id": "start", "media-type": "application/xhtml+xml"},
                          {"href": "toc.ncx", "id": "ncx", "media-type": "application/x-dtbncx+xml"},
                          {"href": "songbook.css", "id": "css", "media-type": "text/css"}]

        for i, d in enumerate(itemAttributes):
            tixi.createElementNS(manifest, "item", opfuri)
            path = manifest + "/opf:item[{}]".format(i + 1)
            for key, value in d.items():
                tixi.addTextAttribute(path, key, value)

        tixi.createElementNS(spine, "itemref", opfuri)
        tixi.addTextAttribute(spine + "/opf:itemref", "idref", "start")

        for i, song in enumerate(self.songs):
            id = "id{}".format(i)

            tixi.createElement(manifest, "item")
            n = tixi.getNamedChildrenCount(manifest, "item")
            path = manifest + "/item[{}]".format(n)

            file = os.path.basename(CFG.SONG_HTML_DIR) + "/" + song.file
            tixi.addTextAttribute(path, "href", file)
            tixi.addTextAttribute(path, "id", id)
            tixi.addTextAttribute(path, "media-type", "application/xhtml+xml")

            tixi.createElementNS(spine, "itemref", opfuri)
            n = tixi.getNamedChildrenCount(spine, "opf:itemref")
            path = spine + "/opf:itemref[{}]".format(n)
            tixi.addTextAttribute(path, "idref", id)
        tixi.saveDocument(opf)
