# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import os
import shutil
import sys

from config import CFG
from tixi import Tixi, TixiException
from tools import HtmlWriter


def write_songs(max_n_songs=None):
    """
    Read the source file and for each song defined, write a properly formatted
    song xml file in the required location
    """
    tixi = Tixi()
    tixi.open(CFG.SONG_SRC_XML, recursive=True)
    tixi.registerNamespace("http://www.w3.org/2001/XMLSchema-instance", 'xsd')

    xPath = "//song[@title]"
    try:
        n = tixi.xPathEvaluateNodeNumber(xPath)
    except TixiException:
        n = 0

    print("Found {} songs".format(n))

    for i in range(1, min(n + 1, max_n_songs)):
        xmlPath = tixi.xPathExpressionGetXPath(xPath, i)
        writer = HtmlWriter(tixi, xmlPath)
        writer.write_song_file()


def main(argv):
    sys.excepthook = print_exceptions
    shutil.rmtree(CFG.SONG_HTML_DIR, ignore_errors=True)
    os.mkdir(CFG.SONG_HTML_DIR)
    write_songs(10)


def print_exceptions(etype, value, tb):
    import sys
    import traceback
    from PyQt5.QtWidgets import QMessageBox

    text = "\n".join(traceback.format_exception(etype, value, tb))
    QMessageBox.critical(None, "Python Error!", text)


if __name__ == '__main__':
    main(sys.argv)
