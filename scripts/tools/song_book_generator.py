# -*- coding: utf-8 -*-
"""
Created on 20.11.2020 18:35

@author: Piotr Gradkowski <grotsztaksel@o2.pl>
"""

__authors__ = ['Piotr Gradkowski <grotsztaksel@o2.pl>']
__date__ = '2020-11-20'
__all__ = ['SongBookGenerator']

import os
import re
import shutil
import logging

from scripts.config import EpubSongbookConfig
from scripts.tixi import Tixi, TixiException, ReturnCode
from .index_authors_writer import AuthorsWriter
from .index_songs_writer import SongsIndexWriter
from .section_writer import SectionWriter
from .song_writer import SongWriter
from .utf_utils import UtfUtils
from .general import escapeQuoteMarks, getDefaultSongAttributes


class SongBookGenerator(object):
    def __init__(self, input_file, xsd_file=None, preprocess=True):
        """
        Master class aggregating all other tools
        :param input_file: input xml file.
        :param xsd_file: XSD schema file to validate the input_file and take default values.
        :param preprocess: run the preprocessing. True by default. Set to False in tests
        """
        self.tixi = Tixi()
        self.tixi.open(input_file, recursive=True)

        if xsd_file is not None:
            self.tixi.schemaValidateWithDefaultsFromFile(xsd_file)

        self.tixi.registerNamespacesFromDocument()
        self.settings = EpubSongbookConfig(self.tixi)
        self.settings.defineOutputDir()
        self.settings.placeEssentialFiles()
        self.settings.setupAttributes()
        self.N = self.settings.maxsongs  # definitely a shorter notation

        self.id = None

        # Hardwired names of index files.
        self.indexes = {"index_of_authors": "idx_authors.xhtml",
                        "index_of_songs": "idx_songs.xhtml"}
        if preprocess:
            self._preprocess()

    #
    def _preprocess(self):
        self._removeIgnoredContent()
        success = True
        success &= self._findAmbiguousSongsContent()
        success &= self._pullAttributesFromSRCs()

        for path in self.tixi.xPathExpressionGetAllXPaths("//html"):
            success &= self.setHTMLtitle(path)

        success &= self._assignXHTMLattributes()

        if not success:
            raise RuntimeError

        self._exposeLinks()

        escapeQuoteMarks(self.tixi)

        self.createTwoWayLinks()

    def _removeIgnoredContent(self, tixi: Tixi = None):
        """Remove elements that should not be taken into account while processing the data:
            -   those with attribute ignore="true"
            -   those that exceed the max number of songs to be processed
            -   sections that are empty after previous operations
        """
        if tixi is None:
            tixi = self.tixi

        # First remove the items that have attribute include="false"
        xPathToRemove = "//*[@include='false']"
        for path in reversed(tixi.xPathExpressionGetAllXPaths(xPathToRemove)):
            # reversed order, in order to prevent modification of the paths of elements that are not yet deleted
            tixi.removeElement(path)
        xPath = "//song[@title]"
        n = tixi.xPathEvaluateNodeNumber(xPath)
        logging.info("Found {} songs".format(n))
        if self.N > 0 and n < self.N or self.N == 0:
            self.N = n
        # Remove the abundant songs
        while tixi.xPathEvaluateNodeNumber(xPath) > self.N:
            path = tixi.xPathExpressionGetXPath(xPath, self.N + 1)
            logging.info("Max song number set to {}. Ignoring {}".format(self.N, path))
            tixi.removeElement(path)
        # Now remove sections that do not have songs inside
        xPath_emptySection = "//section[not(descendant::song)]"
        for path in reversed(tixi.xPathExpressionGetAllXPaths(xPath_emptySection)):
            logging.info(f"Ignoring empty section {path}")
            tixi.removeElement(path)

    def _findAmbiguousSongsContent(self):
        """Find song elements that have both "src" attribute and some children in the master XML. If such elements
        are found, raise an error"""
        xPath = "//song[@src]/*[not (self::link)]"
        wrongPaths = dict()
        for path in self.tixi.xPathExpressionGetAllXPaths(xPath):
            parent = Tixi.parent(path)
            if parent in wrongPaths:
                # No need to do the same for every verse/chorus/link etc.
                continue
            title = self.tixi.getTextAttribute(parent, "title")
            logging.error("{} is defined in both master XML and a source file ({})".format(title, path))
            wrongPaths[parent] = title
        return not wrongPaths

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
        defaultAttributes = getDefaultSongAttributes(self.settings.xsd_song)

        unv_tixi = Tixi()  # since the main tixi has been validated with defaults, a raw copy without default attribute
        # values is needed...
        unv_tixi.open(self.tixi.getDocumentPath())
        # Raw, but without ignored content, to avoid non-unique paths while resolving xPath Expressions
        self._removeIgnoredContent(unv_tixi)
        success = True

        for path in self.tixi.xPathExpressionGetAllXPaths(xPath):
            src = self.tixi.getTextAttribute(path, "src")
            if os.path.isfile(os.path.abspath(src)):
                file = src
            else:
                file = os.path.join(os.path.dirname(self.tixi.getDocumentPath()), src)
            if not os.path.isfile(file):
                logging.error(f"Source file {src} not found ({path})")
                success = False
                continue
            tmp_tixi = Tixi()
            try:
                tmp_tixi.open(file)
            except TixiException:
                missingFiles[path] = src
                continue

            for attrName, attrValue in tmp_tixi.getAttributes(spath).items():
                if not self.tixi.checkAttribute(path, attrName):
                    self.tixi.addTextAttribute(path, attrName, attrValue)
                else:
                    myValue = self.tixi.getTextAttribute(path, attrName)

                    if attrValue != myValue:
                        if attrName in defaultAttributes.keys() and not unv_tixi.checkAttribute(path, attrName):
                            # This was a default value added while schema validating
                            self.tixi.addTextAttribute(path, attrName, attrValue)
                        else:
                            logging.error(
                                f"Ambiguous attribute values for {path}/@{attrName}: '{attrValue}' vs '{myValue}'")
                            success = False

        return success

    def _assignXHTMLattributes(self):
        """For each song and section element, add an attribute that will describe what output xhtml file the given
        song or section should create. Apart from that, the html documents will not be renamed, because they may be
        referenced to in other documents.
        For the same reason, if the master XML file already has "xhtml" attribute for the given song or section,
        it will be then used.
        The file names are built by replacing spaces in title with underscores and
        simplifying the UTF characters to ASCII. If file name is already used, the the new will have an increased
        number appended
        """
        usedFileNames = []
        success = True

        XhtmlNamesAbused = False
        usedXhtmlNames = {}  # If more than one song or section has the same xhtml attribute, collect them and throw an
        #                      error

        xPath = "//*[self::index_of_songs or self::index_of_authors]"

        for xmlPath in self.tixi.xPathExpressionGetAllXPaths(xPath):
            name = Tixi.elementName(xmlPath)
            self.tixi.addTextAttribute(xmlPath, "xhtml", self.indexes[name])

        xPath = "//html"
        for xmlPath in self.tixi.xPathExpressionGetAllXPaths(xPath):
            # Simply copy the "src" attribute to "xhtml"
            src = self.tixi.getTextAttribute(xmlPath, "src")
            self.tixi.addTextAttribute(xmlPath, "xhtml", src)

        xPath = "//*[self::song or self::section]"

        for xmlPath in self.tixi.xPathExpressionGetAllXPaths(xPath):
            title = self.tixi.getTextAttribute(xmlPath, "title")
            if self.tixi.checkAttribute(xmlPath, "xhtml"):
                xhtml = self.tixi.getTextAttribute(xmlPath, "xhtml")
                if xhtml not in usedXhtmlNames.keys():
                    usedXhtmlNames[xhtml] = [xmlPath]
                else:
                    usedXhtmlNames[xhtml].append(xmlPath)
                    success = False

            if Tixi.elementName(xmlPath) == "song":
                prefix = "sng_"
            elif Tixi.elementName(xmlPath) == "section":
                prefix = "sec_"
            else:
                prefix = "htm_"

            file_name_base = UtfUtils.toAscii(title).replace(" ", "_").lower()
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
        if not success:
            for xhtml_name, xmlPaths in usedXhtmlNames.items():
                if len(xmlPaths) > 1:
                    for xmlPath in xmlPaths:
                        logging.error(f"Output HTML name {xhtml_name} used more than once: f{xmlPath}")

        return success

    def _exposeLinks(self):
        """
        For all songs defined in separate files, copy their <link> children to the master XML so that it is
        visible to all song writers
        """
        # First, check if the songs written in separate files have links
        xPathSrc = "//song[@src]"

        for song_path in self.tixi.xPathExpressionGetAllXPaths(xPathSrc):
            source_file = self.tixi.getTextAttribute(song_path, "src")

            song_tixi = Tixi()
            song_tixi.open(os.path.join(os.path.dirname(self.tixi.getDocumentPath()), source_file))
            song_title = song_tixi.getTextAttribute("/song", "title")
            for link_path in song_tixi.xPathExpressionGetAllXPaths("/song/link"):
                try:
                    link_title = song_tixi.getTextAttribute(link_path, "title")
                except TixiException as e:
                    e.error += " at path {}".format(song_path)
                    raise e
                if not self.tixi.checkElement('{}/link[@title="{}"]'.format(song_path, link_title)):
                    new_link = self.tixi.createElement(song_path, "link")
                    self.tixi.addTextAttribute(new_link, "title", link_title)

                # Make sure, that the paired song also has a link to myself
                for paired_link in self.tixi.xPathExpressionGetAllXPaths(
                        '//song[@title="{}"]'.format(link_title)):
                    if not self.tixi.checkElement('{}/link[@title="{}"]'.format(paired_link, song_title)):
                        new_olink = self.tixi.createElement(paired_link, "link")
                        self.tixi.addTextAttribute(new_olink, "title", song_title)

    #
    def write_indexes(self):
        writer = AuthorsWriter(self.tixi, self.settings)
        writer.write_index()
        writer.saveFile(os.path.join(self.settings.dir_text, "idx_authors.xhtml"))

        writer = SongsIndexWriter(self.tixi, self.settings)
        writer.write_index()
        writer.saveFile(os.path.join(self.settings.dir_text, "idx_songs.xhtml"))

    #
    def write_songs(self):
        """
        Read the source file and for each song defined, write a properly formatted
        song xml file in the required location
        """

        xPath = "//song"
        for xml in self.tixi.xPathExpressionGetAllXPaths(xPath):
            file = self.tixi.getTextAttribute(xml, "xhtml")

            writer = SongWriter(self.tixi, self.settings, xml)
            writer.write_song_file(file)

    def setHTMLtitle(self, xmlPath: str) -> str:
        """Get the title of a html document that should also be included in the songbook and place it in the attribute
        "title" of XML element at xmlPath.
        If the document is not a HTML,
        The title is extracted from the /html/header/title of the source document.
        If the XML element at xmlPath already contains attribute "title", it must be identical as the one in the html.

        :param xmlPath: Path to the XML configuration element "html"
        :return: error string. If empty, title attribute was set successfully or unchanged
        """

        if self.tixi.checkAttribute(xmlPath, "title"):
            title = self.tixi.getTextAttribute(xmlPath, "title")
        else:
            title = ""

        src = self.tixi.getTextAttribute(xmlPath, "src")
        if os.path.isabs(src) and os.path.isfile(os.path.abspath(src)):
            htmlFile = src
        elif os.path.isfile(os.path.join(os.path.dirname(self.tixi.getDocumentPath()), src)):
            htmlFile = os.path.join(os.path.dirname(self.tixi.getDocumentPath()), src)
        else:
            logging.error('- {} {} src="{}" - file not found!'.format(xmlPath, title, src))
            return False

        htixi = Tixi()
        try:
            htixi.open(htmlFile)
        except TixiException as e:
            logging.error('- {} {} src="{}" - source is not a valid HTML file!'.format(xmlPath, title, src))
            return False

        # get rid of all namespaces defined in the html - but just for tixi needs. Do not save it!
        html_str = htixi.exportDocumentAsString()
        htixi.close()
        htixi.openString(re.sub(r"xmlns(:\S+)?=['\"].+?['\"]", "", html_str))

        if htixi.checkElement("/html/head/title"):
            htitle = htixi.getTextElement("/html/head/title")
        else:
            logging.error('- {} - undefined document title in {}!'.format(xmlPath, src))
            return False

        if not title:
            self.tixi.addTextAttribute(xmlPath, "title", htitle)
            title = htitle

        if htitle != title:
            logging.error('- {} - title mismatch! ("{}" vs "{}" in {})'.format(xmlPath, title, htitle, src))
            return False

        return self._copyHTML_resources(htixi, htmlFile)

    def _copyHTML_resources(self, tixi: Tixi, html_path=None) -> str:
        """
        Check if the subdocument HTML file uses some resources and verify their availability. If the resource file is
        available, copy it to the output directory keeping the relative path


        REMARK: Only relative paths are supported, as the HTML files are copied to the output directory, and so will
        be their resource files

        REMARK: Only images, html links and stylesheets are checked as of now
        :param tixi: an opened Tixi object containing the html subdocument definition
        :param html_path: path to the source file. If None, the method will try getting it from the Tixi object, which
                          will fail, if the Tixi was created from a string
        :return:  Empty string if everything is fine. Otherwise string containing the error information
        """
        success = True
        if html_path is None:
            html_path = tixi.getDocumentPath()
        css = tixi.xPathExpressionGetAllXPaths("//link[@rel='stylesheet' and @href]")
        images = tixi.xPathExpressionGetAllXPaths("//img[@src]")
        links = tixi.xPathExpressionGetAllXPaths("//a[@href]")
        for path in css + images + links:
            if path in css + links:
                src_attr = "href"
            elif path in images:
                src_attr = "src"
            src = tixi.getTextAttribute(path, src_attr)
            file = os.path.normpath(os.path.join(os.path.dirname(html_path), src))
            filename = os.path.split(file)[1]
            if not os.path.isfile(file):
                logging.error("Resource file {} not found".format(src))
                success = False
                continue

            # Seems like the file exists. Copy it to the destination output directory, keeping the relative location
            target_dir = os.path.normpath(os.path.join(self.settings.dir_text, os.path.dirname(src)))
            os.makedirs(target_dir, exist_ok=True)
            target_file = os.path.join(target_dir, filename)
            try:
                shutil.copy(file, target_file)
            except shutil.SameFileError:
                pass
            except PermissionError:
                logging.error("Could not copy {} to {} - Permission denied".format(file, target_file))
                success = False
            except:
                logging.error("Could not copy {} to {}".format(file, target_file))
                success = False
        return success

    #
    def write_sections(self):
        """
        Read the source file and for each section defined, write a properly formatted
        section xhtml file in the required location
        """

        xPath = "//section"
        for xml in self.tixi.xPathExpressionGetAllXPaths(xPath):
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
            n = self.tixi.xPathEvaluateNodeNumber(xPathFrom)
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
                m = self.tixi.xPathEvaluateNodeNumber(xPath)
                if m == 0:
                    # The indexing in the path_link may change after the new links are created.
                    # It is safer to replace the element index
                    # (e.g. [3]) with linked title (e.g. [@title='Dead link song']
                    # Using regex, because there may be no index at the end
                    path_link = re.sub('\[\d+\]$', '', path_link)
                    linksToRemove.append("{}[@title='{}']".format(path_link, title_link))

                for j in range(1, m + 1):
                    target_path = self.tixi.xPathExpressionGetXPath(xPath, j)
                    # Do not create link, if there already is one
                    if self.tixi.xPathEvaluateNodeNumber(target_path + "/link[@title='{}']".format(title_parent)):
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

        xPath = "//*[self::song " \
                "or self::section " \
                "or self::html " \
                "or self::index_of_authors " \
                "or self::index_of_songs]"

        for i, xml in enumerate(self.tixi.xPathExpressionGetAllXPaths(xPath)):
            fileName = os.path.normpath(self.tixi.getTextAttribute(xml, "xhtml"))
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
        toc_exists = os.path.isfile(toc)
        if toc_exists:
            try:
                tixi.open(toc)
            except TixiException as e:
                if e.code != ReturnCode.OPEN_FAILED:
                    raise e
                toc_exists = False
        if not toc_exists:
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
            secsongFile = os.path.normpath(self.tixi.getTextAttribute(secsongPath, "xhtml"))
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

        xPath = "{}/*[self::song " \
                "or self::section " \
                "or self::html " \
                "or self::index_of_authors " \
                "or self::index_of_songs]".format(secsongPath)

        for path in self.tixi.xPathExpressionGetAllXPaths(xPath):
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
        tpath = tixi.createElement("/ncx", "docTitle")
        tixi.addTextElement(tpath, "text", self.settings.title)
        return tixi
