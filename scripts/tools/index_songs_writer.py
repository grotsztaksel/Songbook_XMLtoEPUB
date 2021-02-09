# -*- coding: utf-8 -*-
"""
Created on 02.12.2020 19:39
 
@author: piotr
"""

from config import EpubSongbookConfig
from tixi import Tixi
from .html_writer import HtmlWriter


class SongsIndexWriter(HtmlWriter):
    """Class responsible for writing the alphabetical index of songs"""

    def __init__(self, tixi: Tixi, settings: EpubSongbookConfig):
        super(SongsIndexWriter, self).__init__(tixi, settings)

        self.songs = dict()

        self.getListOfSongs()

    def getListOfSongs(self):
        """Build a list containing song titles and the songs' html file names.
            Create a dictionary with filenames as keys
            1. Need to sort vs song titles
            2. Song titles are not unlikely to be non-unique
            3. Because of (1-2), cannot use the song titles as dictionary keys
            4. Filenames are unique
            5. Filenames are previously built from song titles, so they should be sortable.
        """
        for path in self.src_tixi.xPathExpressionGetAllXPaths("//song[@title and @xhtml]"):
            title = self.src_tixi.getTextAttribute(path, "title")
            file = self.src_tixi.getTextAttribute(path, "xhtml")
            self.songs[file] = title

    def write_index(self):
        bPath = self.tixi.createElement("/html", "body")
        self.tixi.addTextElement(bPath, "h2", self.settings.alphabedical_index_title)

        I = ""  # Initial
        for file in sorted(self.songs.keys()):
            title = self.songs[file]
            if title[0] > I:
                I = title[0]
                self.tixi.addTextElement(bPath, "h3", I)

            ulPath = self.tixi.createElement(bPath, "ul")

            liPath = self.tixi.createElement(ulPath, "li")
            aPath = self.tixi.addTextElement(liPath, "a", title)
            self.tixi.addTextAttribute(aPath, "href", file)
