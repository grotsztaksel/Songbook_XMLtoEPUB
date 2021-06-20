# -*- coding: utf-8 -*-
"""
Created on 02.12.2020 19:39
 
@author: Piotr Gradkowski <grotsztaksel@o2.pl>
"""

__authors__ = ['Piotr Gradkowski <grotsztaksel@o2.pl>']
__date__ = '2020-12-02'
__all__ = ['SongsIndexWriter']

from scripts.config import EpubSongbookConfig
from scripts.tixi import Tixi
from .html_writer import HtmlWriter


class SongsIndexWriter(HtmlWriter):
    """Class responsible for writing the alphabetical index of songs"""

    def __init__(self, tixi: Tixi, settings: EpubSongbookConfig):
        super(SongsIndexWriter, self).__init__(tixi, settings)

        self.songs = list()

        self.getListOfSongs()

    def getListOfSongs(self):
        """
        Build a list containing song titles and the songs' html file names.
        """
        for path in self.src_tixi.xPathExpressionGetAllXPaths("//song[@title and @xhtml]"):
            title = self.src_tixi.getTextAttribute(path, "title")
            file = self.src_tixi.getTextAttribute(path, "xhtml")
            self.songs.append((title, file))
        self.songs.sort(key=lambda x: x[0])

    def write_index(self):
        bPath = self.tixi.createElement("/html", "body")
        self.tixi.addTextElement(bPath, "h2", self.settings.alphabetical_index_title)

        I = ""  # Initial
        for title, file in self.songs:
            if title[0] > I:
                I = title[0]
                self.tixi.addTextElement(bPath, "h3", I)

            ulPath = self.tixi.createElement(bPath, "ul")

            liPath = self.tixi.createElement(ulPath, "li")
            aPath = self.tixi.addTextElement(liPath, "a", title)
            self.tixi.addTextAttribute(aPath, "href", file)

    def sort_songs(self):
        """
        Return list of tuple pairs: (title, filename), sorted by the title

        """
