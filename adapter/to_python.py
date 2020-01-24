from adapter.comm.xlwings_tools import Book, xl2pd, pd2xl
from adapter.comm.sql import Sql
import re

import logging
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


from pdb import set_trace as bp

class Excel(object):
    """
    """
    def __init__(self, file_path):
        """
        """
        self.wb = Book(file_path)
        self.file_path = file_path

        log.info(
        "Connected to: {}".format(file_path))


    def load(self, table_names = None):
        """Opens the file provided
        through file_path, loads
        all or a subset of tables
        and named ranges
        available in the file and
        converts to a python format.

        Parameters:

            table_names: list
                List of string table names
                to load. Default: None means
                that all tables found in the
                input file get loaded.

        Returns:

            dict_of_dfs: dict of dataframes
                Python dictionary with table name
                keys and input table values.
        """
        # *mig please make corresponding
        # docstrings for the analoguos
        # methods in other classes in this
        # file
        dict_of_dfs = self.get_tables(
            table_names)

        # *lz - this should be uncommented after
        # you implement the method

        # dict_of_dfs.update(
        #     self.get_named_ranges(table_names))

        return dict_of_dfs


    def get_tables(self, table_names):
        """Grabs data defined as excel tables.
        """
        # grab all the input tables
        all_input_tables = self.wb.tables

        # initiate dictionaries of input table dataframes
        # and populate
        dict_of_dfs = dict()

        if len(all_input_tables.keys()) > 0:
            if type(table_names)==list:
                for table_name in table_names:
                    if table_name not in all_input_tables.keys():
                        msg = '{} not found in the input file {}.'
                        log.error(msg.format(
                            table_name, self.file_path))
                        raise ValueError

            elif table_names is None:
                table_names = all_input_tables.keys()

            else:
                msg = 'Unsupported type ({}) passed for table names, {}.'
                msg.error(msg.format(type(table_names), table_names))
                raise ValueError

            try:
                for table_name in table_names:
                    # prepare labels (strip extra spaces)
                    dict_of_dfs[table_name] = self.wb.named_range_to_df(
                        all_input_tables[table_name],
                        verbose = True)
                    dict_of_dfs[table_name].columns = \
                       Toolbox().process_column_labels(
                        dict_of_dfs[table_name].columns)

                msg = 'Read in input tables from {}.'
                log.info(msg.format(self.file_path))
            except:
                # more detailed error data should come from xlwings_tools
                msg = 'Failed to read input tables from {}.'

                log.error(msg.format(self.file_path))
                raise ValueError

            msg = "Loaded named tables from {}."
            log.info(msg.format(self.file_path))

        return dict_of_dfs


    def get_named_ranges(self, table_names):
        """Grabs data defined as named ranges.
        """
        # return dict_of_dfs
        # *lz
        # if len(all_input_tables.keys()) > 0:
        #     msg = "Loaded named rangesfrom {}."
        #     log.info(msg.format(self.file_path))
        pass


class Db(object):
    """
    """
    def __init__(self, file_path):
        self.db = Sql(file_path)
        self.inpath = file_path

    def load(self, table_names = None):
        """
        """
        # try:
        all_dict_of_dfs = self.db.tables2dict(
            close = True)

        dict_of_dfs = dict()

        if len(all_dict_of_dfs.keys()) > 0:

            if type(table_names)==list:

                for table_name in table_names:

                    if table_name not in\
                        all_dict_of_dfs.keys():
                        msg = '{} not found in the input file {}.'
                        log.error(msg.format(
                            table_name, self.file_path))
                        raise ValueError

                    else:
                        dict_of_dfs[table_name] = \
                        all_dict_of_dfs[table_name]
            else:
                dict_of_dfs = all_dict_of_dfs

        # except:
        #     msg = 'Failed to read input tables from {}.'
        #     log.error(msg.format(self.inpath))
        #     raise ValueError

        return dict_of_dfs


class Toolbox(object):

    def process_column_labels(self, list_of_labels):
        """Removes undesired spaces

        Parameters:

            list_of_labels: list
                list with column labels

        Returns:

            list_of_cleaned_labels: list
                A list with cleaned lables
        """
        list_of_cleaned_labels = [
            re.sub(' +', ' ', lbl.strip()) for lbl in list_of_labels]

        return list_of_cleaned_labels
