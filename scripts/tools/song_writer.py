# -*- coding: utf-8 -*-
"""
Created on Sat Nov 14 17:56:39 2020

@author: piotr
"""
__all__ = ['LineWithChords', 'SongWriter']

import os
import re
from collections import namedtuple

from config import CFG, ChordMode
from tixi import Tixi

LineWithChords = namedtuple("LineWithChords", ["text", "chords"])


class SongWriter():
    def __init__(self, tixi: Tixi, path: str, settings=None):
        super(SongWriter, self).__init__()
        self.settings = settings
        self.src_tixi = tixi
        self.src_path = path
        self.dir = CFG.SONG_HTML_DIR

        self.root = "html"

        self.tixi = Tixi()

        self.tixi.create(self.root)
        self.tixi.registerNamespace("http://www.w3.org/2001/XMLSchema-instance", 'xsd')

        self.root = "/" + self.root

    def write_song_file(self, fileName) -> bool:
        """
        Read the xml node in song_path and write a valid HTML file out of it in the desired location
        """
        title = self.src_tixi.getTextAttribute(self.src_path, "title")
        print("Saving song: {}\n  -- to file {}".format(title, fileName))

        self.write_html_header()
        self.write_song_header(title)

        xpath = self.src_path + "/*[self::verse or self::chorus]"
        nparts = self.src_tixi.xPathEvaluateNodeNumber(xpath)
        for i in range(1, nparts + 1):
            path = self.src_tixi.xPathExpressionGetXPath(xpath, i)
            self.write_song_part(path)

        self.write_links()

        self.saveFile(fileName)

    def saveFile(self, fileName):
        """Apply specific formatting andf save the content of the self.tixi to a file filename"""
        text = self.tixi.exportDocumentAsString()
        replaceRules = {
            "&lt;br/&gt;": "<br/>",
            "&amp;nbsp;": "&nbsp;"
        }
        for rr in replaceRules.keys():
            text = text.replace(rr, replaceRules[rr])
        # Now regular expressions

        # fold the table rows <tr><td></td></tr>into a single line
        text = re.sub(r"(<\/?t[dr].*?>)\s*(<\/?t[dr])", r"\1\2", text)

        file = open(os.path.join(CFG.SONG_HTML_DIR, fileName), "w", encoding='utf8')
        file.write(text)
        file.close()

    def write_html_header(self):
        self.tixi.createElement(self.root, "head")
        headPath = self.root + "/head"

        self.tixi.addTextElement(headPath, "title", "Śpiewnik")
        self.tixi.createElement(headPath, "link")

        linkPath = headPath + "/link"

        attrs = {"rel": "stylesheet",
                 "type": "text/css",
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
        self.tixi.addTextElement(bpath, "h1", title)

        # <p class="authors">sł. [lyrics], muz. [music]</p>
        self.tixi.addTextElement(bpath, "p",
                                 "sł. {}, muz. {}".format(lyrics, music))
        self.tixi.addTextAttribute(bpath + "/p", "class", "authors")

    def write_song_part(self, srcPath):
        # vop stands for Verse Or Chorus
        voc = srcPath.split("/")[-1]  # Extract the last element in path
        voc = voc.split("[")[0]  # Get rid of the index, if there is one

        path = self.root + "/body"
        self.format_song_part(srcPath, path, CFG.MODE)
        n = self.tixi.getNamedChildrenCount(self.root + "/body", "p")
        path = "{}/p[{}]".format(path, n)
        self.tixi.addTextAttribute(path, "class", voc)

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

    def write_chords_above(self, srcPath, targetPath):
        """
        In this format, the <p/> element contains N <table/> elements, where
        N is the number of lines. Every table has two rows: one for the chords above,
        one for the line of text
        """
        text = self.src_tixi.getTextElement(srcPath).strip()
        if not CFG.CS in text:
            return False

        self.tixi.createElement(targetPath, "p")
        pPath = "{}/p[{}]".format(targetPath, self.tixi.getNamedChildrenCount(targetPath, "p"))

        for line in SongWriter._identifyLinesWithChords(text):
            if isinstance(line, str):
                self.tixi.addTextElement(pPath, "div", line)
            elif isinstance(line, LineWithChords):
                self.tixi.createElement(pPath, "table")
                row = self.tixi.getNamedChildrenCount(pPath, "table")
                tbPath = "{}/table[{}]".format(pPath, row)

                # with the empty element [''] in front, the chords should have the same length as the textChunks
                chords = [''] + line.chords[0].split(" ")
                textChunks = line.text.split(CFG.CI)

                self.tixi.createElement(tbPath, "tr")
                self.tixi.createElement(tbPath, "tr")
                crdPath = "{}/tr[1]".format(tbPath)
                txtPath = "{}/tr[2]".format(tbPath)
                self.tixi.addTextAttribute(crdPath, "class", "chords_above")

                while chords or textChunks:
                    if not chords:
                        # Run out of chords. Ignore the rest of the CFG.CI characters.
                        chunk = "".join(textChunks)
                        chord = ""
                    elif not textChunks:
                        # Run out of CFG.CI characters. Just add the remaining chords at the end of the line
                        chunk = ""
                        chord = " ".join(chords)
                    else:
                        chord = chords.pop(0)
                        chunk = textChunks.pop(0)
                        if chunk.endswith(" "):
                            chunk = chunk[:-1] + "&nbsp;"
                    self.tixi.addTextElement(crdPath, "td", chord)
                    self.tixi.addTextElement(txtPath, "td", chunk)
        return True

    def write_chords_beside(self, srcPath, targetPath):
        """
        In this format, the <p/> element contains one <table/> element, where
        every row has two columns: one for the line of text, the other for chords
        """
        text = self.src_tixi.getTextElement(srcPath).strip()
        if not CFG.CS in text:
            return False
        lines = [line.strip().split(CFG.CS) for line in text.split('\n')]

        self.tixi.createElement(targetPath, "p")
        pPath = "{}/p[{}]".format(targetPath, self.tixi.getNamedChildrenCount(targetPath, "p"))
        self.tixi.createElement(pPath, "table")
        tbPath = pPath + "/table"
        self.tixi.addTextAttribute(tbPath, "class", "chords_beside")
        for line in lines:
            self.tixi.createElement(tbPath, "tr")
            row = self.tixi.getNamedChildrenCount(tbPath, "tr")
            trPath = "{}/tr[{}]".format(tbPath, row)
            self.tixi.addTextElement(trPath, "td", line[0].replace(CFG.CI, ""))
            try:
                self.tixi.addTextElement(trPath, "td", line[1])
                self.tixi.addTextAttribute(trPath + "/td[2]", "class", "chords")
            except IndexError:
                pass

        return True

    def write_without_chords(self, srcPath, targetPath):
        """
        Get rid of all chord markers and ignore the presence of chords. 
        Write the whole part as a single text element, replacing the newlines
        with newline HTML markers
        """

        text = self.src_tixi.getTextElement(srcPath).strip()
        lines = [line.strip().split(CFG.CS)[0].replace(CFG.CI, "") for line in text.split('\n')]
        text = "<br/>\n".join(lines)  # Leave the \n for better appearance

        self.tixi.addTextElement(self.root + "/body", "p", "\n{}\n".format(text))
        return True

    def write_links(self):
        """If the song contains <link> elements, find all other songs that have the same title as mentioned in the link
            and create approptiate <a href=...> elements
        """
        xPath = self.src_path + "/link[@title]"
        titles_found = []
        targetPath = "/html/body"
        linkPcreated = bool(self.tixi.tryXPathEvaluateNodeNumber(targetPath + "/p[@class='links']"))
        for path in self.src_tixi.getPathsFromXPathExpression(xPath):
            if not linkPcreated:
                # Create the new paragraph to store the links

                #  <h3>Zobacz też</h3>
                self.tixi.addTextElement(targetPath, "h3", "Zobacz też")

                #  <p class="links/>
                targetPath = self.tixi.getNewElementPath(targetPath, "p")
                self.tixi.addTextAttribute(targetPath, "class", "links")

                #  <p class="links>
                #    <ul/>
                #  </p>
                targetPath = self.tixi.getNewElementPath(targetPath, "ul")
                linkPcreated = True

            title = self.tixi.getTextAttribute(path, "title")
            if title in titles_found:
                # Don't want to repeat if the links have already been created for this title
                continue
            titles_found.append(title)

            # Find all songs that have this linked title - each will create a separate
            # <li><a href="...xhtml">Title</a><div> (authors)</div></li> item
            #
            xPath = "//song[@title='{}' and @xhtml]".format(title)
            for songPath in self.src_tixi.getPathsFromXPathExpression(xPath):
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
                authors = "({})".format(", ".join(authors))

                #  <p class="links>
                #    <ul>
                #        <li/>
                #    </ul>
                #  </p>
                liPath = self.tixi.getNewElementPath(targetPath, "li")

                #  <p class="links>
                #    <ul>
                #        <li><a href="...xhtml">Linked song title</a>                                  </li>
                #    </ul>
                #  </p>
                aPath = self.tixi.getNewTextElementPath(liPath, "a", title)
                self.tixi.addTextAttribute(aPath, "href", file)

                #  <p class="links>
                #    <ul>
                #        <li><a href="...xhtml">Linked song title</a><div style="..."> (authors)</div> </li>
                #    </ul>
                #  </p>
                divPath = self.tixi.getNewTextElementPath(liPath, "span", authors)
                self.tixi.addTextAttribute(divPath, "style", "font-size:12px")

    @staticmethod
    def _identifyLinesWithChords(text: str) -> list:
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
            chords = [s.strip() for s in line.split(CFG.CS)]
            text = chords.pop(0)
            if chords == []:
                if noChordLines is None:
                    noChordLines = text
                else:
                    noChordLines += "<br/>\n" + text
            else:
                if noChordLines is not None:
                    # Append the chunk of text to the output and reset the noChordLines collector
                    output.append(noChordLines)
                    noChordLines = None
                output.append(LineWithChords(text, chords))

        if noChordLines is not None:
            # Append the chunk of text to the output and reset the noChordLines collector
            output.append(noChordLines)

        return output