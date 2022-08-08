import os
from unittest import TestCase
from unittest.mock import patch

from adapter.comm.tools import (
    convert_network_drive_path,
    get_mount_point_len,
    mark_time,
)


class Test(TestCase):
    @patch('sys.platform', 'darwin')
    def test_convert_network_drive_path_mac(self):
        str_or_path = '/Volumes/A/abc/c/d/1.xlsx'
        self.assertEqual(convert_network_drive_path(str_or_path), '/Volumes/A/abc/c/d/1.xlsx')
        str_or_path = '/media/b/xyz/c/d/1.xlsx'
        self.assertEqual(convert_network_drive_path(str_or_path), '/Volumes/A/xyz/c/d/1.xlsx')
        str_or_path = r'X:\abc\def\hij\1.xlsx'
        self.assertEqual(convert_network_drive_path(str_or_path), '/Volumes/A/abc/def/hij/1.xlsx')
        # test backwards compatibility
        str_or_path = '/Volumes/A/abc/c/d/1.xlsx'
        self.assertEqual(convert_network_drive_path(str_or_path, mapping=[('X:', '/Volumes/A')]),
                         '/Volumes/A/abc/c/d/1.xlsx')
        str_or_path = r'X:\abc\def\hij\1.xlsx'
        self.assertEqual(convert_network_drive_path(str_or_path, mapping=[('X:', '/Volumes/A')]),
                         '/Volumes/A/abc/def/hij/1.xlsx')
        path_a = r"A:\some_folder\some_file.txt"
        path_b = '/Volumes/A/some_folder/some_file.txt'
        self.assertEqual(
            convert_network_drive_path(path_a, mapping=[('A:', '/Volumes/A')]), path_b)
        # test convert_network_drive_path empty
        p = {}
        self.assertEqual(convert_network_drive_path(str_or_path=p
                                                    ), p)

        # test convert_network_drive_path relative
        str_or_path = r'abc\def\hij\1.xlsx'
        self.assertEqual(convert_network_drive_path(str_or_path), str_or_path)
        str_or_path = 'output/file.txt'
        self.assertEqual(convert_network_drive_path(str_or_path), str_or_path)

        # test convert_network_drive_path local_nonexists
        str_or_path = r"C:\some_folder\some_file.xlsx"
        expected_path = '/Volumes/A/some_folder/some_file.xlsx'
        self.assertEqual(convert_network_drive_path(str_or_path), expected_path)

        # test convert_network_drive_path exists
        str_or_path = r'Adapter\adapter\tests\corrupt.db'
        self.assertEqual(convert_network_drive_path(str_or_path), str_or_path)
        str_or_path = r'test_done.db'
        self.assertEqual(convert_network_drive_path(str_or_path), str_or_path)
        str_or_path = 'input/input_folder'
        self.assertEqual(convert_network_drive_path(str_or_path), str_or_path)
        str_or_path = r'output\output_folder'
        self.assertEqual(convert_network_drive_path(str_or_path), str_or_path)

    @patch('sys.platform', 'win32')
    def test_convert_network_drive_path_win(self):
        str_or_path = '/Volumes/A/abc/c/d/1.xlsx'
        self.assertEqual(convert_network_drive_path(str_or_path), r'X:abc\c\d\1.xlsx')
        str_or_path = '/media/b/xyz/c/d/1.xlsx'
        self.assertEqual(convert_network_drive_path(str_or_path), r'X:xyz\c\d\1.xlsx')
        str_or_path = r'X:\abc\def\hij\1.xlsx'
        self.assertEqual(convert_network_drive_path(str_or_path), r'X:\abc\def\hij\1.xlsx')
        str_or_path = '/Volumes/A/abc/c/d/1.xlsx'
        # test backwards compatibility
        self.assertEqual(convert_network_drive_path(str_or_path, mapping=[('X:', '/Volumes/A')]), r'X:abc\c\d\1.xlsx')
        str_or_path = r'X:\abc\def\hij\1.xlsx'
        self.assertEqual(convert_network_drive_path(str_or_path, mapping=[('X:', '/Volumes/A')]),
                         r'X:\abc\def\hij\1.xlsx')
        path_a = r'A:some_folder\some_file.txt'
        path_b = '/Volumes/A/some_folder/some_file.txt'
        self.assertEqual(
            convert_network_drive_path(path_b, mapping=[('A:', '/Volumes/A')]), path_a)
        # test convert_network_drive_path empty
        p = {}
        self.assertEqual(convert_network_drive_path(str_or_path=p
                                                    ), p)

        # test convert_network_drive_path relative
        str_or_path = r'abc\def\hij\1.xlsx'
        self.assertEqual(convert_network_drive_path(str_or_path), str_or_path)
        str_or_path = 'output/file.txt'
        self.assertEqual(convert_network_drive_path(str_or_path), str_or_path)

        # test convert_network_drive_path local_nonexists
        str_or_path = r"C:\some_folder\some_file.xlsx"
        expected_path = r"X:some_folder\some_file.xlsx"
        self.assertEqual(convert_network_drive_path(str_or_path), expected_path)

        # test convert_network_drive_path exists
        str_or_path = r'Adapter\adapter\tests\corrupt.db'
        self.assertEqual(convert_network_drive_path(str_or_path), str_or_path)
        str_or_path = r'test_done.db'
        self.assertEqual(convert_network_drive_path(str_or_path), str_or_path)
        str_or_path = 'input/input_folder'
        self.assertEqual(convert_network_drive_path(str_or_path), str_or_path)
        str_or_path = r'output\output_folder'
        self.assertEqual(convert_network_drive_path(str_or_path), str_or_path)

    @patch('sys.platform', 'linux')
    def test_convert_network_drive_path_lin(self):
        str_or_path = '/Volumes/A/abc/c/d/1.xlsx'
        self.assertEqual(convert_network_drive_path(str_or_path), '/media/b/abc/c/d/1.xlsx')
        str_or_path = '/media/b/xyz/c/d/1.xlsx'
        self.assertEqual(convert_network_drive_path(str_or_path), '/media/b/xyz/c/d/1.xlsx')
        str_or_path = r'X:\abc\def\hij\1.xlsx'
        self.assertEqual(convert_network_drive_path(str_or_path), '/media/b/abc/def/hij/1.xlsx')
        # test backwards compatibility this should not even happen since it was not supported

        # test convert_network_drive_path empty
        p = {}
        self.assertEqual(convert_network_drive_path(str_or_path=p
                                                    ), p)

        # test convert_network_drive_path relative
        str_or_path = r'abc\def\hij\1.xlsx'
        self.assertEqual(convert_network_drive_path(str_or_path), str_or_path)
        str_or_path = 'output/file.txt'
        self.assertEqual(convert_network_drive_path(str_or_path), str_or_path)

        # test convert_network_drive_path local_nonexists
        str_or_path = r"C:\some_folder\some_file.xlsx"
        expected_path = '/media/b/some_folder/some_file.xlsx'
        self.assertEqual(convert_network_drive_path(str_or_path), expected_path)

        # test convert_network_drive_path exists
        str_or_path = r'Adapter\adapter\tests\corrupt.db'
        self.assertEqual(convert_network_drive_path(str_or_path), str_or_path)
        str_or_path = r'test_done.db'
        self.assertEqual(convert_network_drive_path(str_or_path), str_or_path)
        str_or_path = 'input/input_folder'
        self.assertEqual(convert_network_drive_path(str_or_path), str_or_path)
        str_or_path = r'output\output_folder'
        self.assertEqual(convert_network_drive_path(str_or_path), str_or_path)

    def test_get_mount_point_len(self):
        self.assertEqual(get_mount_point_len(mapping={'win32': 'X:', 'darwin': '/Volumes/A', 'linux': '/media/b'},
                                             str_or_path=r'X:\Abc\1.txt'), 2)
        self.assertEqual(get_mount_point_len(mapping={'win32': 'X:', 'darwin': '/Volumes/A', 'linux': '/media/b'},
                                             str_or_path='/Volumes/A/abc/c/d/1.xlsx'), 10)

    @patch("sys.platform", "linux")
    def test_compare_output(self):
        dir1 = os.path.join(
            "X:",  # will get converted for a given OS
            "First_Level",
            "Second_Level",
            "Third_Level",
            "input",
        )
        dir2 = convert_network_drive_path(
            dir1,
            mapping={
                "win32": "X:",
                "darwin": "/Volumes/Abc",
                "linux": "/media/Abc",
            },
        )
        self.assertEqual(
            dir2,
            "/media/Abc/First_Level/Second_Level/Third_Level/input",
        )


    @patch("sys.platform", "darwin")
    def test_compare_output2(self):
        dir1 = os.path.join(
            "X:",  # will get converted for a given OS
            "First_Level",
            "Second_Level",
            "Third_Level",
            "input",
        )
        dir2 = convert_network_drive_path(
            dir1,
            mapping={
                "win32": "X:",
                "darwin": "/Volumes/Abc",
                "linux": "/media/Abc",
            },
        )
        self.assertEqual(
            dir2,
            "/Volumes/Abc/First_Level/Second_Level/Third_Level/input",
        )

    def test_mark_time(self):
        self.assertEqual(
            len(mark_time(ts_format="short")), len("_220808_1051")
        )
        self.assertEqual(
            len(mark_time(ts_format="long")), len("_2022_08_08-10h_51m")
        )
        self.assertRaises(ValueError, mark_time(ts_format="unknown"), 2)
