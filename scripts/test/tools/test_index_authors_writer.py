# -*- coding: utf-8 -*-
"""
Created on 27.11.2020 22:21
 
@author: piotr
"""

import unittest

from tools.index_authors_writer import AuthorsWriter


class TestAuthorsWriter(unittest.TestCase):
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
