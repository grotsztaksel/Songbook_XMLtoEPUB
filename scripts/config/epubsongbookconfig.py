# -*- coding: utf-8 -*-
"""
Created on Sat Nov 14 17:32:27 2020

@author: piotr
"""

__all__ = ['ChordMode', 'EpubSongbookConfig']

import getpass
import os
import shutil
from enum import Enum

from tixi import Tixi


class ChordMode(Enum):
    """
    CHORD_ABOVE - the chords will be written above the text, indicating the place, where the chord should be played
    CHORD_BESIDE - the chords will be listed to the right of the line
    NO_CHORD - the chords will not be written alltogether
    """
    CHORDS_ABOVE = 0
    CHORDS_BESIDE = 1
    NO_CHORDS = 2


class EpubSongbookConfig():
    """Class responsible for setting up the output directory: creating or copying basic files like
          metadata, mimetypes, etc.
        This class is NOT responsible for writing the content of the songbook

        The defaults are:

     """

    def __init__(self, tixi: Tixi):
        self.tixi = tixi

        # Set up defaults
        self.title = "My Songbook"
        self.user = getpass.getuser()
        self.lang = "en"
        self.maxsongs = 0  # By default, 0 means that all songs should be scanned

        self.chordType = ChordMode.CHORDS_BESIDE

        self.dir_out = "output"
        self.template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../", "template"))
        self.CS = ">"  # [C]hord [S]eparator: character that separates the text from chords lists
        self.CI = "|"  # [C]hord [I]nsertion point: character indicating the location where the chord should be changed
        #                                      while performing the song

        self._getSettings()

    def _getSettings(self):
        """Try reading the settings written in the input file.
        If a given setting is present, override the default one """

        spath = "/songbook/settings"

        elements = {"username": "user",
                    "title": "title",
                    "language": "lang",
                    "output_dir": "dir_out",
                    "template": "template_dir",
                    "chord_separator": "CS",
                    "chord_insertion_character": "CI"}

        for xmlName, myName in elements.items():
            path = spath + "/" + xmlName
            if self.tixi.checkElement(path):
                value = self.tixi.getTextElement(path)
                setattr(self, myName, value)

        # ToDo: Need to find a better way to loop over these attributes
        path = spath + "/max_songs"
        if self.tixi.checkElement(path):
            self.maxsongs = int(self.tixi.getTextElement(path))
        path = spath + "/preferred_chord_mode"
        if self.tixi.checkElement(path):
            self.chordType = \
                {"CHORDS_ABOVE": ChordMode.CHORDS_ABOVE,
                 "CHORDS_BESIDE": ChordMode.CHORDS_BESIDE,
                 "NO_CHORDS": ChordMode.NO_CHORDS}[self.tixi.getTextElement(path)]

    def createOutputDir(self):
        """Use the settings to create output directory and place the essential files in it
        """
        if not os.path.isabs(self.dir_out):
            # Get the absolute path built from the input file location and the dir_out
            self.dir_out = os.path.abspath(os.path.join(self.tixi.getDocumentPath(), self.dir_out))

        shutil.rmtree(self.dir_out, ignore_errors=True)
        os.mkdir(self.dir_out)

    def placeEssentialFiles(self):

        # Do not check for template existence. If it does not, an error will be thrown
        shutil.copytree(self.template_dir, self.dir_out)

        # Write the mimetype from scratch. It's not too long after all...
        with open(os.path.join(self.dir_out, "mimetype"), "w") as mime:
            mime.write("application/epub+zip")

        # Slurp the metadata.opf
        meta = os.path.join(self.dir_out, "metadata.opf")
        with open(meta, "r") as f:
            metadata = f.read()

        metadata = metadata.replace("${user}", self.user)
        metadata = metadata.replace("${title}", self.title)
        metadata = metadata.replace("${language}", self.lang)

        # Rewrite the file
        f = open(meta, "w")
        f.write(metadata)
        f.close()

    def setupAttributes(self):
        """Use the settings to add attributes to the toplevel elements of the songbook, so that they can be later
        overriden
        """
        xPath = "/songbook/*[self::section or self::song][not(@chord_mode)]"
        for path in self.tixi.getPathsFromXPathExpression(xPath):
            self.tixi.addTextAttribute(path, "chord_mode", self.chordType)
