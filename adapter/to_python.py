import numpy as np

from adapter.comm.xlwings_tools import Book, xl2pd, pd2xl
from adapter.comm.sql import Sql
import re, sys

import logging

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


from pdb import set_trace as bp


class Excel(object):
    """Loads bulk named tables
    and ranges from .xlsx to python as
    a dictionary of dataframes.

    Parameters:

        file_path: str
            Path to an excel sheet
    """

    def __init__(self, file_path):
        converted_fpath = Toolbox.convert_network_drive_path(file_path)
        
        self.wb = Book(converted_fpath)
        self.file_path = converted_fpath

        log.info("Connected to: {}".format(converted_fpath))

    def load(self, data_object_names=None, kind="all"):
        """Opens the file provided
        through file_path, loads
        all or a subset of tables
        and named ranges
        available in the file and
        converts to a python format.

        Parameters:

            data_object_names: list
                List of string data object names
                to load. Data objects can be 
                named tables and named ranges, see 
                'type' kwarg for details. 
                Default: None means
                that all data objects found in the
                input file get loaded.

            kind: str
                'tables' : gets only named tables
                'ranges' : gets only named ranges
                'all' : gest both named tables 
                and named ranges

        Returns:

            dict_of_dfs: dict of dataframes
                Python dictionary with table name
                keys and input table values.
        """
        # *mig please make corresponding
        # docstrings for the analoguos
        # methods in other classes in this
        # file
        dict_of_dfs = self.get_named_data_objects(data_object_names, kind=kind)

        # @lz - this should be uncommented after
        # you implement the method

        # dict_of_dfs.update(
        #     self.get_named_ranges(table_names))

        return dict_of_dfs

    def get_named_data_objects(self, data_object_names, kind="all"):
        """Grabs data defined as excel tables.

        Parameters:

            data_object_names: list
                List of string data object names
                to load. Data objects can be 
                named tables and named ranges, see 
                'type' kwarg for details. 
                Default: None means
                that all data objects found in the
                input file get loaded.

            kind: str
                'tables' : gets only named tables
                'ranges' : gets only named ranges
                'all' : gest both named tables 
                and named ranges

        Returns:

            dict_of_dfs: dict of dataframes
                Python dictionary with table name/
                named range as keys and contents of 
                the corresponding named data object
                 values.
        """
        if kind == "tables":
            # grab all the input tables/named ranges
            all_input_names = self.wb.tables

        if kind == "ranges":
            all_input_names = {
                x.name: x
                for x in self.wb.names
                if "_FilterDatabase" not in x.name
            }

        if kind == "all":
            all_input_tables = self.wb.tables
            all_input_ranges = {
                x.name: x
                for x in self.wb.names
                if "_FilterDatabase" not in x.name
            }

            all_input_tables.update(all_input_ranges)

            all_input_names = all_input_tables.copy()

        elif kind not in ["all", "ranges", "tables"]:
            msg = "An unsupported value provided for kwarg kind {}."
            log.error(msg.format(kind))
            raise ValueError

        # initiate dictionaries of input table dataframes
        # and populate
        dict_of_dfs = dict()

        if len(all_input_names.keys()) > 0:
            if type(data_object_names) == list:
                for data_object_name in data_object_names:
                    if data_object_name not in all_input_names.keys():
                        msg = "{} not found in the input file {}."
                        log.error(msg.format(data_object_name, self.file_path))
                        raise ValueError

            elif (data_object_names is None) or (data_object_names is np.nan):
                data_object_names = all_input_names.keys()

            else:
                msg = "Unsupported type ({}) passed for table names, {}."
                log.error(msg.format(type(table_names), table_names))
                raise ValueError

            try:
                for data_object_name in data_object_names:
                    # prepare labels (strip extra spaces)
                    dict_of_dfs[data_object_name] = self.wb.named_range_to_df(
                        all_input_names[data_object_name], verbose=True
                    )
                    dict_of_dfs[
                        data_object_name
                    ].columns = Toolbox().process_column_labels(
                        dict_of_dfs[data_object_name].columns
                    )

                msg = "Read in input tables from {}."
                log.info(msg.format(self.file_path))
            except:
                # more detailed error data should come from xlwings_tools
                msg = "Failed to read input tables from {}."

                log.error(msg.format(self.file_path))
                raise ValueError

            msg = "Loaded named tables from {}."
            log.info(msg.format(self.file_path))

        else:
            msg = (
                "Neither named tables nor named ranges found in "
                "the input file {}."
            )
            log.info(msg.format(self.file_path))

        return dict_of_dfs


class Db(object):
    """Loads tables from a database to python
    as a dictionary of dataframes.

    Parameters:

        file_path: str
            Path to an db file
    """

    def __init__(self, file_path):
        converted_fpath = Toolbox.convert_network_drive_path(file_path)

        self.db = Sql(converted_fpath)
        self.file_path = converted_fpath

    def load(self, table_names=None):
        """Loads tables

        Parameters:

            table_names: list
                List of table names to load.
                Default: None = load all tables
        """
        try:
            all_dict_of_dfs = self.db.tables2dict(close=True)

            dict_of_dfs = dict()

            if len(all_dict_of_dfs.keys()) > 0:

                if type(table_names) == list:

                    for table_name in table_names:

                        if table_name not in all_dict_of_dfs.keys():
                            msg = "{} not found in the input file {}."
                            log.error(msg.format(table_name, self.file_path))
                            raise ValueError

                        else:
                            dict_of_dfs[table_name] = all_dict_of_dfs[
                                table_name
                            ]
                else:
                    dict_of_dfs = all_dict_of_dfs

        except:
            msg = "Failed to read input tables from {}."
            log.error(msg.format(self.inpath))
            raise ValueError

        return dict_of_dfs


class Toolbox(object):
    def process_column_labels(self, list_of_labels):
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

    @staticmethod
    def convert_network_drive_path(str_or_path,mapping = [("X:","/Volumes/my_folder")]):
        """Convert network drive paths from those formatted for one OS into those formatted for another. (works for Windows <-> OSX)
        If a string that doesn't seem to represent a path in the other OS is given, it will be returned unchanged.

        Args:
            str_or_path (str): string holding a filepath. 
            mapping (list): list of 2-tuples where 0th entry of each tuple is the name of a windows network drive location (e.g. "A:") and the 1st entry is OSX network drive location (e.g. "/Volumes/A"). Defaults to [("X:","/Volumes/my_folder")].

        Raises:
            Exception: When no mapping is given
        """            
        if mapping:
            windows_drive_names = [pair[0].rstrip('\\') for pair in mapping]
            osx_drive_names = [pair[1].rstrip('/') for pair in mapping]
        else:
            raise Exception("No network drive mappings given")

        if sys.platform.startswith('win'):
            for i,name in enumerate(osx_drive_names):
                if str_or_path.startswith(name):
                    str_or_path = str_or_path.replace(name,windows_drive_names[i]).replace('/','\\')
                    break

        elif sys.platform.startswith('darwin'):
            for i,name in enumerate(windows_drive_names):
                if str_or_path.startswith(name):
                    str_or_path = str_or_path.replace('\\','/').replace(name,osx_drive_names[i])
                    break
            
        return str_or_path
