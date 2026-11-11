import os
import re
from unittest.mock import patch

import pytest

from adapter.comm.tools import (
    convert_network_drive_path,
    get_mount_point_len,
    mark_time,
    process_column_labels,
)


class Test:
    """comm.tools: converting network-drive paths between OS mount points, and
    timestamps for run tags.
    """

    @patch("sys.platform", "darwin")
    def test_convert_network_drive_path_mac(self):
        """convert_network_drive_path() on macOS maps Windows and Linux network-drive paths
        to /Volumes/A, and leaves relative and local paths unchanged.
        """
        str_or_path = "/Volumes/A/abc/c/d/1.xlsx"
        assert convert_network_drive_path(str_or_path) == "/Volumes/A/abc/c/d/1.xlsx"
        str_or_path = "/media/b/xyz/c/d/1.xlsx"
        assert convert_network_drive_path(str_or_path) == "/Volumes/A/xyz/c/d/1.xlsx"
        str_or_path = r"X:\abc\def\hij\1.xlsx"
        assert (
            convert_network_drive_path(str_or_path) == "/Volumes/A/abc/def/hij/1.xlsx"
        )
        # test backwards compatibility
        str_or_path = "/Volumes/A/abc/c/d/1.xlsx"
        assert (
            convert_network_drive_path(str_or_path, mapping=[("X:", "/Volumes/A")])
            == "/Volumes/A/abc/c/d/1.xlsx"
        )
        str_or_path = r"X:\abc\def\hij\1.xlsx"
        assert (
            convert_network_drive_path(str_or_path, mapping=[("X:", "/Volumes/A")])
            == "/Volumes/A/abc/def/hij/1.xlsx"
        )
        path_a = r"A:\some_folder\some_file.txt"
        path_b = "/Volumes/A/some_folder/some_file.txt"
        assert (
            convert_network_drive_path(path_a, mapping=[("A:", "/Volumes/A")]) == path_b
        )
        # test convert_network_drive_path empty
        p = {}
        assert convert_network_drive_path(str_or_path=p) == p

        # test convert_network_drive_path relative
        str_or_path = r"abc\def\hij\1.xlsx"
        assert convert_network_drive_path(str_or_path) == str_or_path
        str_or_path = "output/file.txt"
        assert convert_network_drive_path(str_or_path) == str_or_path

        # test convert_network_drive_path local_nonexists (not on a mapped drive)
        str_or_path = r"C:\some_folder\some_file.xlsx"
        expected_path = str_or_path  # C: isn't a mapped drive
        assert convert_network_drive_path(str_or_path) == expected_path

        # test convert_network_drive_path exists
        str_or_path = r"Adapter\adapter\tests\corrupt.db"
        assert convert_network_drive_path(str_or_path) == str_or_path
        str_or_path = r"test_done.db"
        assert convert_network_drive_path(str_or_path) == str_or_path
        str_or_path = "input/input_folder"
        assert convert_network_drive_path(str_or_path) == str_or_path
        str_or_path = r"output\output_folder"
        assert convert_network_drive_path(str_or_path) == str_or_path

    @patch("sys.platform", "win32")
    def test_convert_network_drive_path_win(self):
        """convert_network_drive_path() on Windows maps macOS and Linux network-drive paths
        to X:, and leaves relative and local paths unchanged.
        """
        str_or_path = "/Volumes/A/abc/c/d/1.xlsx"
        assert convert_network_drive_path(str_or_path) == r"X:\abc\c\d\1.xlsx"
        str_or_path = "/media/b/xyz/c/d/1.xlsx"
        assert convert_network_drive_path(str_or_path) == r"X:\xyz\c\d\1.xlsx"
        str_or_path = r"X:\abc\def\hij\1.xlsx"
        assert convert_network_drive_path(str_or_path) == r"X:\abc\def\hij\1.xlsx"
        str_or_path = "/Volumes/A/abc/c/d/1.xlsx"
        # test backwards compatibility
        assert (
            convert_network_drive_path(str_or_path, mapping=[("X:", "/Volumes/A")])
            == r"X:\abc\c\d\1.xlsx"
        )
        str_or_path = r"X:\abc\def\hij\1.xlsx"
        assert (
            convert_network_drive_path(str_or_path, mapping=[("X:", "/Volumes/A")])
            == r"X:\abc\def\hij\1.xlsx"
        )
        path_a = r"A:\some_folder\some_file.txt"
        path_b = "/Volumes/A/some_folder/some_file.txt"
        assert (
            convert_network_drive_path(path_b, mapping=[("A:", "/Volumes/A")]) == path_a
        )
        # test convert_network_drive_path empty
        p = {}
        assert convert_network_drive_path(str_or_path=p) == p

        # test convert_network_drive_path relative
        str_or_path = r"abc\def\hij\1.xlsx"
        assert convert_network_drive_path(str_or_path) == str_or_path
        str_or_path = "output/file.txt"
        assert convert_network_drive_path(str_or_path) == str_or_path

        # test convert_network_drive_path local_nonexists (not on a mapped drive)
        str_or_path = r"C:\some_folder\some_file.xlsx"
        expected_path = str_or_path  # C: isn't a mapped drive
        assert convert_network_drive_path(str_or_path) == expected_path

        # test convert_network_drive_path exists
        str_or_path = r"Adapter\adapter\tests\corrupt.db"
        assert convert_network_drive_path(str_or_path) == str_or_path
        str_or_path = r"test_done.db"
        assert convert_network_drive_path(str_or_path) == str_or_path
        str_or_path = "input/input_folder"
        assert convert_network_drive_path(str_or_path) == str_or_path
        str_or_path = r"output\output_folder"
        assert convert_network_drive_path(str_or_path) == str_or_path

    @patch("sys.platform", "linux")
    def test_convert_network_drive_path_lin(self):
        """convert_network_drive_path() on Linux maps Windows and macOS network-drive paths
        to /media/b, and leaves relative and local paths unchanged.
        """
        str_or_path = "/Volumes/A/abc/c/d/1.xlsx"
        assert convert_network_drive_path(str_or_path) == "/media/b/abc/c/d/1.xlsx"
        str_or_path = "/media/b/xyz/c/d/1.xlsx"
        assert convert_network_drive_path(str_or_path) == "/media/b/xyz/c/d/1.xlsx"
        str_or_path = r"X:\abc\def\hij\1.xlsx"
        assert convert_network_drive_path(str_or_path) == "/media/b/abc/def/hij/1.xlsx"
        # test backwards compatibility this should not even happen since it was not supported

        # test convert_network_drive_path empty
        p = {}
        assert convert_network_drive_path(str_or_path=p) == p

        # test convert_network_drive_path relative
        str_or_path = r"abc\def\hij\1.xlsx"
        assert convert_network_drive_path(str_or_path) == str_or_path
        str_or_path = "output/file.txt"
        assert convert_network_drive_path(str_or_path) == str_or_path

        # test convert_network_drive_path local_nonexists (not on a mapped drive)
        str_or_path = r"C:\some_folder\some_file.xlsx"
        expected_path = str_or_path  # C: isn't a mapped drive
        assert convert_network_drive_path(str_or_path) == expected_path

        # test convert_network_drive_path exists
        str_or_path = r"Adapter\adapter\tests\corrupt.db"
        assert convert_network_drive_path(str_or_path) == str_or_path
        str_or_path = r"test_done.db"
        assert convert_network_drive_path(str_or_path) == str_or_path
        str_or_path = "input/input_folder"
        assert convert_network_drive_path(str_or_path) == str_or_path
        str_or_path = r"output\output_folder"
        assert convert_network_drive_path(str_or_path) == str_or_path

    @pytest.mark.parametrize("platform", ["darwin", "linux", "win32"])
    def test_convert_network_drive_path_keeps_unmapped_absolute_path(self, platform):
        """convert_network_drive_path() leaves an absolute POSIX path that isn't under a
        mapped mount point unchanged, even if it doesn't exist yet.
        """
        path = "/nonexistent_adapter_folder/new_output/file.csv"

        with patch("sys.platform", platform):
            assert convert_network_drive_path(path) == path

    @pytest.mark.parametrize("platform", ["darwin", "linux", "win32"])
    @pytest.mark.parametrize(
        "path",
        [
            r"C:\Users\someone\AppData\Local\Temp\new_output\file.csv",
            "D:/data/new_output/file.csv",
        ],
    )
    def test_convert_network_drive_path_keeps_unmapped_drive_path(self, platform, path):
        """convert_network_drive_path() leaves an absolute Windows path on a drive that
        isn't mapped (e.g. a local C: drive) unchanged, even if it doesn't exist yet.
        """
        with patch("sys.platform", platform):
            assert convert_network_drive_path(path) == path

    def test_get_mount_point_len(self):
        """get_mount_point_len() returns the length of the path's mount point, or 0."""
        assert (
            get_mount_point_len(
                mapping={"win32": "X:", "darwin": "/Volumes/A", "linux": "/media/b"},
                str_or_path=r"X:\Abc\1.txt",
            )
            == 2
        )
        assert (
            get_mount_point_len(
                mapping={"win32": "X:", "darwin": "/Volumes/A", "linux": "/media/b"},
                str_or_path="/Volumes/A/abc/c/d/1.xlsx",
            )
            == 10
        )
        # no matching mount point
        assert (
            get_mount_point_len(
                mapping={"win32": "X:", "darwin": "/Volumes/A", "linux": "/media/b"},
                str_or_path="/home/user/1.txt",
            )
            == 0
        )

    @patch("sys.platform", "linux")
    def test_compare_output(self):
        """convert_network_drive_path() with a custom mapping converts an X: path for Linux."""
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
        assert dir2 == "/media/Abc/First_Level/Second_Level/Third_Level/input"

    @patch("sys.platform", "darwin")
    def test_compare_output2(self):
        """convert_network_drive_path() with a custom mapping converts an X: path for macOS."""
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
        assert dir2 == "/Volumes/Abc/First_Level/Second_Level/Third_Level/input"

    def test_process_column_labels(self):
        """process_column_labels() strips string labels and collapses repeated spaces,
        leaving other labels unchanged.
        """
        assert process_column_labels([" a   b ", "c ", 1, None]) == [
            "a b",
            "c",
            1,
            None,
        ]

    def test_mark_time(self):
        """mark_time() returns `<prefix>_<timestamp>` in the short or long format, and
        raises ValueError for any other format.
        """
        assert re.search(
            r"adapter_\d{6}_\d{4}", mark_time(prefix="adapter", ts_format="short")
        )
        assert re.search(
            r"adapter2_\d{4}_\d{2}_\d{2}_\d{2}h_\d{2}m",
            mark_time(prefix="adapter2", ts_format="long"),
        )
        assert len(mark_time(ts_format="short")) == len("_220808_1051")
        assert len(mark_time(ts_format="long")) == len("_2022_08_08_10h_51m")
        with pytest.raises(ValueError):
            mark_time(ts_format="str is not long")
