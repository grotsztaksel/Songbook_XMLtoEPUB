# -*- coding: utf-8 -*-|"łmkj,ncbgfdxsa!
"""
Created on 27.11.2020 19:51
 
@author: Piotr Gradkowski <grotsztaksel@o2.pl>
"""
__authors__ = ['Piotr Gradkowski <grotsztaksel@o2.pl>']
__date__ = '2020-11-27'
__all__ = ['AuthorsWriter']

import re

from src.config import EpubSongbookConfig
from src.tixi import Tixi
from .html_writer import HtmlWriter


class AuthorsWriter(HtmlWriter):
    """Class responsible for writing the index of authors"""

    def __init__(self, tixi: Tixi, settings: EpubSongbookConfig):
        super(AuthorsWriter, self).__init__(tixi, settings)
        # This the author strings to standardized author names to appear in the index

        self.standardized_author_names = dict()
        self.songs_by_author = dict()
        self.findSongsByAuthors()

    #
    @staticmethod
    def standardize_author_name(name, isBandName=False):
        """Standardize author name:
        - "J. Doe" translates to "Doe, J."
        - "John Doe" translates to "Doe, John"
        - "Doe, John" remains "Doe, John"
        - "Cher" remains "Cher"
        - "J.F. Kennedy" translates to "Kennedy, J. F."  (note the missing space in 'J.F. K...')

        If input argument isBandName is True, then the order of words is not kept
        """

        # Initial modifications and standarizations
        name = name.replace(".", ". ")  # Add space after dot
        name = name.replace(",", ", ")  # Add space after comma
        name = re.sub(r' +', ' ', name)  # Replace multiplem spaces with one

        names = name.split(" ")

        if isBandName:
            return name
        if names[0][-1] == ",":
            return name

        if len(names) <= 1:
            return name

        newName = []
        newName.append(names.pop(-1) + ",")
        newName.extend(names)
        return " ".join(newName)

    #
    def findSongsByAuthors(self):
        """For each author name in the dictionary, find the songs associated with that name. Then, find
           the standardized name and create a list (so that it can be sorted) of tuples (title, file)
        """
        for path in self.src_tixi.xPathExpressionGetAllXPaths("//song[@lyrics or @music or @band]"):
            for attr in ["lyrics", "music", "band"]:
                isBand = attr == "band"
                # For each of these attributes, if exist and not yet in the dictionary,
                # Standardize te name. If it is a band, make sure not to alter the word order
                if self.src_tixi.checkAttribute(path, attr):
                    authors = self.src_tixi.getTextAttribute(path, attr).strip()
                    if isBand:
                        authors = [authors]
                    else:
                        authors = authors.split(";")

                    for a in authors:
                        author = a.strip()
                        stdName = AuthorsWriter.standardize_author_name(author, isBand)
                        self.standardized_author_names[author] = stdName

                        title = self.src_tixi.getTextAttribute(path, "title")
                        file = self.src_tixi.getTextAttribute(path, "xhtml")
                        if stdName not in self.songs_by_author:
                            self.songs_by_author[stdName] = dict()
                        self.songs_by_author[self.standardized_author_names[author]][title] = file

    #
    def write_index(self):
        """Write the whole block of the index"""
        bPath = self.tixi.createElement("/html", "body")
        self.tixi.addTextElement(bPath, "h2", self.settings.authors_index_title)

        I = ""  # Initial
        for author in sorted(self.songs_by_author.keys()):
            hisOrHerSongs = self.songs_by_author[author]
            if not hisOrHerSongs:
                continue
            if author[0] > I:
                I = author[0]
                self.tixi.addTextElement(bPath, "h3", I)

            self.tixi.addTextElement(bPath, "h4", author)
            ulPath = self.tixi.createElement(bPath, "ul")

            for song in sorted(hisOrHerSongs.keys()):
                liPath = self.tixi.createElement(ulPath, "li")
                file = hisOrHerSongs[song]

                aPath = self.tixi.addTextElement(liPath, "a", song)
                self.tixi.addTextAttribute(aPath, "href", file)
