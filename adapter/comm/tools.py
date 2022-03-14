import os
import re
import sys
from pathlib import PurePath, PureWindowsPath, PurePosixPath


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
    if (
        (not isinstance(str_or_path, str))
        or os.path.isfile(str_or_path)
        or (not (str_or_path[0] == "/" or ":" in str_or_path))
    ):
        # return if abs file exists or path is absolute, return if it's relative.
        # Note: either os.path nor pathlib work correctly
        return str_or_path
    if not mapping:
        raise Exception("No network drive mappings given")
    if mapping[sys.platform] in str_or_path:
        # return if path is already for the current OS
        return str_or_path
    mp = get_mount_point_len(mapping, str_or_path)
    if mp == 0:
        raise IOError(
            f"the given path: {str_or_path} doesn't match any of OS mappings! If you work with a local dir, "
            f"set isLocal arg as IO(isLocal=True) or i_o.write(isLocal=True)"
        )
    if ":" in str_or_path:
        file_path = PureWindowsPath(str_or_path[mp + 1 :])
    else:
        file_path = PurePosixPath(str_or_path[mp + 1 :])
    if sys.platform == "win32":
        # convert to current system's mount point when mount point and sys not the same
        return str(PureWindowsPath(mapping[sys.platform]).joinpath(file_path))
    elif sys.platform == "darwin" or sys.platform == "linux":
        return str(PurePosixPath(mapping[sys.platform]).joinpath(file_path))
    else:
        raise IOError(f"Not supported OS: {sys.platform}!")


def get_mount_point_len(mapping: dict, str_or_path: str) -> int:
    """Get the length of the current mount point.

    Parameters:
        mapping: dict
            A OS and mount_point pair. For example, {'win32': 'X:', 'darwin': '/Volumes/A', 'linux': '/media/b'}
        str_or_path: str
            A path str. For example, 'X:\Abc\1.txt'

    Returns:
            the length of the mount point
    """
    mp = 0
    for v in mapping.values():
        if v.upper() == (str_or_path[: len(v)]).upper():
            return len(v)
    return mp


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
