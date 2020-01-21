from comm.xlwings_tools import Book, xl2pd, pd2xl


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

        # grab all the input tables
        all_input_table_names = self.wb.tables

        # initiate dictionaries of input table dataframes
        # and populate
        dict_of_dfs = dict()

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
        

    def write(close = True):
        """
        """
        pass


class Db(object):
    """
    """
    def __init__(file_path):
        pass

    def load(table_names = None):
        """
        """
        pass

    def write(db_connection = None, close = True):
        """
        """
        pass


class Text(object):
    """
    """
    def __init__(file_path):
        pass

    def load():
        """
        """
        pass

    def write(db_connection = None, close = True):
        """
        """
        pass


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
