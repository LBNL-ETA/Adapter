import os
import re
import sys
from datetime import datetime
from pathlib import PureWindowsPath, PurePosixPath


def process_column_labels(list_of_labels):
    """Removes undesired spaces.

    Parameters:

        list_of_labels: list
            list with column labels

    Returns:

        list_of_cleaned_labels: list
            A list with cleaned lables
    """
    list_of_cleaned_labels = [
        re.sub(" +", " ", lbl.strip()) if lbl is str else lbl
        for lbl in list_of_labels
    ]

    return list_of_cleaned_labels


def convert_network_drive_path(
    str_or_path,
    mapping={"win32": "X:", "darwin": "/Volumes/A", "linux": "/media/b"},
):
    """
    Convert network drive paths from those formatted for one OS into those formatted for another. (works for Windows,
    OSX, Linux)
    If a string that doesn't seem to represent a path in the other OS is given, it will be returned unchanged.

    Parameters:
        str_or_path: str
            string holding a filepath.

        mapping: dict
            OS, mount point pair.

    Returns:
        str_or_path: str
            string holding a converted filepath based on the mapping, or original in the case that no mapped network
            drive was found.

    Raises:
        Exception: When no mapping is given or running on an unsupported OS
    """
    # backwards compatibility
    if not isinstance(mapping, dict):
        # automatically assume list of tuples
        os_mapping = {
            "win32": mapping[0][0],
            "darwin": mapping[0][1],
        }
        mapping = os_mapping
    if not isinstance(str_or_path, str):
        return str_or_path
    if not (str_or_path[0] == "/" or ":" in str_or_path):
        # return if it's relative.
        # Note: either os.path nor pathlib work correctly
        return str_or_path
    if mapping[sys.platform] in str_or_path:
        # return if path is already for the current OS
        return str_or_path
    if os.path.exists(str_or_path):
        return str_or_path
    if os.getcwd() in str_or_path:
        # return if it's a local relative path
        return str_or_path
    if ":" in str_or_path:
        # create win path
        i = 1
        if ":\\" in str_or_path or ":/" in str_or_path:
            i = 2
            # create win path
        file_path = PureWindowsPath(str_or_path[str_or_path.index(":") + i :])
    else:
        file_path = PurePosixPath(
            str_or_path[get_mount_point_len(mapping, str_or_path) + 1 :]
        )
    if sys.platform == "win32":
        # convert to current system's mount point when mount point and sys not the same
        return str(PureWindowsPath(mapping[sys.platform]).joinpath(file_path))
    elif sys.platform == "darwin" or sys.platform == "linux":
        return str(PurePosixPath(mapping[sys.platform]).joinpath(file_path))
    else:
        raise IOError(f"Not supported OS: {sys.platform}!")


def get_mount_point_len(mapping: dict, str_or_path: str) -> int:
    """Get the length of the current mount point.
    For example, get_mount_point_len(mapping={'win32': 'X:',
    'darwin': '/Volumes/A', 'linux': '/media/b'}, str_or_path=r'X:\Abc\1.txt') => 2.
    get_mount_point_len(mapping={'win32': 'X:',
    'darwin': '/Volumes/A', 'linux': '/media/b'}, str_or_path='/Volumes/A/1.txt') => 10

    Parameters:
        mapping: dict
            A OS and mount_point pair. For example, {'win32': 'X:', 'darwin': '/Volumes/A', 'linux': '/media/b'}
        str_or_path: str
            A path str. For example, 'X:\Abc\1.txt'

    Returns:
            the length of the mount point, or 0 when no match found
    """
    for v in mapping.values():
        if v.upper() == (str_or_path[: len(v)]).upper():
            return len(v)
    return 0


def user_select_file(user_message="", mul_fls=False):
    """Prompts the user to navigate and select a desired
    input file, as needed for a specific calculation.

    Parameters:

        user_message: str
            A string message to the user selecting the file
            Default: empty string

        mul_fls: boolean
            Select multiple files
            Default: False

    Returns:

        fpath: string
            Fullpath to the selected input file, or,
            in case of multiple file selection,
            the selected input folder path holding the files.
    """

    # case for Windows
    if sys.platform.lower().startswith("win"):

        print(user_message)
        import win32ui, win32con

        # For multiple files replace 0 with win32con.OFN_ALLOWMULTISELECT below
        if mul_fls:
            dial_flg = win32con.OFN_ALLOWMULTISELECT
        else:
            dial_flg = 0

        fd = win32ui.CreateFileDialog(1, None, None, dial_flg)

        fd.SetOFNTitle(user_message)
        if fd.DoModal() == win32con.IDCANCEL:
            sys.exit(1)

        # file_name = fd.GetFileName()
        fpath = fd.GetPathName()

        return fpath

    # case for OSX
    elif sys.platform.lower() == "darwin":

        print(
            user_message
            + " (You may have to search for the file prompt window)"
        )
        from tkinter import filedialog as fd

        if mul_fls:
            fpath = fd.askdirectory(title=user_message)

        else:
            fpath = fd.askopenfilename(
                title=user_message,
                filetypes=[("Excel", "*.xlsx *.xls"), ("Database", "*.db")],
            )

        return fpath


def mark_time(prefix: str = "", ts_format: str = "short") -> str:
    """This method creates a string using prefix string and a timestamp.

    Parameters
    ----------
    prefix : str
        The prefix to use in the return string. e.g. "adapter"
    ts_format : str
        The timestamp format to use in the return string. e.g. 'short', 'long'

    Returns
    -------
    str
        A string with a timestamp. e.g. "adapter_2022_08_08_10h_51m".

    Raises
    ------
    ValueError
        If `ts_format` is neither 'short' nor 'long'.

    Examples
    --------
    >>> mark_time(prefix="adapter")
    "adapter_220808_1051"
    >>> mark_time(prefix="adapter", ts_format='short')
    "adapter_220808_1051"
    >>> mark_time(prefix="adapter",ts_format="long")
    "adapter_2022_08_08_10h_51m"

    """
    if ts_format == "short":
        return f'{prefix}_{datetime.now().strftime("%y%m%d_%H%M")}'
    elif ts_format == "long":
        return f'{prefix}_{datetime.now().strftime("%Y_%m_%d_%Hh_%Mm")}'
    else:
        raise ValueError("Unsupported timestamp format!")
