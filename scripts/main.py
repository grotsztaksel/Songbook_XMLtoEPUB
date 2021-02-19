# -*- coding: utf-8 -*-
"""
Created on 14.11.2020 17:05

@author: Piotr Gradkowski <grotsztaksel@o2.pl>
"""

__authors__ = ['Piotr Gradkowski <grotsztaksel@o2.pl>']
__date__ = '2020-11-14'

import os
import sys

from scripts.tools.song_book_generator import SongBookGenerator


def main(argv):
    sys.excepthook = print_exceptions

    if len(argv) < 2:
        raise IOError("Need an XML file name as input!")

    xsd_file = os.path.join(os.path.dirname(__file__), "config", "source_schema.xsd")
    if not os.path.isfile(xsd_file):
        xsd_file = None
    sg = SongBookGenerator(argv[1], xsd_file)
    sg.write_songs()
    sg.write_sections()
    sg.write_metadata()
    sg.write_toc()
    sg.write_indexes()


def print_exceptions(etype, value, tb):
    import traceback
    text = "\n".join(traceback.format_exception(etype, value, tb))
    print(text)
    traceback.format_exception(etype, value, tb)


if __name__ == '__main__':
    main(sys.argv)
