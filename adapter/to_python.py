from comm.xlwings_tools import Book, xl2pd, pd2xl
from comm.sql import Sql

import logging
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class Excel(object):
    """
    """
    def __init__(file_path):
        """
        """
        self.wb = Book(file_path)
        self.file_path = file_path


    def load(table_names = None):
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

        dict_of_dfs.update(
            self.get_named_ranges(table_names))

        return dict_of_dfs


    def get_tables(self, table_names):
        """Grabs data defined as excel tables.
        """
        # grab all the input tables
        all_input_table_names = self.wb.tables

        # initiate dictionaries of input table dataframes
        # and populate
        dict_of_dfs = dict()

        if len(all_input_table_names) > 0:
            if type(table_names)==list:
                for table_name in table_names:
                    if table_name is not in all_input_table_names:
                        msg = '{} not found in the input file {}.'
                        log.error(msg.format(
                            table_name, self.file_path))
                        raise ValueError

            elif table_names is None:
                table_names = all_input_table_names

            else:
                msg = 'Unsupported type ({}) passed for table names, {}.'
                msg.error(msg.format(type(table_names), table_names))
                raise ValueError

            try:
                for table_name in table_names:
                    # prepare labels (strip extra spaces)
                    dict_of_dfs[table_name] = self.wb.named_range_to_df(
                        input_tables[table_name], verbose = True)
                    dict_of_dfs[table_name].columns = \
                       Toolbox.process_column_labels(
                        dict_of_dfs[table_name].columns)

                msg = 'Read in input tables from {}.'
                log.info(msg.format(self.inpath))
            except:
                # more detailed error data should come from xlwings_tools
                msg = 'Failed to read input tables from {}.'

                log.error(msg.format(self.inpath))
                raise ValueError

        return dict_of_dfs


    def get_named_ranges(self):
        """Grabs data defined as named ranges.
        """
        # return dict_of_dfs
        # *lz
        pass


class Db(object):
    """
    """
    def __init__(file_path):
        self.db = Sql(file_path)
        self.inpath = file_path

    def load(table_names = None):
        """
        """
        try:
            dict_of_dfs = self.db.tables2dict(
                close = True)

        # *mig similarly to Excel, make sure that
        # only the provided list of table_names, if
        # it got provided, gets read in. I would
        # simply eliminate any tables that got
        # read in in the previous step and also make
        # sure that all the listed tables are in the
        # dict_of_dfs

        except:
            msg = 'Failed to read input tables from {}.'
            log.error(msg.format(self.inpath))
            raise ValueError

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
