# -*- coding: utf-8 -*-
"""
Created on 05.12.2020 17:46
 
@author: Piotr Gradkowski <grotsztaksel@o2.pl>
"""

import os
import re
import sys

from tixi import Tixi, TixiException
from tools import UtfSimplifier


def main(argv):
    splitter = SourceSplitter(argv[1])
    return 0


class SourceSplitter(object):
    """Read in the source song file and produce a number of smaller songs out of it.
    Might be useful, if your songbook source becomes large and your text editor
    gets sluggish with it.
    """

    def __init__(self, src):
        self.src = src
        self.dir = os.path.dirname(self.src)

        self.usedFileNames = []

        pattern = r"(\n *<song[^b].+?</song>)"

        with open(src, "r", encoding='utf8') as f:
            file = f.read()

        output = ""
        documentParts = re.split(pattern, file, flags=re.DOTALL)

        for prt in documentParts:
            output += self.moveToFile(prt)

        outputFile = src.rsplit(".", 1)[0] + "_split.xml"
        o = open(outputFile, "w", encoding='utf8')
        o.write(output)
        o.close

    def moveToFile(self, text):
        """Try reading a song from the text and moving it to a separate file.
           If successful, return a "externaldata" xml element as text, indented so, that the indentation
           matches the input string. Otherwise, return the input text
        """
        tixi = Tixi()
        try:
            tixi.openString(text)
        except TixiException as e:
            return text
        spaces = text.find("<") * " "
        root = "/" + tixi.getChildNodeName("/", 1)
        title = tixi.getTextAttribute(root, "title")

        file_name_base = UtfSimplifier.toAscii(title).replace(" ", "_").lower()

        suffix = ""
        ext = ".xml"
        fileNameTaken = True
        number = ""
        while fileNameTaken:
            fileName = file_name_base + suffix + ext
            fileNameTaken = fileName in self.usedFileNames
            if not suffix:
                number = 0
            number += 1
            suffix = "_" + str(number)
        self.usedFileNames.append(fileName)
        print("Save xml:", fileName)
        tixi.saveCompleteDocument(os.path.join(self.dir, fileName))
        tixi_ext = Tixi()
        tixi_ext.create("externaldata")
        tixi_ext.addTextAttribute("/externaldata", "title", title)
        tixi_ext.addTextElement("/externaldata", "path", "file://./")
        tixi_ext.addTextElement("/externaldata", "filename", fileName)

        output = ""
        for line in tixi_ext.exportDocumentAsString().split("\n")[1:]:
            # [1:] to skip the xml header (<?xml version="1.0"?>)
            output += spaces + line + "\n"
        return output

    @staticmethod
    def deIndent(text):
        """Find the beginning of the first xml tag, count the number of preceding spaces
        and remove the same number of spaces from the beginning of each line"""

        n_spaces = text.find("<")
        if n_spaces < 0:
            return text

        output = []
        for line in text.split("\n"):
            output.append(line[n_spaces:])

        return "\n".join(output)


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
    for song in tixi.xPathExpressionGetAllXPaths(songXPath):
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
        print("Add external Link to: {}\n    file: {}".format(song, os.path.join(os.path.dirname(input), fileName)))
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


if __name__ == '__main__':
    main(sys.argv)
