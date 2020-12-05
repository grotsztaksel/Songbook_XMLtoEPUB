# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import sys

from tools.song_book_generator import SongBookGenerator


def main(argv):
    sys.excepthook = print_exceptions

    if len(argv) < 2:
        raise IOError("Need an XML file name as input!")

    sg = SongBookGenerator(argv[1])
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
