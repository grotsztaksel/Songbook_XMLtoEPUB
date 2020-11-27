# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import os
import shutil
import sys

from config import CFG
from tools.song_book_generator import SongBookGenerator


def main(argv):
    sys.excepthook = print_exceptions
    shutil.rmtree(CFG.SONG_HTML_DIR, ignore_errors=True)
    os.mkdir(CFG.SONG_HTML_DIR)
    sg = SongBookGenerator(30)
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
