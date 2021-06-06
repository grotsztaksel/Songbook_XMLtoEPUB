# -*- coding: utf-8 -*-
"""
Created on Sat Nov 14 17:56:39 2020

@author: Piotr Gradkowski <grotsztaksel@o2.pl>
"""

__authors__ = ['Piotr Gradkowski <grotsztaksel@o2.pl>']
__date__ = '2020-11-14'
__all__ = ['LineWithChords', 'SongWriter']

import os
from collections import namedtuple

from scripts.config import EpubSongbookConfig, ChordMode
from scripts.tixi import Tixi, TixiException, ReturnCode
from .html_writer import HtmlWriter
from .general import escapeQuoteMarks, getDefaultSongAttributes

LineWithChords = namedtuple("LineWithChords", ["text", "chords"])


class SongWriter(HtmlWriter):
    def __init__(self, tixi: Tixi, settings: EpubSongbookConfig, path: str):
        super(SongWriter, self).__init__(tixi, settings)

        self.src_path = path
        if self.src_tixi.checkAttribute(self.src_path, "src"):
            songFilePath = os.path.join(os.path.dirname(self.src_tixi.getDocumentPath()),
                                        self.src_tixi.getTextAttribute(self.src_path, "src"))
            assert os.path.isfile(songFilePath)
            self.song_tixi = Tixi()
            self.song_tixi.open(songFilePath)
            escapeQuoteMarks(self.song_tixi)
            self.song_path = "/song"
            try:
                self.song_tixi.schemaValidateWithDefaultsFromFile(self.settings.xsd_song)
            except TixiException as e:
                e.error += " in file {}".format(songFilePath)
                raise e

        else:
            self.song_tixi = self.src_tixi
            self.song_path = self.src_path

        self.CS = self.settings.CS
        self.CI = self.settings.CI

        result = self._compareAttributes()
        if result.code != ReturnCode.SUCCESS:
            raise result

        self.mode = ChordMode.get(self.src_tixi.getInheritedTextAttribute(path, "chord_mode"))

    #
    def write_song_file(self, fileName) -> bool:
        """
        Read the xml node in song_path and write a valid HTML file out of it in the desired location
        """
        title = self.src_tixi.getTextAttribute(self.src_path, "title")
        print("Saving song: {}\n  -- to file {}".format(title, fileName))

        self.write_song_header(title)

        xpath = self.song_path + "/*[self::verse or self::chorus]"
        nparts = self.song_tixi.xPathEvaluateNodeNumber(xpath)
        for i in range(1, nparts + 1):
            path = self.song_tixi.xPathExpressionGetXPath(xpath, i)
            self.write_song_part(path)

        self.write_links()

        self.saveFile(os.path.join(self.settings.dir_text, fileName))

    #
    def write_song_header(self, title):
        band = ""
        lyrics = ""
        music = ""
        for tixi, path in zip([self.src_tixi, self.song_tixi], [self.src_path, self.song_path]):
            if band == "" and tixi.checkAttribute(path, "band"):
                band = tixi.getTextAttribute(path, "band")
            if lyrics == "" and tixi.checkAttribute(path, "lyrics"):
                lyrics = tixi.getTextAttribute(path, "lyrics")
            if music == "" and tixi.checkAttribute(path, "music"):
                music = tixi.getTextAttribute(path, "music")
        defaultValues = getDefaultSongAttributes(self.settings.xsd_song)

        definedBand = (bool(band) and band != defaultValues["band"]) \
            if "band" in defaultValues else bool(band)
        definedLyrics = (bool(lyrics) and lyrics != defaultValues["lyrics"]) \
            if "lyrics" in defaultValues else bool(lyrics)
        definedMusic = (bool(music) and music != defaultValues["music"]) \
            if "music" in defaultValues else bool(music)

        if definedBand and not definedLyrics and not definedMusic:
            text = band
        else:
            if not definedLyrics:
                lyrics = self.settings.unknown_author
            if not definedMusic:
                music = self.settings.unknown_author

            text = "{} {}, {} {}".format(self.settings.lyrics_string, lyrics,
                                         self.settings.music_string, music)

            if definedBand:
                text += " ({})".format(band)

        # <body/>
        self.tixi.createElement(self.root, "body")
        bpath = self.root + "/body"

        # <h1>[title]</h1>
        self.tixi.addTextElement(bpath, "h1", title)

        # <p class="authors">lyrics by: [lyrics], music by: [music] (The Developers)</p>
        pPath = self.tixi.addTextElement(bpath, "p", text)
        self.tixi.addTextAttribute(pPath, "class", "authors")

    #
    def write_song_part(self, srcPath):
        """Write either a verse or chorus of the song, applying the expected formatting"""
        # voc stands for Verse Or Chorus
        voc = srcPath.split("/")[-1]  # Extract the last element in path
        voc = voc.split("[")[0]  # Get rid of the index, if there is one

        mode = ChordMode.get(self.song_tixi.getInheritedTextAttribute(srcPath, "chord_mode"))
        path = self.root + "/body"
        self.format_song_part(srcPath, path, mode)
        n = self.tixi.getNamedChildrenCount(self.root + "/body", "p")
        path = "{}/p[{}]".format(path, n)
        self.tixi.addTextAttribute(path, "class", voc)

    #
    def format_song_part(self, srcPath, targetPath, mode=None):
        """
        Basing on the global settings, read the content of the verse/chorus 
        from the source and apply a format according to the mode:
        ChordMode.CHORD_ABOVE - the chords will be written above the text, indicating the place, where the chord should be played
                               This will be achieved by placing the fragmented words and chords in a table.
        ChordMode.CHORD_BESIDE - the chords will be listed to the right of the line
                               This will be achieved by placing the whole verse/chorus in a two-column table, 
                               with the 1st column containing the text, and the 2nd containing the chords
        ChordMode.NO_CHORD - the chords will not be written at all. The text will be as a whole, replacing newline characters with newline markers
            
        """

        if mode is None:
            mode = ChordMode.CHORDS_ABOVE

        if mode == ChordMode.CHORDS_ABOVE:
            if not self.write_chords_above(srcPath, targetPath):
                # Input data was invalid for chords-above formatting
                mode = ChordMode.CHORDS_BESIDE

        if mode == ChordMode.CHORDS_BESIDE:
            if not self.write_chords_beside(srcPath, targetPath):
                # Input data was invalid for chords-beside formatting
                mode = ChordMode.NO_CHORDS

        if mode == ChordMode.NO_CHORDS:
            self.write_without_chords(srcPath, targetPath)

    #
    def write_chords_above(self, srcPath, targetPath):
        """
        In this format, the <p/> element contains N <table/> elements, where
        N is the number of lines. Every table has two rows: one for the chords above,
        one for the line of text
        """
        text = self.song_tixi.getTextElement(srcPath).strip()
        if not self.CS in text:
            return False

        pPath = self.tixi.createElement(targetPath, "p")
        for line in self._identifyLinesWithChords(text):
            if isinstance(line, list):
                while line:
                    l = line.pop(0)
                    self.tixi.addTextElement(pPath, "span", l)
                    if line:
                        self.tixi.createElement(pPath, "br")
            elif isinstance(line, LineWithChords):
                tbPath = self.tixi.createElement(pPath, "table")

                # with the empty element [''] in front, the chords should have the same length as the textChunks
                chords = [''] + line.chords[0].split(" ")
                textChunks = line.text.split(self.CI)

                self.tixi.createElement(tbPath, "tr")
                self.tixi.createElement(tbPath, "tr")
                crdPath = "{}/tr[1]".format(tbPath)
                txtPath = "{}/tr[2]".format(tbPath)
                self.tixi.addTextAttribute(crdPath, "class", "chords_above")

                while chords or textChunks:
                    if not chords:
                        # Run out of chords. Ignore the rest of the self.CI characters.
                        chunk = "".join(textChunks)
                        lastChunk = self.tixi.getTextElement(lastText_td)
                        if lastChunk.endswith("&#xA0;"):
                            lastChunk = lastChunk[:-6] + " "
                        self.tixi.updateTextElement(lastText_td, lastChunk + chunk)
                        break
                    elif not textChunks:
                        # Run out of self.CI characters. Just add the remaining chords at the end of the line
                        chunk = ""
                        chord = " ".join(chords)
                        textChunks = False
                        chords = False
                    else:
                        chord = chords.pop(0)
                        chunk = textChunks.pop(0)
                        if chunk.endswith(" "):
                            chunk = chunk[:-1] + "&#xA0;"
                    if chord:
                        self.tixi.addTextElement(crdPath, "td", chord)
                    else:
                        self.tixi.createElement(crdPath, "td")
                    if chunk:
                        lastText_td = self.tixi.addTextElement(txtPath, "td", chunk)
                    else:
                        lastText_td = self.tixi.createElement(txtPath, "td")

        return True

    #
    def write_chords_beside(self, srcPath, targetPath):
        """
        In this format, the <p/> element contains one <table/> element, where
        every row has two columns: one for the line of text, the other for chords
        """
        text = self.song_tixi.getTextElement(srcPath).strip()
        if not self.CS in text:
            return False

        pPath = self.tixi.createElement(targetPath, "p")

        previousWasTable = False
        for line in self._identifyLinesWithChords(text):
            if isinstance(line, list):
                while line:
                    l = line.pop(0)
                    self.tixi.addTextElement(pPath, "span", l)
                    if line:
                        self.tixi.createElement(pPath, "br")
                previousWasTable = False
            elif isinstance(line, LineWithChords):
                if not previousWasTable:
                    tbPath = self.tixi.createElement(pPath, "table")
                previousWasTable = True
                self.tixi.addTextAttribute(tbPath, "class", "chords_beside")

                trPath = self.tixi.createElement(tbPath, "tr")
                self.tixi.addTextElement(trPath, "td", line[0].replace(self.CI, ""))
                try:
                    self.tixi.addTextElement(trPath, "td", line[1][0])
                    self.tixi.addTextAttribute(trPath + "/td[2]", "class", "chords")
                except IndexError:
                    pass

        return True

    #
    def write_without_chords(self, srcPath, targetPath):
        """
        Get rid of all chord markers and ignore the presence of chords. 
        Write the whole part as a single text element, replacing the newlines
        with newline HTML markers
        """

        text = self.song_tixi.getTextElement(srcPath).strip()
        lines = [line.strip().split(self.CS)[0].replace(self.CI, "") for line in text.split('\n')]
        pPath = self.tixi.createElement(self.root + "/body", "p")
        while lines:
            line = lines.pop(0)
            self.tixi.addTextElement(pPath, "span", line)
            if lines:
                self.tixi.createElement(pPath, "br")
        return True

    #
    def write_links(self):
        """If the song contains <link> elements, find all other songs that have the same title as mentioned in the link
            and create approptiate <a href=...> elements
        """
        xPath = self.src_path + "/link[@title]"
        titles_found = []
        targetPath = "/html/body"
        linkPcreated = bool(self.tixi.xPathEvaluateNodeNumber(targetPath + "/p[@class='links']"))
        for path in self.src_tixi.xPathExpressionGetAllXPaths(xPath):
            if not linkPcreated:
                # Create the new paragraph to store the links

                #  <h3>See also</h3>
                self.tixi.addTextElement(targetPath, "h3", self.settings.links_header)

                #  <p class="links/>
                targetPath = self.tixi.createElement(targetPath, "p")
                self.tixi.addTextAttribute(targetPath, "class", "links")

                #  <p class="links>
                #    <ul/>
                #  </p>
                targetPath = self.tixi.createElement(targetPath, "ul")
                linkPcreated = True

            title = self.src_tixi.getTextAttribute(path, "title")
            if title in titles_found:
                # Don't want to repeat if the links have already been created for this title
                continue
            titles_found.append(title)

            # Find all songs that have this linked title - each will create a separate
            # <li><a href="...xhtml">Title</a><span> (authors)</span></li> item
            #
            xPath = "//song[@title='{}' and @xhtml]".format(title)
            for songPath in self.src_tixi.xPathExpressionGetAllXPaths(xPath):
                if songPath == self.src_path:
                    # Don't want to create link for ourselves
                    continue

                file = self.src_tixi.getTextAttribute(songPath, "xhtml")
                title = self.src_tixi.getTextAttribute(songPath, "title")

                authors = []
                for attr in ["lyrics", "music"]:
                    if self.src_tixi.checkAttribute(songPath, attr):
                        author = self.src_tixi.getTextAttribute(songPath, attr)
                        if author not in authors:
                            authors.append(author)

                #  <p class="links>
                #    <ul>
                #        <li/>
                #    </ul>
                #  </p>
                liPath = self.tixi.createElement(targetPath, "li")

                #  <p class="links>
                #    <ul>
                #        <li><a href="...xhtml">Linked song title</a>                                  </li>
                #    </ul>
                #  </p>
                aPath = self.tixi.addTextElement(liPath, "a", title)
                self.tixi.addTextAttribute(aPath, "href", file)

                #  <p class="links>
                #    <ul>
                #        <li><a href="...xhtml">Linked song title</a><span style="..."> (authors)</span> </li>
                #    </ul>
                #  </p>
                if authors:
                    authors = "({})".format(", ".join(authors))
                    sPath = self.tixi.addTextElement(liPath, "span", authors)
                    self.tixi.addTextAttribute(sPath, "style", "font-size:12px")

    #
    def _identifyLinesWithChords(self, text: str) -> list:
        """
        Split the text on newlines and return a list of items.
        If a line contains chords, return it as namedtuple LineWithChords
        Otherwise, merge all neighboring lines that do not have chords.
        :param text: input text
        :return: list of LineWithChords and/or plain string elements
        """
        output = list()
        lines = [line.strip() for line in text.split("\n")]
        noChordLines = None

        for line in lines:
            chords = [[s.strip()] for s in line.split(self.CS)]
            text = chords.pop(0)[0]
            if not chords:
                if noChordLines is None:
                    noChordLines = [text]
                else:
                    noChordLines.append(text)
            else:
                if noChordLines is not None:
                    # Append the chunk of text to the output and reset the noChordLines collector
                    output.append(noChordLines)
                    noChordLines = None
                output.append(LineWithChords(text, chords[0]))

        if noChordLines is not None:
            # Append the chunk of text to the output and reset the noChordLines collector
            output.append(noChordLines)

        return output

    def _compareAttributes(self) -> TixiException:
        """
        If the song is written in a separate tixi than the src_tixi, make sure that none of the attributes in the
        source path and song path has different value. If the attributes do not repeat, everything is fine.
        :return: TixiException. If attributes are not contradicting, returns with code SUCCESS. Otherwise with code
                 NOT_SCHEMA_COMPLAINT
        """
        nonMatchingAttributes = dict()
        e = TixiException(ReturnCode.SUCCESS)

        for i in range(1, self.src_tixi.getNumberOfAttributes(self.src_path) + 1):
            attrName = self.src_tixi.getAttributeName(self.src_path, i)
            if self.song_tixi.checkAttribute(self.song_path, attrName):
                src_attribute_value = self.src_tixi.getTextAttribute(self.src_path, attrName)
                sng_attribute_value = self.song_tixi.getTextAttribute(self.song_path, attrName)
                if sng_attribute_value != src_attribute_value:
                    nonMatchingAttributes[attrName] = [src_attribute_value, sng_attribute_value]
        if nonMatchingAttributes:
            attrs = ['{}: "{}"'.format(attr, '" vs "'.join(nonMatchingAttributes[attr])) for attr in
                     nonMatchingAttributes.keys()]

            e = TixiException(ReturnCode.NOT_SCHEMA_COMPLIANT)
            e.error = "Containing XML and Song XML <song> element has incoherent attributes:\n{}".format(
                "\n".join(attrs))
        return e
