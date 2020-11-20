# -*- coding: utf-8 -*-
"""
Created on 20.11.2020 18:35
 
@author: piotr
"""
import os

from config import CFG
from tixi import Tixi, TixiException
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
        try:
            n = self.tixi.xPathEvaluateNodeNumber(xPath)
            print("Found {} songs".format(n))
            if self.N > 0 and n < self.N:
                self.N = n
        except TixiException:
            self.N = 0

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
