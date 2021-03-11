import numpy as np

from adapter.comm.xlwings_tools import Book, xl2pd, pd2xl
from adapter.comm.sql import Sql
import re

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
        self.wb = Book(file_path)
        self.file_path = file_path

        log.info("Connected to: {}".format(file_path))

    def has_table(self,table_name):
        '''
        Checks whether a specific table is in the workbook, by name

        Parameters:
            table_name: str
                Name of the table whose existence is being queried

        Returns:
            True/False
                Whether or not the table exists in this workbook.
        '''
        # inefficient: queries all table names to check if one is in the whole list.
        return table_name in self.wb.tables

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
        # docstrings for the analogous
        # methods in other classes in this
        # file 
        dict_of_dfs = self.get_named_data_objects(
            data_object_names, kind=kind)

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
                if "_FilterDatabase" not in x.name and
                "_xlfn." not in x.name
            }

        if kind == "all":
            all_input_tables = self.wb.tables
            all_input_ranges = {
                x.name: x
                for x in self.wb.names
                if "_FilterDatabase" not in x.name and
                "_xlfn." not in x.name
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
                        all_input_names[data_object_name], verbose=True,
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
        self.db = Sql(file_path)
        self.file_path = file_path

    def has_table(self,table_name):
        '''
        Check whether or not a table exists in this database

        Parameters:
            table_name: str
                The table name whose existence you're querying for

        Returns:
            True/False
                Whether or not this database has the table
        '''
        return self.db.has_table(table_name)

    def load(self, table_names=None, close = True):
        """Loads tables

        Parameters:

            table_names: list
                List of table names to load.
                Default: None = load all tables
        """
        try:
            all_dict_of_dfs = self.db.tables2dict(close=close)

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

    def write_df(self,df,table_name,close=False,**kwargs):
        '''
        Write a df to self.db under the name <table_name>.

        Parameters:
            df: pd.DataFrame
                Table to write

            table_name: str
                Name under which table will be saved in self.db

            kwargs: dict
                Handed as keyword arguments to pd.to_sql

        Returns:
            True or None
                True if the execution of the save succeeded. 
        '''
        return self.db.pd2table(df,table_name, close = close, **kwargs)

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
