# -*- coding: utf-8 -*-
"""
Created on 01.12.2020 19:07
 
@author: Piotr Gradkowski <grotsztaksel@o2.pl>
"""

__authors__ = ['Piotr Gradkowski <grotsztaksel@o2.pl>']
__date__ = '2020-12-01'

import unittest
from split_song_xml import SourceSplitter


class MyTestCase(unittest.TestCase):
    def test_deIndent(self):
        input = ""
        input += "        <node>                 \n"
        input += "            <child>            \n"
        input += "                text1          \n"
        input += "                text2          \n"
        input += "            </child>           \n"
        input += "            <child>            \n"
        input += "                txt1           \n"
        input += "                txt2           \n"
        input += "            </child>           \n"
        input += "        </node>                \n"

        expected = ""
        expected += "<node>                 \n"
        expected += "    <child>            \n"
        expected += "        text1          \n"
        expected += "        text2          \n"
        expected += "    </child>           \n"
        expected += "    <child>            \n"
        expected += "        txt1           \n"
        expected += "        txt2           \n"
        expected += "    </child>           \n"
        expected += "</node>                \n"

        self.assertEqual(expected, SourceSplitter.deIndent(input))


if __name__ == '__main__':
    unittest.main()
