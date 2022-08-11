import logging
import os
import traceback
import openpyxl

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, MetaData

from adapter.comm.tools import process_column_labels

import logging

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class Excel(object):
    """Loads bulk named tables
    and ranges from excel to python as
    a dictionary of dataframes.

    This Class replaces the old Excel Class

    Parameters:

        file_path: str
            Path to an excel sheet where input
            tables/named ranges need to be loaded.
            No data is read in when None

        pre_existing_keys: dictionary key index
            Keys is the previously loaded
            dictionary of dataframes
    """

    def __init__(self, file_path, pre_existing_keys=None):
        self.file_path = file_path
        self.wb = openpyxl.load_workbook(
            self.file_path, data_only=True, read_only=False, keep_vba=False
        )
        self.pre_existing_keys = pre_existing_keys

        log.info("Connected to: {}".format(self.file_path))

    def load(self, data_object_names=None, kind="all"):
        """Grabs all or a subset of named tables and ranges 
        found in excel file as a dictionary of dataframes

        This function replaces the older version of Excel.load
        
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

            dict_of_dfs: dictionary of dataframes
                Python dictionary with table name/
                named range as keys and contents of
                the corresponding named data object
                values
        """
        # check if any name in data_object_names not in excel file
        all_input_ranges = {object_range.name for object_range in self.wb.defined_names.definedName}
        all_input_tables = {object_table for ws in self.wb.worksheets for object_table in ws.tables.keys()}
        all_input_objects = all_input_ranges | all_input_tables

        if isinstance(data_object_names, list):
            data_object_names = set(data_object_names)
            missings = data_object_names - all_input_objects
            if len(missings) > 0:
                raise ValueError(f"{missings} not found in the input file {self.file_path}.")

        elif data_object_names is None or np.isnan(data_object_names):
            data_object_names = all_input_objects

        else:
            raise ValueError(f"Unsupported type ({type(data_object_names)}) passed for data object names {data_object_names}.")

        if len(all_input_objects) == 0:
            msg = (
                "Neither named tables nor named ranges found in "
                "the input file {}."
            )
            log.info(msg.format(self.file_path))

        dict_of_dfs = dict()
        if kind not in ["all", "ranges", "tables"]:
            raise ValueError(f"An unsupported value provided for kwarg kind {kind}.")
        # get named ranges
        if kind in ['all', 'ranges']:
            try:
                for name in data_object_names & all_input_ranges:
                    dict_of_dfs[name] = self.get_named_data_object(name)
            except:
                msg = (
                "Failed to read input named range {}"
                " from input file {}. "
                "If the data contained in the table "
                "is needed in the analysis please attempt"
                " to rename the table/range using strings and numerals "
                "and/or further check the data range or table "
                "definition."
                )
                raise ValueError(msg.format(name, self.file_path))

        # get named tables
        if kind in ['all', 'tables']:
            try:
                for ws in self.wb.worksheets:
                    for table_name, table_range in ws.tables.items():
                        if table_name in data_object_names:
                            dict_of_dfs[table_name] = self.convert_data_object_to_df(
                                ws[table_range], table_name
                            )
            except:
                msg = (
                "Failed to read input named table {}"
                " from input file {}. "
                "If the data contained in the table "
                "is needed in the analysis please attempt"
                " to rename the table/range using strings and numerals "
                "and/or further check the data range or table "
                "definition."
                )
                raise ValueError(msg.format(table_name, self.file_path))

        if self.pre_existing_keys is not None:
            Debugger.check_for_duplicates(
                self.pre_existing_keys, dict_of_dfs.keys())

        for k, df in dict_of_dfs.items():
            # xlwings-based Excel class converted all numbers to float types.
            # The code below maintains backward compatibility
            df = df.astype(
                {
                    k: float if np.issubdtype(v, np.number) else v
                    for k, v in df.dtypes.items()
                }
            )
            df.columns = process_column_labels(df.columns)
            dict_of_dfs[k] = df

        log.info(f"Read in input named tables and ranges: {data_object_names}")

        return dict_of_dfs

    def get_named_data_object(self, data_object_name):
        """Opens excel workbook and loads all tables and
        named ranges and converts to a python format.
        range_name can be a standard Excel reference
        ('Sheet1!A2:B7') or refer to a named region
        ('my_cells').

        This function replaces the older version of
        Excel.get_named_data_object. kwarg 'kind' is deprecated

        Parameters:

            data_object_name: str
                worksheet reference to find
                a rectangular region (cell or tuple of cells)
                of data objects in workbook. Data objects
                can be named tables and named ranges

        Returns:

            df: dataframe
                named table or range in format of
                pandas dataframe read from the input workbook
        """
        if "!" in data_object_name:
            # pass a worksheet!cell reference
            ws_name, reg = data_object_name.split("!")
            if ws_name.startswith("'") and ws_name.endswith("'"):
                # optionally strip single quotes around sheet name
                ws_name = ws_name[1:-1]
        else:
            # pass a named range;
            # find the cells in the workbook
            full_range = self.wb.defined_names[data_object_name]
            if full_range is None:
                raise ValueError(f'Range "{data_object_name}" not found in workbook.')

            destinations = list(full_range.destinations)
            if len(destinations) > 1:
                raise ValueError(
                    f'Range "{data_object_name}" in contains more than one region.'
                )
            ws_name, reg = destinations[0]

        region = self.wb[ws_name][reg]
        df = self.convert_data_object_to_df(region, data_object_name)

        return df

    def convert_data_object_to_df(self, data_object, name):
        """Converts data objects defined as named ranges
        and tables in excel file into dataframes

        Parameters:

            data_object: single cell or tuple of tuple of cells
                Each cell is an openpyxl.cell.cell.Cell
                data object read from an excel worksheet

            name: str
                name of th data object

        Returns:

            df: dataframe
                named table or range in format of
                pandas dataframe read from the input workbook
        """
        if isinstance(data_object, tuple):
            df = pd.DataFrame(
                [[cell.value for cell in row] for row in data_object[1:]],
                columns=[cell.value for cell in data_object[0]],
            )
        else:  # read in scalar value
            df = pd.DataFrame([[data_object.value]], columns=[name])
        return df


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
            # check for duplicates in tables_names,
            # if table_names == None, check for duplcates for all the tables
            Debugger.check_for_duplicates(
                self.pre_existing_keys, table_names or keys
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
                dict_of_dfs[table_name] = pd.read_sql(con=self.engine, sql=sql_string)

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
