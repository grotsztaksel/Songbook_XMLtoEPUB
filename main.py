# -*- coding: utf-8 -*-
"""
Created on 14.11.2020 17:05

@author: Piotr Gradkowski <grotsztaksel@o2.pl>
"""

__authors__ = ['Piotr Gradkowski <grotsztaksel@o2.pl>']
__date__ = '2020-11-14'

import os
import sys
import logging

from scripts.tools.song_book_generator import SongBookGenerator

logfile = "ebook_generator.log"


def main(argv):
    sys.excepthook = print_exceptions
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s",
                        handlers=[
                            logging.FileHandler(logfile, 'w', 'utf-8'),
                            logging.StreamHandler(sys.stdout)
                        ]
                        )
    print("Logging information to {}".format(os.path.abspath(os.path.join(os.getcwd(), logfile))))

    if len(argv) < 2:
        raise IOError("Need an XML file name as input!")

    xsd_file = os.path.join(os.path.dirname(__file__), "config", "source_schema.xsd")
    if not os.path.isfile(xsd_file):
        xsd_file = None
    sg = SongBookGenerator(argv[1], xsd_file)
    sg.write_songs()
    sg.write_sections()
    sg.write_indexes()
    sg.write_toc()
    sg.write_metadata()
    logging.info("DONE!")


def print_exceptions(etype, value, tb):
    import traceback
    text = "\n".join(traceback.format_exception(etype, value, tb))
    logging.error(text)
    traceback.format_exception(etype, value, tb)


if __name__ == '__main__':
    main(sys.argv)
    from subprocess import Popen

    bat = "html2kindle.bat"
    cwd = r"C:\Users\piotr\Documents\Songbook"
    logging.info(f"Executing {bat} in {cwd}")
    p = Popen(bat, cwd=cwd)
    stdout, stderr = p.communicate()
