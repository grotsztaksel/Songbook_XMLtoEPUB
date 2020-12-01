# -*- coding: utf-8 -*-
"""
Created on 01.12.2020 18:52
 
@author: piotr
"""
import os
import re

from tixi import Tixi, TixiException, ReturnCode

from .utf_simplifier import UtfSimplifier


class SourceSplitter(object):
    """Read in the source song file and produce a number of smaller song out of it.
    Might be useful, if your songbook source becomes large and your text edior
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
            output +=  self.moveToFile(prt)


        outputFile = src.rsplit(".", 1)[0] + "_split.xml"
        o = open(outputFile, "w",  encoding='utf8')
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
        print ("Save xml:", fileName)
        tixi.saveCompleteDocument(os.path.join(self.dir,fileName))
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
