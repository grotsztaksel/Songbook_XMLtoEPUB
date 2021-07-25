# -*- coding: utf-8 -*-
"""
Created on Sat Nov 14 17:32:27 2020

@author: Piotr Gradkowski <grotsztaksel@o2.pl>
"""

__all__ = ['ChordMode', 'EpubSongbookConfig']
__authors__ = ['Piotr Gradkowski <grotsztaksel@o2.pl>']
__date__ = '2020-11-14'

import getpass
import os
import shutil
from enum import Enum
from typing import Any

try:
    from scripts.tixi import Tixi, TixiException, ReturnCode
except Exception:
    pth = os.environ["PATH"].split(";")
    print(os.path.isfile(os.path.join(pth[-2], "tixi3.dll")))
    raise Exception("--\n--".join(pth))


class ChordMode(Enum):
    """
    CHORD_ABOVE - the chords will be written above the text, indicating the place, where the chord should be played
    CHORD_BESIDE - the chords will be listed to the right of the line
    NO_CHORD - the chords will not be written alltogether
    """
    CHORDS_ABOVE = 0
    CHORDS_BESIDE = 1
    NO_CHORDS = 2

    #
    @staticmethod
    def get(text):
        """Convert a text value (e.g. from the text attribute) to an Enum value"""
        if text == "CHORDS_ABOVE":
            return ChordMode.CHORDS_ABOVE
        elif text == "CHORDS_BESIDE":
            return ChordMode.CHORDS_BESIDE
        elif text == "NO_CHORDS":
            return ChordMode.NO_CHORDS

    #
    def __str__(self):
        if self == ChordMode.CHORDS_ABOVE:
            return "CHORDS_ABOVE"
        elif self == ChordMode.CHORDS_BESIDE:
            return "CHORDS_BESIDE"
        elif self == ChordMode.NO_CHORDS:
            return "NO_CHORDS"


class EpubSongbookConfig():
    """Class responsible for setting up the output directory: creating or copying basic files like
          metadata, mimetypes, etc.
        This class is NOT responsible for writing the content of the songbook
     """

    def __init__(self, tixi: Tixi):
        """

        :param tixi: input tixi to find the <settings> element
        :param xsd_file: XSD schema file (to take default values)
        """
        self.tixi = tixi

        self.xsd_elements_2_settings_map = {"username": "user",
                                            "title": "title",
                                            "max_songs": "maxsongs",
                                            "section_title": "default_section_title",
                                            "authors_index_title": "authors_index_title",
                                            "alphabetical_index_title": "alphabetical_index_title",
                                            "toc_title": "toc_title",
                                            "links_header": "links_header",
                                            "language": "lang",
                                            "encoding": "encoding",
                                            "output_dir": "dir_out",
                                            "template_dir": "template_dir",
                                            "lyrics_string": "lyrics_string",
                                            "music_string": "music_string",
                                            "unknown_author": "unknown_author",
                                            "prefered_chord_mode": "chordType",
                                            "chord_separator": "CS",
                                            "chord_insertion_character": "CI"}

        xsd_file = os.path.join(os.path.dirname(__file__), "source_schema.xsd")
        self.xsd_song = os.path.join(os.path.dirname(__file__), "song_schema.xsd")
        self.xsd = Tixi()
        self.xsd.open(xsd_file)
        self.xsd.registerNamespacesFromDocument()
        self.xsd_spath = '/xs:schema/xs:complexType[@name="settings"]/xs:all/xs:element'

        self._setup_defaults()

        self._getSettings()

    def _setup_defaults(self):
        """Set up defaults"""

        # Validate with default values
        self.tixi.schemaValidateWithDefaultsFromFile(self.xsd.getDocumentPath())

        # copy the keys of self.xsd_elements_2_settings_map to later make sure that all have been defined in xsd
        settings = list(self.xsd_elements_2_settings_map.keys())

        for setting in self.xsd.xPathExpressionGetAllXPaths(self.xsd_spath):
            name = self.xsd.getTextAttribute(setting, "name")
            # If setting is not in self.xsd_elements_2_settings_map, this will throw an error
            try:
                settings.remove(name)
            except ValueError:
                xsd_file = self.xsd.getDocumentPath()
                raise ValueError("EpubSongbookConfig.xsd_elements_2_settings_map "
                                 "does not have {}, which is present in {}. xsd_elements_2_settings_map must agree with"
                                 "settings listed in the {}".format(name, xsd_file, xsd_file))

            # Set the default value if it is defined in XSD
            if self.xsd.checkAttribute(setting, "default"):
                a = self.xsd.getTextAttribute(setting, "default")

                defvalue = self.type(setting, a)
            else:
                defvalue = None
            setattr(self, self.xsd_elements_2_settings_map[name], defvalue)

        # Check if all settings defined in self.xsd_elements_2_settings_map were found in XSD
        if settings:
            raise ValueError("EpubSongbookConfig.xsd_elements_2_settings_map has more settings defined than the XSD:\n"
                             "\n".join(settings))

        # Special treatment to some variables that could not have their default defined
        xsd_path = self.xsd.xPathExpressionGetXPath('{}[@name="{}"]'.format(self.xsd_spath, "prefered_chord_mode"), 1)
        self.chordType = ChordMode.get(self.xsd.getTextAttribute(xsd_path, "default"))
        self.user = getpass.getuser()
        self.template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../", "template"))
        self.dir_text = None

    def type(self, xsd_path: str, value: str) -> Any:
        """Return the value of an attribute in the appropriate type. List of types is taken from
            https://www.w3.org/TR/xmlschema-2/
        """
        if self.xsd.checkAttribute(xsd_path, "type"):
            tp = self.xsd.getTextAttribute(xsd_path, "type").lstrip("xs:").lstrip("xsd:")
        else:
            # Maybe it is a simple type with some restrictions?
            paths = self.xsd.xPathExpressionGetAllXPaths('{}/xs:simpleType/xs:restriction[@base]'.format(xsd_path))
            if len(paths) != 1:
                return value
            tp = self.xsd.getTextAttribute(paths[0], "base").lstrip("xs:").lstrip("xsd:")

        # Simple types
        if tp in ["byte", "int", "integer", "long", "negativeInteger", "nonNegativeInteger", "nonPositiveInteger",
                  "positiveInteger", "short", "unsignedLong", "unsignedInt", "unsignedShort", "unsignedByte"]:
            return int(value)
        elif tp in ["string", "normalizedString", "token", "language", "Name", "NCName", "ID", "IDREF", "IDREFS",
                    "NMTOKEN",
                    "NMTOKENS", "ENTITY", "ENTITIES"]:
            return str(value)
        elif tp in ["float", "double", "decimal"]:
            return float(value)
        elif tp in ["boolean"]:
            return value == "true"

        # Derived types

        # Didn't recognize the value. Just return it
        return value

    #
    def _getSettings(self):
        """Try reading the settings written in the input file.
        If a given setting is present, override the default one """

        spath = "/songbook/settings"

        for xmlName, myName in self.xsd_elements_2_settings_map.items():
            path = spath + "/" + xmlName
            xpath = '{}[@name="{}"]'.format(self.xsd_spath, xmlName)
            if self.tixi.checkElement(path):
                value = self.tixi.getTextElement(path)
                value = self.type(xpath, value)
                if xmlName == "encoding" and value == "":
                    value = None
                setattr(self, myName, value)

        # ToDo: Need to find a better way to loop over these attributes
        path = spath + "/max_songs"
        if self.tixi.checkElement(path):
            try:
                self.maxsongs = int(self.tixi.getTextElement(path))
            except ValueError:
                pass
        path = spath + "/prefered_chord_mode"
        if self.tixi.checkElement(path):
            self.chordType = \
                {"CHORDS_ABOVE": ChordMode.CHORDS_ABOVE,
                 "CHORDS_BESIDE": ChordMode.CHORDS_BESIDE,
                 "NO_CHORDS": ChordMode.NO_CHORDS}[self.tixi.getTextElement(path)]

    #
    def defineOutputDir(self):
        """Use the settings to create output directory and place the essential files in it
        """

        if not os.path.isabs(self.dir_out):
            file = os.path.abspath(os.path.dirname(self.tixi.getDocumentPath()))
            rel = self.dir_out
            # Get the absolute path built from the input file location and the dir_out
            self.dir_out = os.path.normpath(os.path.join(file, rel))

        shutil.rmtree(self.dir_out, ignore_errors=True)
        self.dir_text = os.path.join(self.dir_out, "text")

    #
    def placeEssentialFiles(self):

        # Do not check for template existence. If it does not, an error will be thrown
        shutil.copytree(self.template_dir, self.dir_out)
        os.makedirs(self.dir_text, exist_ok=True)

        # Write the mimetype from scratch. It's not too long after all...
        with open(os.path.join(self.dir_out, "mimetype"), "w") as mime:
            mime.write("application/epub+zip")

        # Slurp the metadata.opf
        meta = os.path.join(self.dir_out, "metadata.opf")
        with open(meta, "r", encoding='utf8') as f:
            metadata = f.read()

        metadata = metadata.replace("${user}", self.user)
        metadata = metadata.replace("${title}", self.title)
        metadata = metadata.replace("${language}", self.lang)

        # Rewrite the file
        with open(meta, "w", encoding='utf8') as f:
            f.write(metadata)

    #
    def setupAttributes(self):
        """Use the settings to add attributes to the toplevel elements of the songbook, so that they can be later
        overriden
        """
        xPath = "/songbook/*[self::section or self::song][not(@chord_mode)]"
        for path in self.tixi.xPathExpressionGetAllXPaths(xPath):
            self.tixi.addTextAttribute(path, "chord_mode", str(self.chordType))
