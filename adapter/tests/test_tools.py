from unittest import TestCase
from unittest.mock import patch

from adapter.comm.tools import convert_path


class Test(TestCase):
    def setUp(self) -> None:
        self.win_dir = "a:\\b\\c\\d\\e\\f.gh"
        self.linux = "/media/forecast/b/c/d/e/f.gh"
        self.osx = "/Volumes/ees/b/c/d/e/f.gh"

    def tearDown(self) -> None:
        del self.win_dir
        del self.linux
        del self.osx

    @patch('sys.platform', 'freebsd7')
    def test_unix(self):
        with self.assertRaises(IOError):
            convert_path(self.win_dir)

    @patch('sys.platform', 'linux')
    def test_linux(self):
        self.assertEqual(self.linux, convert_path(self.win_dir))

    @patch('sys.platform', 'darwin')
    def test_osx(self):
        self.assertEqual(self.osx, convert_path(self.win_dir))

    @patch('sys.platform', 'win32')
    def test_win(self):
        self.assertEqual(self.win_dir, convert_path(self.win_dir))
