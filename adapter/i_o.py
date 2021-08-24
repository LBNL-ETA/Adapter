import os
import numpy as np
import pandas as pd

from adapter.to_python import Excel, Db, Db_sqlalchemy, Debugger
from adapter.label_map import Labels

from adapter.comm.tools import convert_network_drive_path

from datetime import datetime
import re
import sqlite3
from shutil import copy
import ntpath

import logging

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

from pdb import set_trace as bp


class IO(object):
    """Connects to the main input
    file that can be an excel sheet,
    a csv file or a database,
    loads the data, looks for
    additional input data paths
    and loops through those to
    get data as well. Saves a
    full input DB and provides the
    user with output and db paths,
    and database connections. It allows
    for large tables to be only queried and
    not loaded in python.

    Parameters:

        path : string
            Path to the initial input table. An
            initial input table can be of
            any type (.xlsx, .csv, .db) and can
            contain pointers to further input
            files. It is recommended to have
            a `run_parameters` table (see test
            folders on the master branch
            of the adapter repo for examples)
            that provides an output path and a
            version substring.

        mapping: list
            list of 2-tuples where 0th entry of each 
            tuple is the name of a windows network drive 
            location (e.g. "A:") and the 1st entry is OSX 
            network drive location (e.g. "/Volumes/A"). 
            Defaults to [("X:","/Volumes/my_folder")].

    """

    def __init__(
        self, 
        path, 
        os_mapping=[("X:", "/Volumes/my_drive")]):

        path = convert_network_drive_path(path,
            mapping = os_mapping)

        self.input_path = path

        if isinstance(path, str):
            self.input_type = self.get_file_type(path)

        # set labels
        self.la = Labels().set_labels()

    def get_file_type(self, path):
        """Extracts the file type from the fullpath.

        Parameters:

            path : string
                File path
        """
        extns = re.split("\.", path)[-1]

        # extns = ...
        file_type = ""

        if extns == "xlsx":
            file_type += "excel"

        elif (extns == "db") or (extns == "sqlite"):
            file_type += "database"

            # *mig add more file extension checks
            # as needed

        elif extns == "csv":
            file_type += "text"

        # If the path contains lbl.gov, it is likely a database that can be used with sqlalchemy
        elif "lbl.gov" in path:
            file_type += "sqlalchemy"

        else:
            msg = "Passed an unsupported input file type: {}."
            log.error(msg.format(extns))

        return file_type

    def load(
        self,
        create_db=True,
        db_flavor="sqlite",
        close_db=True,
        save_input=True,
        set_first_col_as_index=False,
        quick_db_out_filename=None,
        clean_labels=True,
        to_numeric=None,
    ):
        """Loads tables from the input file
        as a dictionary of python dataframes.

        Recognizes any special table names, such
        as:

            - `run_parameters`, that specifies the output
            path, alongside to some further analysis related
            specifiers.

            - `inputs_from_files`, that specifies a list of
            additional input files of file types: csv, excel, db.
            See examples in the test folders on the master
            branch of the adapter repo for details on the
            structure and labels of the table.

        Parameters:

            create_db: bool
                Write all tables read from input files
                into a run database

            db_flavor: string
                Database type. Currently implemented:
                'sqlite'

            close_db: bool
                True: close the database that got
                created, False: keep the database open

            save_input: bool
                Save initial input file under the output
                folder

            set_first_col_as_index: bool or list of strings
                True: Set index for all tables
                False: do not set the first column as index
                for any tables
                List of strings: List of tables that need
                their first column set as index

            quick_db_out_filename: string, defaults to None
                Output filename without the
                file extension if one does not
                want to use the version tag and outpath
                as provided in a run parameters table when
                saving a database.

                Use with caution as there is no run tag
                or timestamp included. This may be useful when
                quickly converting an excel file with tables
                and named ranges into a database.

            to_numeric: list
                List of string table names where
                values should be converted to
                numeric where possible

            clean_labels: bool
                Process table columns to remove trailing whitespaces

        Returns:

            res : dict
                Keys:

                'tables_as_dict_of_dfs' - all input
                    tables loaded in python as dictionary
                    of dataframes
                'outpath' - output folder path
                'run_tag' - version + analysis start time

                If db got written:

                'db_path' - database fullpath
                'db_conn' - database connection
        """
        dict_of_dfs = self.get_tables(self.input_path)

        # are there any further input files?
        # if that is the case, the file paths and further info
        # should be placed in an `inputs_from_files` table
        qry_flags = dict()

        if self.la["extra_files"] in dict_of_dfs.keys():

            extra_files = dict_of_dfs[self.la["extra_files"]].reset_index()

            for inx in extra_files.index:

                file_path = extra_files.loc[inx, self.la["inpath"]].strip()

                table_names = extra_files.loc[inx, self.la["tbl_nam"]]

                if isinstance(table_names, str):
                    table_names = re.split(",", table_names)
                    table_names = [i.strip() for i in table_names]

                qry_flags[file_path] = extra_files.loc[inx, self.la["query"]]

                if (qry_flags[file_path] is not None) and isinstance(
                    table_names, str
                ):

                    qry_flags[file_path] = re.split(",", qry_flags[file_path])
                    qry_flags[file_path] = [
                        i.strip() for i in qry_flags[file_path]
                    ]

                dict_of_dfs.update(
                    self.get_tables(
                        file_path,
                        table_names=table_names,
                        query_only=qry_flags[file_path],
                        pre_existing_keys=dict_of_dfs.keys(),
                    )
                )

        else:
            qry_flags = None

        # define output path for the analysis run

        if quick_db_out_filename is None:
            # look for `run_parameters` table to extract the outpath
            # and the version
            # `run_parameters` table should occur only in one
            # of the input files, and only once, so if multiple
            # run_parameters{any_text} tables are found, then
            # the first one, when names sorted alphabetically,
            # will be used

            run_params_table = []

            for key in dict_of_dfs.keys():

                if self.la["run_pars"] in key:

                    msg = "Identified run parameters table named {}"
                    log.info(msg.format(key))

                    run_params_table.append(key)

            if len(run_params_table) > 1:
                run_params_table.sort()

                msg = (
                    "Run parameters table named {} will be used to set the "
                    "outpath and the version. "
                    "Additional run parameters table(s) named: {} "
                    "will be ignored. Please make sure to remove any"
                    " unwanted run_parameters tables from the inputs."
                )

                log.warning(
                    msg.format(run_params_table[0], run_params_table[1:])
                )

            if len(run_params_table) != 0:

                outpath_base = os.path.join(
                    os.getcwd(),
                    dict_of_dfs[run_params_table[0]].loc[
                        0, self.la["outpath"]
                    ],
                )

                version = dict_of_dfs[run_params_table[0]].loc[
                    0, self.la["version"]
                ]

                if not isinstance(version, str):
                    # if it was read in as a number, as occurs in the test_input.xlsx on OSX
                    if str(version).endswith(".0"):
                        # Assume that the only case is when version "123" got read in as number "123.0"
                        # period will be removed next
                        version = str(version).rstrip("0")

                # Removing '.', '\', '/' characters from version
                # to avoid any errors during writing output
                version = re.sub("[\\\\./]", "", version)

                self.version = version

            # otherwise declare current folder + "/output" as the output
            # path
            else:
                outpath_base = os.path.join(os.getcwd(), "output")
                version = ""

            run_tag = (
                version + "_" + datetime.now().strftime("%Y_%m_%d-%Hh_%Mm")
            )

            outpath = os.path.join(outpath_base, run_tag)

        else:
            outpath = os.getcwd()
            run_tag = quick_db_out_filename

        if not os.path.exists(outpath):
            os.makedirs(outpath)

        if save_input and isinstance(self.input_path, str):
            # self.input_path
            filename = ntpath.basename(self.input_path)
            filename_extns = re.split("\.", filename)[-1]
            filename_only = re.split("\.", filename)[0]

            versioned_filename = (
                filename_only + "_" + run_tag + "." + filename_extns
            )

            copy(self.input_path, os.path.join(outpath, versioned_filename))

        if create_db == True:

            try:
                db_res = self.create_db(
                    dict_of_dfs,
                    outpath=outpath,
                    run_tag=run_tag,
                    flavor=db_flavor,
                    close=close_db,
                )
            except:
                msg = (
                    "Not able to create a db of tables "
                    "that were read in from {}."
                )

                log.error(msg.format(self.input_path))

        if set_first_col_as_index != False:
            dict_of_dfs = self.first_col_to_index(
                dict_of_dfs, table_names=set_first_col_as_index, drop=True
            )

        # value type conversion for any tables listed
        # as to_numeric and to_float
        if to_numeric is not None:
            if isinstance(to_numeric, list):
                pass
            else:
                msg = (
                    "{} passed for to_numeric kwarg."
                    "Only None or a list of strings are supported."
                )
                log.error(msg.format(to_numeric))

            for key in dict_of_dfs.keys():
                if any([key in tb_nm for tb_nm in to_numeric]):
                    dict_of_dfs[key] = dict_of_dfs[key].apply(
                        pd.to_numeric, errors="ignore", axis=1
                    )

        res = dict()
        res["tables_as_dict_of_dfs"] = dict_of_dfs

        res["outpath"] = outpath
        res["run_tag"] = run_tag

        if create_db == True:
            res.update(db_res)

        if clean_labels == True:

            input_tables_list = res["tables_as_dict_of_dfs"]

            for table in input_tables_list:

                table_columns = input_tables_list[table].columns

                clean_cols = self.process_column_labels(table_columns)
                input_tables_list[table].columns = clean_cols

            msg = "All table column labels were processed to remove undesired whitespaces."
            log.info(msg)

        return res

    def get_tables(
        self,
        file_path,
        table_names=None,
        query_only=None,
        pre_existing_keys=None,
    ):
        """Gets all tables from an input
        file. Creates a dictionary
        of pandas dataframes, with each dataframe
        corresponding to one of the input tables.
        If it is a csv file the contents
        get loaded as a single table with the
        dictionary key being the name of the
        file

        Parameters:

            file_path: str or None
                Input file path
                No data is read in when None,
                creates an empty dictionary

            query_only: str list of 'N' and 'Y', or empty cell (None)
                Default: None - all tables get
                loaded.
                Values in the list: 'N' or 'Y'

            table_names: list of str
                Tables to load. If None
                all tables get loaded (
                unless all need to be
                queried)

            pre_existing_keys: dictionary key index
                Keys is the previously loaded
                dictionary of dataframes

        Returns:

            dict_of_dfs: dict of pd dfs
                Dictionary of pandas dataframes
                containing all the tables
                from the input file, less those
                indicated using the query_only
                flags, if applicable.
        """
        file_path = convert_network_drive_path(file_path)

        if file_path is None:

            dict_of_dfs = dict()

        elif isinstance(file_path, str):

            file_type = self.get_file_type(file_path)

            if isinstance(query_only, str):

                query_only = re.split(",", query_only)
                query_only = [i.strip() for i in query_only]

                if table_names is None:
                    if len(query_only) != 1:
                        msg = (
                            "All tables need to be loaded."
                            "It is unclear which tables need to "
                            "only be queried. Please provide a "
                            "list of table names and query flags "
                            "of the same length."
                        )
                        log.error(msg)

                    elif query_only[0] == "Y":
                        # query all tables
                        table_names_to_load = None
                        table_names_for_conn = table_names

                else:
                    # identify tables that require database connections
                    inx = [i != "Y" for i in query_only]
                    # load only these tables
                    table_names_to_load = np.array(table_names)[inx].tolist()
                    # others should be just connected to
                    not_inx = [not i for i in inx]
                    table_names_for_conn = np.array(table_names)[
                        not_inx
                    ].tolist()

            else:
                table_names_to_load = table_names
                table_names_for_conn = None

            if file_type == "excel":
                # load all tables found in the
                # file as a dict of dataframes

                dict_of_dfs = Excel(file_path, pre_existing_keys).load(
                    data_object_names=table_names_to_load
                )

            elif file_type == "text":
                dict_of_dfs = dict()

                filename_to_tablename = ntpath.basename(file_path)
                filename_to_tablename = re.split("\.", filename_to_tablename)[
                    0
                ]

                Debugger.check_for_duplicates(
                    pre_existing_keys, filename_to_tablename
                )

                # get rid of the version substring
                if self.la["extra_files"] in filename_to_tablename:
                    filename_to_tablename = self.la["extra_files"]

                dict_of_dfs[filename_to_tablename] = pd.read_csv(file_path)

            elif file_type == "database":
                # load all tables found in the
                # file as a dict of dataframes

                dict_of_dfs = Db(file_path, pre_existing_keys).load(
                    table_names=table_names_to_load
                )

            elif file_type == "sqlalchemy":
                # load all tables found in the
                # sqlalchemy database as a dict of dataframes

                dict_of_dfs = Db_sqlalchemy(file_path, pre_existing_keys).load(
                    table_names=table_names_for_conn
                )

        else:
            msg = "Unsupported value ({}) provided as input file path."
            log.error(msg.format(file_path))

        return dict_of_dfs

    def create_db(
        self,
        dict_of_dfs,
        db_conn=False,
        outpath=None,
        run_tag="",
        flavor="sqlite",
        close=True,
    ):
        """Creates a database with all the input
        tables that were read in.

        Parameters:

            dict_of_dfs: dict of dfs
                Contains all input
                tables with table name
                as a dict key and the table
                as a pandas dataframe under that
                key

            db_conn: None or db connection
                None: Writes to the db initiated at
                input data read-in
                Otherwise pass a database connection
                to an existing database

            outpath:
                Output folder path

            run_tag: str
                Default: ""
                Tag to include in the db name

            db_flavor:
                Database file format

        Returns:

            res: dict
                {'db_path' : database path ,
                 'db_conn' : database connection}
        """
        if flavor == "sqlite":
            db_out_type = ".db"

        if outpath is None:
            # create an `output` folder under CWD
            outpath = os.path.join(os.getcwd(), "output")

        if not os.path.exists(outpath):
            os.makedirs(outpath)

        # create an sql database within the output folder and connect
        db_path = os.path.join(outpath, run_tag + db_out_type)
        db_con = sqlite3.connect(db_path)

        # write all input tables in the db
        for table_name in dict_of_dfs.keys():
            try:
                dict_of_dfs[table_name].to_sql(
                    name=table_name,
                    con=db_con,
                    if_exists="replace",
                    index=False,
                )
            except:
                msg = "An error occurred when writting {} table " "to a db {}."
                log.error(msg.format(table_name, db_path))
                raise ValueError

            msg = "Wrote tables in a database: {}."
            log.info(msg.format(db_path))

        if close:
            db_con.close()

        res = {"db_path": db_path, "db_conn": db_con}

        return res

    def write(
        self,
        type="db",
        data_connection=None,
        data_as_dict_of_dfs=None,
        outpath=None,
        run_tag="",
        db_conn=None,
        close_db=True,
    ):
        """Writes all dataframes from a dictionary of dataframes
        out into an existing database.

        Paramters:

            type: str
                String to indicate type of output
                files:

                'db': database
                'csv': csv
                'db&csv': both database and csv

            data_connection: dict
                Return of `load` method

                Keys:

                'tables_as_dict_of_dfs' - all input
                    tables loaded in python as dictionary
                    of dataframes, to be written

                If data_as_dict_of_dfs is not none, these
                will be the dataframes written to output
                instead

                'outpath' - output folder path
                'run_tag' - version + analysis start time


                If db got written:

                'db_path' - database fullpath
                'db_conn' - database connection

                Set to None if passing the data, db
                connection and run tag explicitely through
                other kwargs. This functionality can
                be used when the `load` method was not called.

            data_as_dict_of_dfs: dict of dfs to be written
                Default: None, if data was passed with the
                data_connection

            outpath:
                Default: None means current working directory
                It is ignored if using the data connection
                that is the return of `load` method.
                Otherwise pass output folder path

            run_tag: str
                Default: ""
                It is ignored if using the data connection
                that is the return of `load` method.
                Tag to include in the db/file name

            db_conn: None or db connection
                Default: None if using the data connection that
                is the return of `load` method.
                Otherwise pass a database connection
                to an existing database

            close_db: boolean
                Default: True
                To close the db connection after
                the data is written.

        Return:

            True
        """
        if data_connection is not None:

            if data_as_dict_of_dfs is None:
                data_as_dict_of_dfs = data_connection["tables_as_dict_of_dfs"]

            db_conn = data_connection["db_conn"]

            if outpath is None:
                outpath = data_connection["outpath"]

            run_tag = data_connection["run_tag"]
        else:
            if outpath is None:
                outpath = os.getcwd()

        outpath = convert_network_drive_path(outpath)

        if data_as_dict_of_dfs is None:
            msg = "No data to write passed."
            log.error(msg)
            raise ValueError
        elif not isinstance(data_as_dict_of_dfs, dict):
            msg = "Data needs to be in a " "dictionary of dataframes format."
            log.error(msg)
            raise ValueError

        if "db" in type:

            close = close_db

            if db_conn is None:
                msg = "Missing db connection."
                log.error(msg)
                raise ValueError

            self.create_db(
                dict_of_dfs=data_as_dict_of_dfs,
                db_conn=db_conn,
                outpath=outpath,
                run_tag=run_tag,
                flavor="sqlite",
                close=close_db,
            )

        if "csv" in type:

            if not os.path.exists(outpath):
                os.mkdir(outpath)

            for key in data_as_dict_of_dfs.keys():
                df_to_write = data_as_dict_of_dfs[key]

                df_to_write.to_csv(
                    path_or_buf=os.path.join(
                        outpath,
                        key + "_" + run_tag + ".csv",
                    )
                )

    def first_col_to_index(self, dict_of_dfs, table_names=True, drop=True):
        """Function that sets the first column of dataframe as index.

        Parameters:

            dict_of_dfs: dict of pandas dataframes
                Contains all input
                tables with table name
                as a dict key and the table
                as a pandas dataframe under that
                key

            table_names: list or True
                List containing names of tables that
                need to be modified
                Default: True means all tables are
                modified

            drop: boolean
                Flag indicating whether to drop the column
                being set as index. Default value is true.

        Returns:

            res: dict of pandas dataframes
                Contains the modified dataframes after
                the index has been set

        """
        if table_names == True:
            msg = "Converting first column to index for all inputs."
            log.info(msg.format(table_names))
            table_names = dict_of_dfs.keys()

        elif isinstance(table_names, list):
            msg = "Converting first column to index for {} tables."
            log.info(msg.format(table_names))

        elif table_names == False:
            pass

        else:
            msg = "Unsupported value {} passed to table_names kwarg."
            log.error(msg.format(table_names))
            raise ValueError

        res = dict()
        for x in dict_of_dfs.keys():
            if x in table_names:
                col = dict_of_dfs[x].columns[0]
                res[x] = dict_of_dfs[x].copy().set_index(col, drop=True)
            else:
                res[x] = dict_of_dfs[x].copy()

        return res

    def process_column_labels(self, list_of_labels):
        """
        Converts table columns to string type and removes undesired spaces

        Parameters:

            list_of_labels: list
                list with column labels

        Returns:

            list_of_cleaned_labels: list
                A list with cleaned lables
        """
        list_of_labels = [str(x) for x in list_of_labels]

        list_of_cleaned_labels = [
            re.sub(" +", " ", lbl.strip()) for lbl in list_of_labels
        ]

        return list_of_cleaned_labels
