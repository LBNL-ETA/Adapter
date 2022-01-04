import logging
import os
import traceback

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, MetaData

from adapter.comm.excel import Book
from adapter.comm.tools import process_column_labels

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class Excel(object):
    """Loads bulk named tables
    and ranges from .xlsx to python as
    a dictionary of dataframes.

    Parameters:

        file_path: str
            Path to an excel sheet

        pre_existing_keys: dictionary key index
            Keys is the previously loaded
            dictionary of dataframes
    """

    def __init__(self, file_path, pre_existing_keys=None):

        self.wb = Book(file_path)
        self.file_path = file_path
        self.pre_existing_keys = pre_existing_keys

        log.info("Connected to: {}".format(file_path))

    def load(
            self,
            data_object_names=None,
            kind="all",
    ):
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
        dict_of_dfs = self.get_named_data_objects(data_object_names, kind=kind)

        return dict_of_dfs

    def get_named_data_objects(self, data_object_names, kind="all"):
        """Grabs data defined as excel tables, named ranges, or both.

        Parameters:

            data_object_names: list or None
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
            all_input_objects = self.wb.tables

        if kind == "ranges":
            all_input_objects = {
                x.name: x
                for x in self.wb.names
                if "_FilterDatabase" not in x.name and "_xlfn." not in x.name
            }

        if kind == "all":
            all_input_tables = self.wb.tables
            all_input_ranges = {
                x.name: x
                for x in self.wb.names
                if "_FilterDatabase" not in x.name and "_xlfn." not in x.name
            }

            all_input_tables.update(all_input_ranges)

            all_input_objects = all_input_tables.copy()

        elif kind not in ["all", "ranges", "tables"]:
            msg = "An unsupported value provided for kwarg kind {}."
            log.error(msg.format(kind))
            raise ValueError

        if self.pre_existing_keys is not None:
            Debugger.check_for_duplicates(
                self.pre_existing_keys, all_input_objects.keys()
            )

        # initiate dictionaries of input table dataframes
        # and populate
        dict_of_dfs = dict()

        if len(all_input_objects.keys()) > 0:

            if type(data_object_names) == list:
                for data_object_name in data_object_names:
                    if data_object_name not in all_input_objects.keys():
                        msg = "{} not found in the input file {}."
                        log.error(msg.format(data_object_name, self.file_path))
                        raise ValueError

            elif (
                    (data_object_names is None)
                    or (data_object_names is np.nan)
                    or (np.isnan(data_object_names))
            ):
                data_object_names = all_input_objects.keys()

            else:
                msg = "Unsupported type ({}) passed for table names, {}."
                # log.error(msg.format(type(table_names), table_names))
                raise ValueError

            try:

                for data_object_name in data_object_names:

                    try:
                        # prepare labels (strip extra spaces)
                        dict_of_dfs[
                            data_object_name
                        ] = self.wb.named_range_to_df(
                            all_input_objects[data_object_name],
                            verbose=True,
                        )

                        dict_of_dfs[
                            data_object_name
                        ].columns = process_column_labels(
                            dict_of_dfs[data_object_name].columns
                        )

                    except:
                        msg = (
                            "Failed to read input table named {}"
                            " from input file {}. "
                            "If the data contained in the table "
                            "is needed in the analysis please attempt"
                            " to rename the table/range using strings and numerals "
                            "and/or further check the data range or table "
                            "definition."
                        )

                        log.warning(
                            msg.format(data_object_name, self.file_path)
                        )
                        raise ValueError

                msg = "Read in input tables and ranges from {}."
                log.info(msg.format(self.file_path))

            except:
                msg = "Failed to read input tables from {}."

                log.error(msg.format(self.file_path))
                raise ValueError

        else:
            msg = (
                "Neither named tables nor named ranges found in "
                "the input file {}."
            )
            log.info(msg.format(self.file_path))

        return dict_of_dfs


class Db(object):
    """Loads tables from a sqlite3 database into python
    as a dictionary of dataframes.

    Parameters:

        file_path: str
            Path to a sqlite db file

        pre_existing_keys: dictionary key index
            Keys is the previously loaded
            dictionary of dataframes
    """

    def __init__(self, file_path, pre_existing_keys=None):
        self.file_path = file_path
        self.pre_existing_keys = pre_existing_keys

    def load(self, table_names=None):
        """Loads tables from a sqlite file

        Parameters:

            table_names: list
                List of table names to load. Assuming the given tables always exist in the db file
                Default: None = load all tables
        Notes
        -----
        input file checking comment out for now because it crashes LCC. this section should be uncommented
        once LCC fixes the issue.
        """
        # if not os.path.exists(self.file_path):
        #     # check if file exists
        #     raise ImportError(f'Cannot find {self.file_path}')
        con_str = f'sqlite+pysqlite:///{self.file_path}'
        engine = create_engine(con_str)
        metadata = MetaData()
        metadata.reflect(bind=engine)

        keys = metadata.tables.keys()
        if len(keys) == 0:
            # check database integrity
            raise IOError(
                f'0 table found in the database file! The input file: {self.file_path} may be unsupported or corrupted')
        if self.pre_existing_keys is not None:
            Debugger.check_for_duplicates(
                self.pre_existing_keys, keys
            )
            # skip pre_existing_keys
        if table_names is not None:
            # only import given table names
            keys = keys & set(table_names)
        dict_of_dfs = dict()
        for t in keys:
            dict_of_dfs[t] = pd.read_sql_table(f'{t}', con=con_str)
        return dict_of_dfs


class Db_sqlalchemy(object):
    """Loads tables from a database using sqlalchemy to python
    as a dictionary of dataframes.

    Parameters:

        file_path: str
            Path to an db file

        pre_existing_keys: dictionary key index
            Keys is the previously loaded
            dictionary of dataframes
    """

    def __init__(self, file_path, pre_existing_keys=None):
        # Imports in this class so if you don;t need them it will still work
        try:
            from adapter.Secret import database_credentials
        except:
            raise ValueError(
                """You must define your "Secret.py" file within the adapter folder.  
                                Replace the example "Secret_example.py" with your credentials"""
            )

        self.cxn_str = (
                "postgresql://"
                + database_credentials["Username"]
                + ":"
                + database_credentials["Password"]
                + "@"
                + file_path
        )
        self.engine = create_engine(self.cxn_str)
        self.file_path = file_path
        self.pre_existing_keys = pre_existing_keys

    def load(self, table_names=None):
        """Loads tables

        Parameters:

            table_names: list
                List of table names to load.
                Default: None = load all tables
        """

        try:
            dict_of_dfs = dict()
            for table_name in table_names:
                sql_string = "SELECT * FROM {table}".format(table=table_name)
                dict_of_dfs[table_name] = pd.read_sql(
                    con=self.engine, sql=sql_string
                )

            if self.pre_existing_keys is not None:
                Debugger.check_for_duplicates(
                    self.pre_existing_keys, dict_of_dfs.keys()
                )

        except:
            traceback.print_exc()
            msg = "Failed to read input tables from {}."
            log.error(msg.format(self.file_path))
            raise ValueError

        return dict_of_dfs


class Debugger(object):
    @staticmethod
    def check_for_duplicates(pre_existing_keys, table_names):
        """Checks if among data tables already
        added to the dict_of_dfs there exists
        a table of a same name with any of the
        tables being added to the dict_of_dfs.

        Parameters:

            pre_existing_keys: dictionary key index
                Keys is the previously loaded
                dictionary of dataframes

            table_names: list or string
                List of table names; or a
                single string table name.
        """
        msg = (
            "An identically name table/range"
            " {} was already read in. "
            "Please rename all tables and ranges"
            " in the inputs uniquely. "
            "It may be that the same-named "
            "table came from a different input file."
        )

        if not isinstance(table_names, str):
            for name in table_names:
                if name in pre_existing_keys:
                    log.error(msg.format(name))
                    raise ValueError(msg.format(name))

        else:
            try:
                if pre_existing_keys is not None:
                    if table_names in pre_existing_keys:
                        # log.error(msg.format(name))
                        raise ValueError
            except:
                msg = "Unexpected table_name ({}) format."
                log.error(msg.format(table_names))
