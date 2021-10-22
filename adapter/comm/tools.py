import sys, re, os


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
    str_or_path, mapping=[("X:", "/Volumes/my_drive")]
):
    """
    Convert network drive paths from those formatted for one OS into those formatted for another. (works for Windows <-> OSX)
    If a string that doesn't seem to represent a path in the other OS is given, it will be returned unchanged.

    Parameters:
        str_or_path: str
            string holding a filepath.

        mapping: list
            list of 2-tuples where 0th entry of each tuple is the name of a windows network drive location (e.g. "A:") and the 1st entry is OSX network drive location (e.g. "/Volumes/A"). Defaults to [("X:","/Volumes/my_folder")].

    Returns:
        str_or_path: str
            string holding a converted filepath, or original in the case that no mapped network drive was found.

    Raises:
        Exception: When no mapping is given
    """
    if not isinstance(str_or_path, str):
        return str_or_path

    if mapping:
        windows_drive_names = [pair[0].rstrip("\\") for pair in mapping]
        osx_drive_names = [pair[1].rstrip("/") for pair in mapping]
    else:
        raise Exception("No network drive mappings given")

    if sys.platform.startswith("win"):
        for i, name in enumerate(osx_drive_names):
            if str_or_path.startswith(name):
                str_or_path = str_or_path.replace(
                    name, windows_drive_names[i]
                ).replace("/", "\\")
                break

    elif sys.platform.startswith("darwin"):
        for i, name in enumerate(windows_drive_names):
            if str_or_path.startswith(name):
                str_or_path = str_or_path.replace("\\", "/").replace(
                    name, osx_drive_names[i]
                )
                break

    return str_or_path


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
                title=user_message, filetypes=[("Excel", "*.xlsx *.xls"),("Database", "*.db")]
            )

        return fpath

