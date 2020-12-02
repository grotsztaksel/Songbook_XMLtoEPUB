# -*- coding: utf-8 -*-
"""
Created on 20.11.2020 18:35

@author: piotr
"""
import os

from config import CFG
from tixi import Tixi
from .index_authors_writer import AuthorsWriter
from .index_songs_writer import SongsIndexWriter
from .song_writer import SongWriter
from .section_writer import SectionWriter
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

    @staticmethod
    def split_song_xml(input):
        """Read in the input song source and add the externalData attributes. Then save files with
        Tixi

        NOTE: Unfortunately, this function does not work - Tixi3 throws errors. Apparently it is not enough to add
              externalData attributes to force Tixi save the data in a separate file.
              Nor does the function addExternalLink split the document to more docs.
        """
        # externalFileName="song_title.xml"
        # externalDataDirectory="file://./"
        # externalDataNodePath="/songbook/section"
        return
        tixi = Tixi()
        tixi.open(input, recursive=True)

        usedFileNames = []
        songXPath = "//song[@title]"
        for song in tixi.getPathsFromXPathExpression(songXPath):
            title = tixi.getTextAttribute(song, "title")

            file_name_base = UtfSimplifier.toAscii(title).replace(" ", "_").lower()
            suffix = ""
            ext = ".xml"
            fileNameTaken = True
            number = ""
            while fileNameTaken:
                fileName = file_name_base + suffix + ext
                fileNameTaken = fileName in usedFileNames
                if not suffix:
                    number = 0
                number += 1
                suffix = "_" + str(number)
            usedFileNames.append(fileName)

            # f = open(os.path.join(os.path.dirname(input), fileName), "w+")
            # f.write('<?xml version="1.0"?>')
            # f.close()
            print("Add external Link to: {}\n    file: {}". format(song, os.path.join(os.path.dirname(input), fileName)))
            tixi.addExternalLink(song, os.path.join(os.path.dirname(input), fileName), "xml")

        #     tixi.addTextAttribute(song, "externalFileName", fileName)
        #     tixi.addTextAttribute(song, "externalDataDirectory", "file://./")
        #     tixi.addTextAttribute(song, "externalDataNodePath", tixi.parent(song))
        #
        #
        #
        # newTixi = Tixi()
        # newTixi.openString(tixi.exportDocumentAsString())
        outputFile = input.rsplit(".", 1)[0] + "_split.xml"
        tixi.saveCompleteDocument(outputFile)
        # print ("Saving to "+outputFile)
        # newTixi.saveCompleteDocument(outputFile)

    def getBasicSongInfo(self):
        # First remove the songs that have attribute include="false"
        xPathToRemove = "//song[@include='false']"
        for path in reversed(self.tixi.getPathsFromXPathExpression(xPathToRemove)):
            self.tixi.removeElement(path)

        xPath = "//song[@title]"
        n = self.tixi.tryXPathEvaluateNodeNumber(xPath)
        print("Found {} songs".format(n))
        if self.N > 0 and n < self.N or self.N == 0:
            self.N = n

        # Remove the abundant songs
        while self.tixi.tryXPathEvaluateNodeNumber(xPath) > self.N:
            path = self.tixi.xPathExpressionGetXPath(xPath, self.N + 1)
            self.tixi.removeElement(path)

        # Now remove sections that do not have songs inside
        xPath_emptySection = "//section[not(descendant::song)]"
        for path in reversed(self.tixi.getPathsFromXPathExpression(xPath_emptySection)):
            self.tixi.removeElement(path)

        print("Will process {} songs".format(self.N))

        usedFileNames = []
        xPath = "//*[self::song or self::section][@title]"

        for xmlPath in self.tixi.getPathsFromXPathExpression(xPath):
            if not self.tixi.checkElement(xmlPath):
                return False
            title = self.tixi.getTextAttribute(xmlPath, "title")

            if Tixi.elementName(xmlPath) == "song":
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

        # replace all single and double quotes in attributes with &apos; and &quot; , respectively
        for path in self.tixi.getPathsFromXPathExpression("//*[@*]"):
            # xpath expression means all elements that have any attributes
            for i in range(self.tixi.getNumberOfAttributes(path)):
                attr = self.tixi.getAttributeName(path, i + 1)
                value = self.tixi.getTextAttribute(path, attr)
                value1 = value.replace("'", "&apos;")
                value1 = value1.replace('"', "&quot;")
                if value == value1:
                    continue
                self.tixi.addTextAttribute(path, attr, value1)

    def write_indexes(self):
        writer = AuthorsWriter(self.tixi)
        writer.write_index()
        writer.saveFile(os.path.join(CFG.SONG_HTML_DIR, "idx_authors.xhtml"))

        writer = SongsIndexWriter(self.tixi)
        writer.write_index()
        writer.saveFile(os.path.join(CFG.SONG_HTML_DIR, "idx_songs.xhtml"))

    def write_songs(self):
        """
        Read the source file and for each song defined, write a properly formatted
        song xml file in the required location
        """

        xPath = "//song"
        for xml in self.tixi.getPathsFromXPathExpression(xPath):
            file = self.tixi.getTextAttribute(xml, "xhtml")

            writer = SongWriter(self.tixi, xml)
            writer.write_song_file(file)

    def write_sections(self):
        """
        Read the source file and for each section defined, write a properly formatted
        section xhtml file in the required location
        """

        xPath = "//section"
        for xml in self.tixi.getPathsFromXPathExpression(xPath):
            file = self.tixi.getTextAttribute(xml, "xhtml")

            writer = SectionWriter(self.tixi, xml)
            writer.write_section_file(file)

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
            n = self.tixi.tryXPathEvaluateNodeNumber(xPathFrom)
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
                m = self.tixi.tryXPathEvaluateNodeNumber(xPath)
                if m == 0:
                    linksToRemove.append(path_link)
                for j in range(1, m + 1):
                    target_path = self.tixi.xPathExpressionGetXPath(xPath, j)
                    # Do not create link, if there already is one
                    if self.tixi.tryXPathEvaluateNodeNumber(target_path + "/link[@title='{}']".format(title_parent)):
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

        xPath = "//*[self::song or self::section]"
        for i, xml in enumerate(self.tixi.getPathsFromXPathExpression(xPath)):
            fileName = self.tixi.getTextAttribute(xml, "xhtml")
            id = "id{}".format(i + 1)

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

        for path in self.tixi.getPathsFromXPathExpression(xPath):
            self._createNavPoint(path, my_npPath, tixi_ncx)
