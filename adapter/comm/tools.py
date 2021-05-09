import sys, re


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
