# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import os
import sys

from tools.song_book_generator import SongBookGenerator


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
