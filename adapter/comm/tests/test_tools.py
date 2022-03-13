from unittest import TestCase
from unittest.mock import patch

from adapter.comm.tools import convert_network_drive_path


class Test(TestCase):
    @patch('sys.platform', 'darwin')
    def test_convert_network_drive_path_mac(self):
        str_or_path = '//Volumes/ees/abc/c/d/1.xlsx'
        self.assertEqual(convert_network_drive_path(str_or_path), '/Volumes/A/abc/c/d/1.xlsx')
        str_or_path = '//media/ees/xyz/c/d/1.xlsx'
        self.assertEqual(convert_network_drive_path(str_or_path), '/Volumes/A/xyz/c/d/1.xlsx')
        str_or_path = r'X:\abc\def\hij\1.xlsx'
        self.assertEqual(convert_network_drive_path(str_or_path), '/Volumes/A/abc/def/hij/1.xlsx')

    @patch('sys.platform', 'win32')
    def test_convert_network_drive_path_win(self):
        str_or_path = '//Volumes/ees/abc/c/d/1.xlsx'
        self.assertEqual(convert_network_drive_path(str_or_path), r'X:abc\c\d\1.xlsx')
        str_or_path = '//media/ees/xyz/c/d/1.xlsx'
        self.assertEqual(convert_network_drive_path(str_or_path), r'X:xyz\c\d\1.xlsx')
        str_or_path = r'X:\abc\def\hij\1.xlsx'
        self.assertEqual(convert_network_drive_path(str_or_path), r'X:\abc\def\hij\1.xlsx')

    @patch('sys.platform', 'linux')
    def test_convert_network_drive_path_lin(self):
        str_or_path = '//Volumes/ees/abc/c/d/1.xlsx'
        self.assertEqual(convert_network_drive_path(str_or_path), '/media/b/abc/c/d/1.xlsx')
        str_or_path = '//media/ees/xyz/c/d/1.xlsx'
        self.assertEqual(convert_network_drive_path(str_or_path), '/media/b/xyz/c/d/1.xlsx')
        str_or_path = r'X:\abc\def\hij\1.xlsx'
        self.assertEqual(convert_network_drive_path(str_or_path), '/media/b/abc/def/hij/1.xlsx')

    def test_convert_network_drive_path_empty(self):
        p = {}
        self.assertEqual(convert_network_drive_path(str_or_path=p
                                                    ), p)

    def test_convert_network_drive_path_relative(self):
        str_or_path = r'abc\def\hij\1.xlsx'
        self.assertEqual(convert_network_drive_path(str_or_path), str_or_path)
        str_or_path = 'output/file.txt'
        self.assertEqual(convert_network_drive_path(str_or_path), str_or_path)

    def test_convert_network_drive_path_exists(self):
        str_or_path = r'..\..\..\Adapter\adapter\tests\corrupt.db'
        self.assertEqual(convert_network_drive_path(str_or_path), str_or_path)
        str_or_path = r'test_done.db'
        self.assertEqual(convert_network_drive_path(str_or_path), str_or_path)
