# -*- coding: utf-8 -*-
"""
Created on 20.11.2020 18:35

@author: piotr
"""
import os

from config import CFG
from tixi import Tixi, tryXPathEvaluateNodeNumber, elementName
from .html_writer import HtmlWriter
from .utf_simplifier import UtfSimplifier


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

        self.id = None
        self.getBasicSongInfo()

    def getBasicSongInfo(self):
        # First remove the songs that have attribute include="false"
        xPathToRemove = "//song[@include='false']"
        for i in reversed(range(tryXPathEvaluateNodeNumber(self.tixi, xPathToRemove))):
            path = self.tixi.xPathExpressionGetXPath(xPathToRemove, i + 1)
            self.tixi.removeElement(path)

        xPath = "//song[@title]"
        n = tryXPathEvaluateNodeNumber(self.tixi, xPath)
        print("Found {} songs".format(n))
        if self.N > 0 and n < self.N or self.N == 0:
            self.N = n

        # Remove the abundant songs
        while tryXPathEvaluateNodeNumber(self.tixi, xPath) > self.N:
            path = self.tixi.xPathExpressionGetXPath(xPath, self.N + 1)
            self.tixi.removeElement(path)

        # Now remove sections that do not have songs inside
        xPath_emptySection = "//section[not(descendant::song)]"
        for i in reversed(range(tryXPathEvaluateNodeNumber(self.tixi, xPath_emptySection))):
            path = self.tixi.xPathExpressionGetXPath(xPath_emptySection, i + 1)
            self.tixi.removeElement(path)

        print("Will process {} songs".format(self.N))

        usedFileNames = []
        xPath = "//*[self::song or self::section][@title]"
        n = tryXPathEvaluateNodeNumber(self.tixi, xPath)
        for i in range(1, n + 1):
            xmlPath = self.tixi.xPathExpressionGetXPath(xPath, i)

            if not self.tixi.checkElement(xmlPath):
                return False
            title = self.tixi.getTextAttribute(xmlPath, "title")

            if elementName(xmlPath) == "song":
                prefix = "sng_"
            else:
                prefix = "sec_"
            file_name_base = UtfSimplifier.toAscii(title).replace(" ", "_").lower()
            suffix = ""
            ext = ".xhtml"
            fileNameTaken = True
            number = ""
            while fileNameTaken:
                fileName = prefix + file_name_base + suffix + ext
                fileNameTaken = fileName in usedFileNames
                if not suffix:
                    number = 0
                number += 1
                suffix = "_" + str(number)
            usedFileNames.append(fileName)

            self.tixi.addTextAttribute(xmlPath, "xhtml", fileName)

    def write_songs(self):
        """
        Read the source file and for each song defined, write a properly formatted
        song xml file in the required location
        """

        xPath = "//song"
        for i in range(tryXPathEvaluateNodeNumber(self.tixi, xPath)):
            xml = self.tixi.xPathExpressionGetXPath(xPath, i + 1)
            file = self.tixi.getTextAttribute(xml, "xhtml")

            writer = HtmlWriter(self.tixi, xml)
            writer.write_song_file(file)

    def createTwoWayLinks(self):
        """
            Find all songs that have links to other songs. Then, find that other songs and create links to the songs
            that linked to these songs

            For example, a song A is found that links to B:

            <song title="A">
                <link title="B">
            </song>

            Find the song B and create link to A:

            <song title="B">
                <link title="A">
            </song>
        """

        xPathFrom = "//song/link[@title]"

        linksToCreate = True
        while linksToCreate:
            n = tryXPathEvaluateNodeNumber(self.tixi, xPathFrom)
            linksToCreate = list()
            linksToRemove = list()
            for i in range(1, n + 1):
                path_link = self.tixi.xPathExpressionGetXPath(xPathFrom, i)
                xpath_parent_song = path_link + "/ancestor::song"
                path_song = self.tixi.xPathExpressionGetXPath(xpath_parent_song, 1)
                title_parent = self.tixi.getTextAttribute(path_song, "title")
                title_link = self.tixi.getTextAttribute(path_link, "title")

                # Find all songs that have title mentioned in the link
                xPath = "//song[@title=\"{}\"]".format(title_link)
                m = tryXPathEvaluateNodeNumber(self.tixi, xPath)
                if m == 0:
                    linksToRemove.append(path_link)
                for j in range(1, m + 1):
                    target_path = self.tixi.xPathExpressionGetXPath(xPath, j)
                    # Do not create link, if there already is one
                    if tryXPathEvaluateNodeNumber(self.tixi, target_path + "/link[@title='{}']".format(title_parent)):
                        continue
                    nlinks = self.tixi.getNamedChildrenCount(target_path, "link")
                    linksToCreate.append((target_path, nlinks + 1, title_parent))
            for link in linksToCreate:
                self.tixi.createElementAtIndex(link[0], "link", link[1])
                newPath = "{}/link[{}]".format(link[0], link[1])
                self.tixi.addTextAttribute(newPath, "title", link[2])
            for link in reversed(linksToRemove):
                self.tixi.removeElement(link)

    def write_metadata(self):
        """Cleanup and rewrite the metadata.opf"""
        tixi = Tixi()
        opf = os.path.join(CFG.OUTPUT_DIR, "metadata.opf")
        opfuri = "http://www.idpf.org/2007/opf"
        tixi.open(opf)
        tixi.registerNamespacesFromDocument()
        tixi.registerNamespace(opfuri, "opf")
        tixi.registerNamespace("http://purl.org/dc/elements/1.1/", "dc")

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

        xPath = "//song"
        for i in range(1, tryXPathEvaluateNodeNumber(self.tixi, xPath) + 1):
            xml = self.tixi.xPathExpressionGetXPath(xPath, i)
            fileName = self.tixi.getTextAttribute(xml, "xhtml")
            id = "id{}".format(i)

            tixi.createElement(manifest, "item")
            n = tixi.getNamedChildrenCount(manifest, "item")
            path = manifest + "/item[{}]".format(n)

            file = os.path.basename(CFG.SONG_HTML_DIR) + "/" + fileName
            tixi.addTextAttribute(path, "href", file)
            tixi.addTextAttribute(path, "id", id)
            tixi.addTextAttribute(path, "media-type", "application/xhtml+xml")

            tixi.createElementNS(spine, "itemref", opfuri)
            n = tixi.getNamedChildrenCount(spine, "opf:itemref")
            path = spine + "/opf:itemref[{}]".format(n)
            tixi.addTextAttribute(path, "idref", id)
        tixi.saveDocument(opf)

    def write_toc(self):
        """Cleanup and rewrite the toc.ncx"""
        tixi = Tixi()
        toc = os.path.join(CFG.OUTPUT_DIR, "toc.ncx")
        tixi.open(toc)
        tixi.registerNamespacesFromDocument()
        tixi.registerNamespace("http://www.daisy.org/z3986/2005/ncx/", "ncx")
        tixi.registerNamespace("http://www.w3.org/XML/", "xml")

        if tixi.checkElement("/ncx:ncx/ncx:navMap"):
            tixi.removeElement("/ncx:ncx/ncx:navMap")

        tixi.createElement("/ncx:ncx", "navMap")
        navMap = "/ncx:ncx/navMap"

        assert tixi.checkElement(navMap)

        self.id = 1
        self._createNavPoint("/songbook", navMap, tixi)

        tixi.saveDocument(toc)

    def _createNavPoint(self, secsongPath: str, npPath: str, tixi_ncx: Tixi) -> None:
        """
            Recursive helper function creating navPoint elements for each song/section in the source tixi
        """
        attr_id = "num_{}".format(self.id)  # used for attribute "id"
        attr_po = "{}".format(self.id)  # used for attribute "playOrder"

        isRoot = secsongPath == "/" + self.tixi.getChildNodeName("/", 1)
        if not isRoot:
            secsongTitle = self.tixi.getTextAttribute(secsongPath, "title")
            secsongFile = self.tixi.getTextAttribute(secsongPath, "xhtml")
            tixi_ncx.createElement(npPath, "navPoint")
            n = tixi_ncx.getNamedChildrenCount(npPath, "navPoint")
            my_npPath = "{}/navPoint[{}]".format(npPath, n)

            tixi_ncx.addTextAttribute(my_npPath, "id", attr_id)
            tixi_ncx.addTextAttribute(my_npPath, "playOrder", attr_po)

            tixi_ncx.createElement(my_npPath, "navLabel")
            tixi_ncx.addTextElement(my_npPath + "/navLabel", "text", secsongTitle)
            tixi_ncx.createElement(my_npPath, "content")
            tixi_ncx.addTextAttribute(my_npPath + "/content", "src", "text/" + secsongFile)

            self.id += 1
        else:
            my_npPath = npPath

        xPath = "{}/*[self::song or self::section]".format(secsongPath)
        n = tryXPathEvaluateNodeNumber(self.tixi, xPath)
        for i in range(n):
            path = self.tixi.xPathExpressionGetXPath(xPath, i + 1)
            self._createNavPoint(path, my_npPath, tixi_ncx)
