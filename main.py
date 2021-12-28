# -*- coding: utf-8 -*-
"""
Created on 14.11.2020 17:05

@author: Piotr Gradkowski <grotsztaksel@o2.pl>
"""

__authors__ = ['Piotr Gradkowski <grotsztaksel@o2.pl>']
__date__ = '2020-11-14'

import argparse
import logging
import os
import pathlib
import sys

try:
    # Enable importing modules from PATH environmental variable (Python 3.8+ on Windows)
    _dllDirs = [os.add_dll_directory(d) for d in os.environ["PATH"].split(";") if os.path.isdir(d)]
except AttributeError:
    pass

from scripts.tools.song_book_generator import SongBookGenerator


def main(argparser: argparse.ArgumentParser):
    sys.excepthook = print_exceptions
    args = argparser.parse_args()
    logfile = args.logfile.buffer.raw.name
    loglevel = {'critical': logging.CRITICAL,
                'error': logging.ERROR,
                'warning': logging.WARNING,
                'info': logging.INFO,
                'debug': logging.DEBUG}[args.loglevel]
    logging.basicConfig(level=loglevel,
                        format="%(asctime)s [%(levelname)s] %(message)s",
                        handlers=[
                            logging.FileHandler(logfile, 'w', 'utf-8'),
                            logging.StreamHandler(sys.stdout)
                        ]
                        )
    print("Logging information to {}".format(os.path.abspath(os.path.join(os.getcwd(), logfile))))

    xsd_file = os.path.join(os.path.dirname(__file__), "config", "source_schema.xsd")
    if not os.path.isfile(xsd_file):
        xsd_file = None
    sg = SongBookGenerator(args.input.buffer.raw.name, xsd_file)
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
    parser = argparse.ArgumentParser(description="Generate a songbook e-Book from XML files")
    parser.add_argument('input', type=argparse.FileType('r'),
                        help="Name of the input XML file")
    parser.add_argument('--logfile', type=argparse.FileType('w'), default="ebook_generator.log",
                        help="Name of the log file")
    parser.add_argument('--loglevel', type=str, choices=['critical', 'error', 'warning', 'info', 'debug'],
                        default='info',
                        help="Level of logged information")

    parser.add_argument('--postproc', type=str,
                        help="Name of the postprocessing script. For example a script that will automatically zip the "
                             "output directory (this tool does not do that by itself)")
    parser.add_argument('--postwd', type=str, default=os.getcwd(),
                        help="Working directory where the postprocessing script should be launched")
    main(parser)
    from subprocess import Popen

    bat = "html2kindle.bat"
    cwd = r"C:\Users\piotr\Documents\Songbook"
    logging.info(f"Executing {bat} in {cwd}")
    p = Popen(bat, cwd=cwd)
    stdout, stderr = p.communicate()
