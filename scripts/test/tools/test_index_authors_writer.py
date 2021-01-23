# -*- coding: utf-8 -*-
"""
Created on 27.11.2020 22:21
 
@author: piotr
"""
import os
import unittest

from config import EpubSongbookConfig
from tixi import Tixi
from tools.index_authors_writer import AuthorsWriter


class TestAuthorsWriter(unittest.TestCase):
    def setUp(self):
        self.src_file = os.path.join(os.path.dirname(__file__), "test_song_src.xml")
        tixi = Tixi()
        tixi.open(self.src_file, recursive=True)
        self.settings = EpubSongbookConfig(tixi)
        # Need to add fake xhtml attributes, otherwise the AuthorsWriter will bomb out
        i = 0
        for path in tixi.getPathsFromXPathExpression("//song"):
            i += 1
            tixi.addTextAttribute(path, "xhtml", "song_file_{}.xhtml".format(i))

        self.writer = AuthorsWriter(tixi, self.settings)

    def test_findSOngsByAuthor(self):
        # The method should've been called upon initialization
        expected_std_author_names = {"John Doe": "Doe, John",
                                     "Mike Moo": "Moo, Mike",
                                     "P. Gradkowski": "Gradkowski, P.",
                                     "Sam Composer": "Composer, Sam",
                                     'The Developers': 'The Developers'
                                     }
        self.assertEqual(expected_std_author_names, self.writer.standardized_author_names)

        expected_songs_dict = {
            "Doe, John": {
                "Song A": "song_file_3.xhtml",
                "Song B": "song_file_4.xhtml",
                "Song C": "song_file_5.xhtml",
                "Song ABBA": "song_file_9.xhtml"
            },
            "Moo, Mike": {
                "Song C": "song_file_5.xhtml",
                "Song A": "song_file_6.xhtml"
            },
            "Gradkowski, P.": {
                "My Test Song": "song_file_2.xhtml"
            },
            "Composer, Sam": {
                "My Test Song": "song_file_2.xhtml"
            },
            'The Developers': {
                "My Test Song": "song_file_2.xhtml"
            }
        }
        self.assertEqual(expected_songs_dict, self.writer.songs_by_author)

    def test_standardize_author_name(self):
        self.assertEqual("Kowalski, M.", AuthorsWriter.standardize_author_name("M.Kowalski"))
        self.assertEqual("Kowalski, M.", AuthorsWriter.standardize_author_name("M. Kowalski"))
        self.assertEqual("Kowalski, Maniek", AuthorsWriter.standardize_author_name("Maniek Kowalski"))
        self.assertEqual("Kowalski, Maniek", AuthorsWriter.standardize_author_name("Kowalski, Maniek"))
        self.assertEqual("Perez-Reverte, A.", AuthorsWriter.standardize_author_name("A. Perez-Reverte"))
        self.assertEqual("Mozart, W. A.", AuthorsWriter.standardize_author_name("W.A.Mozart"))
        self.assertEqual("Cher", AuthorsWriter.standardize_author_name("Cher"))
        self.assertEqual("Led Zeppelin", AuthorsWriter.standardize_author_name("Led Zeppelin", isBandName=True))


if __name__ == '__main__':
    unittest.main()
