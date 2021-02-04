# -*- coding: utf-8 -*-
"""
Created on 20.11.2020 18:35

@author: piotr
"""
import os

from config import EpubSongbookConfig
from tixi import Tixi, TixiException, ReturnCode
from .index_authors_writer import AuthorsWriter
from .index_songs_writer import SongsIndexWriter
from .section_writer import SectionWriter
from .song_writer import SongWriter
from .utf_simplifier import UtfSimplifier


class SongBookGenerator(object):
    def __init__(self, input_file, xsd_file=None, preprocess = True):
        """
        Master class aggregating all other tools
        :param input_file: input xml file.
        :param xsd_file: XSD schema file to validate the input_file and take default values.
        :param preprocess: run the preprocessing. True by default. Set to False in tests
        """
        self.tixi = Tixi()
        self.tixi.open(input_file, recursive=True)

        if xsd_file is not None:
            self.tixi.schemaValidateFromFile(xsd_file)

        self.tixi.registerNamespacesFromDocument()
        self.settings = EpubSongbookConfig(self.tixi, xsd_file)
        self.settings.defineOutputDir()
        self.settings.placeEssentialFiles()
        self.settings.setupAttributes()
        self.N = self.settings.maxsongs  # definitely a shorter notation

        self.id = None
        if preprocess:
            self._preprocess()

    #
    def _preprocess(self):
        self._removeIgnoredContent()

        self._findAmbiguousSongsContent()

        self._pullAttributesFromSRCs()

        self._assignXHTMLattributes()

        self._escapeQuoteMarks()

    def _removeIgnoredContent(self):
        """Remove elements that should not be taken into account while processing the data:
            -   those with attribute ignore="true"
            -   those that exceed the max number of songs to be processed
            -   sections that are empty after previous operations
        """
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

    def _findAmbiguousSongsContent(self):
        """Find song elements that have both "src" attribute and some children in the same tixi. If such elements
        are found, raise an error"""
        xPath = "//song[@src]/*"
        wrongPaths = dict()
        for path in self.tixi.getPathsFromXPathExpression(xPath):
            parent = Tixi.parent(path)
            if parent in wrongPaths:
                # No need to do the same for every verse/chorus/link etc.
                continue

            wrongPaths[parent] = self.tixi.getTextAttribute(parent, "title")
        message = "\n".join(["{} ({})".format(title, path) for path, title in wrongPaths.items()])
        if message:
            e = TixiException(ReturnCode.NOT_SCHEMA_COMPLIANT)
            e.error = "Ambiguous content!\nFollowing songs are defined both " \
                      "in master XML and in separate src files:\n{}".format(message)
            raise e

    def _pullAttributesFromSRCs(self):
        """
        Get all attributes from the separate song file to which path is provided in the src attributes of song elements
        and copy them to the elements. This allows for collecting all attributes in one element, and also for accessing
        the inherited attributes (like chord_mode) that can be defined higher in the XML tree.

        Moreover, check if songs in src files don't have different attributes than song elements in toplevel tixi
        and copy these attributes, because that is considered an unambiguity"""
        xPath = "//song[@src]"
        spath = "/song"
        missingFiles = dict()
        ambiguousAttributes = dict()
        for path in self.tixi.getPathsFromXPathExpression(xPath):
            src = self.tixi.getTextAttribute(path, "src")
            file = os.path.join(self.tixi.getDocumentPath(), src)
            if not os.path.isfile(file):
                missingFiles[path] = src
                continue
            tmp_tixi = Tixi()
            try:
                tmp_tixi.open(file)
            except TixiException:
                missingFiles[path] = src
                continue

            for attrName, attrValue in tmp_tixi.getAttributes(spath):
                if not self.tixi.checkAttribute(path, attrName):
                    self.tixi.addTextAttribute(path, attrName, attrValue)
                else:
                    myValue = self.tixi.getTextAttribute(path, attrName)
                    if attrValue != myValue:
                        ambiguousAttributes["{}, {}".format(path, attrName)] = [attrValue, myValue]

    def _assignXHTMLattributes(self):
        """For each song and section element, add an attribute that will describe what output xhtml file the given
        song or section should create. The file names are built by replacing spaces in title with underscores and
        simplifying the UTF characters to ASCII. If file name is already used, the the new will have an increased
        number appended
        """
        usedFileNames = []
        xPath = "//*[self::song or self::section][@title]"

        for xmlPath in self.tixi.getPathsFromXPathExpression(xPath):
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

    def _escapeQuoteMarks(self):
        """replace all single and double quotes in attributes with &apos; and &quot; , respectively"""
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

    #
    def write_indexes(self):
        writer = AuthorsWriter(self.tixi, self.settings)
        writer.write_index()
        writer.saveFile(os.path.join(self.settings.dir_out, "idx_authors.xhtml"))

        writer = SongsIndexWriter(self.tixi, self.settings)
        writer.write_index()
        writer.saveFile(os.path.join(self.settings.dir_out, "idx_songs.xhtml"))

    #
    def write_songs(self):
        """
        Read the source file and for each song defined, write a properly formatted
        song xml file in the required location
        """

        xPath = "//song"
        for xml in self.tixi.getPathsFromXPathExpression(xPath):
            file = self.tixi.getTextAttribute(xml, "xhtml")

            writer = SongWriter(self.tixi, self.settings, xml)
            writer.write_song_file(file)

    #
    def write_sections(self):
        """
        Read the source file and for each section defined, write a properly formatted
        section xhtml file in the required location
        """

        xPath = "//section"
        for xml in self.tixi.getPathsFromXPathExpression(xPath):
            file = self.tixi.getTextAttribute(xml, "xhtml")

            writer = SectionWriter(self.tixi, self.settings, xml)
            writer.write_section_file(file)

    #
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

    #
    def write_metadata(self):
        """Cleanup and rewrite the metadata.opf"""
        tixi = Tixi()
        opf = os.path.join(self.settings.dir_out, "metadata.opf")
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

        itemAttributes = [{"href": "toc.ncx", "id": "ncx", "media-type": "application/x-dtbncx+xml"},
                          {"href": "songbook.css", "id": "css", "media-type": "text/css"}]

        for i, d in enumerate(itemAttributes):
            tixi.createElementNS(manifest, "item", opfuri)
            path = manifest + "/opf:item[{}]".format(i + 1)
            for key, value in d.items():
                tixi.addTextAttribute(path, key, value)

        xPath = "//*[self::song or self::section]"
        for i, xml in enumerate(self.tixi.getPathsFromXPathExpression(xPath)):
            fileName = self.tixi.getTextAttribute(xml, "xhtml")
            id_attr = "id{}".format(i + 1)

            tixi.createElement(manifest, "item")
            n = tixi.getNamedChildrenCount(manifest, "item")
            path = manifest + "/item[{}]".format(n)

            file = os.path.join(os.path.basename(self.settings.dir_text), fileName).replace("\\", "/")
            tixi.addTextAttribute(path, "href", file)
            tixi.addTextAttribute(path, "id", id_attr)
            tixi.addTextAttribute(path, "media-type", "application/xhtml+xml")

            tixi.createElementNS(spine, "itemref", opfuri)
            n = tixi.getNamedChildrenCount(spine, "opf:itemref")
            path = spine + "/opf:itemref[{}]".format(n)
            tixi.addTextAttribute(path, "idref", id_attr)
        tixi.saveDocument(opf)

    #
    def write_toc(self):
        """Cleanup and rewrite the toc.ncx"""
        tixi = Tixi()
        toc = os.path.join(self.settings.dir_out, "toc.ncx")
        try:
            tixi.open(toc)
        except TixiException as e:
            if e.code != ReturnCode.OPEN_FAILED:
                raise e
            tixi = self._createEmptyToC()
        tixi.registerNamespacesFromDocument()
        uri = "http://www.daisy.org/z3986/2005/ncx/"
        tixi.registerNamespace(uri, "ncx")
        tixi.registerNamespace("http://www.w3.org/XML/", "xml")

        if tixi.checkElement("/ncx:ncx/ncx:navMap"):
            tixi.removeElement("/ncx:ncx/ncx:navMap")

        tixi.createElement("/ncx", "navMap")
        navMap = "/ncx/navMap"

        assert tixi.checkElement(navMap)

        self.id = 1
        self._createNavPoint("/songbook", navMap, tixi)

        tixi.saveDocument(toc)

    #
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

    #
    def _createEmptyToC(self):
        """Create the empty template for the toc.ncx"""
        tixi = Tixi()
        uri = "http://www.daisy.org/z3986/2005/ncx/"
        tixi.create("ncx")
        tixi.addTextAttribute("/ncx", "xmlns", uri)
        tixi.addTextAttribute("/ncx", "version", "2005-1")
        tixi.addTextAttribute("/ncx", "xml:lang", self.settings.lang)

        tixi.createElement("/ncx", "head"),
        tpath = tixi.getNewElementPath("/ncx", "docTitle")
        tixi.addTextElement(tpath, "text", self.settings.title)
        return tixi
