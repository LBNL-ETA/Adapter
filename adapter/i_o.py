from to_python import Excel, Db
from label_map import Labels

from datetime import datetime
import re

import logging
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class IO(object):
    """

    Parameters:

        db_db_flavor:
    """
    def __init__(path):

        self.input_path = path

        self.input_type = self.get_file_type(path)

        # set labels
        self.la = Labels().set_labels()


    def get_file_type(self, path):
        """Extracts the file type from the fullpath.
        """
        extns = re.split('\.', path)[-1]

        # extns = ...
        file_type = ''

        if extns=='xlsx':
            file_type += 'excel'

        elif extns=='db':
            file_type += 'database'

            # *mig add more file extension checks
            # as needed

        elif extns=='csv':
            file_type += 'text'

        else:
            msg = 'Passed an unsupported input file type: {}.'
            log.error(msg.format(extns))

        return file_type


    def load(self, create_db = True):
        """Loads tables from the input file
        as a dictinary of python dataframes.

        Recognizes any special table names, such
        as:

            - `run_parameters`, that specifies the output
            path, alongside to some further analysis related
            specifiers.

            - `inputs_from_files`, that specifies a list of
            additional input files of various file types.

        Parameters:

            create_db:

        Returns:

            dict_of_dfs:

            tables_to_query:
        """
        dict_of_dfs = self.get_tables(self.input_type)

        # are there any further input files?
        # if that is the case, the file paths and further info
        # should be placed in an `inputs_from_files` table
        if self.la['extra_files'] in dict_of_dfs.keys():

            extra_files = dict_of_dfs[
                self.la['extra_files']].reset_index()

            for inx in extra_files.index:

                file_path = extra_files.loc[
                inx, self.la['inpath']]

                type = self.get_file_type(
                    file_path)

                table_names = extra_files.loc[
                inx, self.la['tbl_nam']]

                qry_flags = extra_files.loc[
                inx, self.la['query']]

                # get those tables
                dict_of_dfs.update(self.get_tables(
                    type, table_names=table_names,
                    load_or_query=qry_flags)
                    )


        if create_db = True:
            # initial value
            outpath = None

            # look for `run_parameters` table
            # to extract the outpath
            if self.la['run_pars'] in dict_of_dfs.keys():

                outpath_base = dict_of_dfs[
                    self.la['run_pars']].loc[0, self.la['outpath']]

                version = dict_of_dfs[
                    self.la['run_pars']].loc[0, self.la['version']]

                run_tag = version + '_' + \
                    datetime.now().strftime('%Y_%m_%d-%Hh_%Mm')

                outpath = os.path.join(outpath, run_tag)

            try:
                self.create(
                    create_db=create_db,
                    outpath=outpath
                    db_flavor=db_flavor)
            except:
                # *mig add error message
                pass

            res = dict()
            res['tables'] = dict_of_dfs
            res['query_only'] = tables_to_query
            res['outpath'] = outpath

        return res


    def get_tables(self,
        file_type,
        table_names=None,
        load_or_query=None):
        """

        Parameters:

            file_type: str
                Options:
                'excel', 'database', 'text'

            load_or_query: str list
                Values: 'N' or 'Y'
                If None all tables get
                loaded. If a single
                'Y' is passed, it will
                be applied to all tables

            table_names: list of str
                Tables to load. If None
                all tables get loaded (
                unless all need to be
                queried)
        """
        if load_or_query == 'Y':
            load_or_query = ['Y']

        if load_or_query is not None:

            if table_names is None:
                if len(load_or_query) !=1:
                    msg = 'All tables need to be loaded.'\
                    'It is unclear which tables need to '\
                    'only be querried. Please provide a '\
                    'list of table names and query flags '\
                    'of the same length.'
                    log.error(msg)

            else:
                inx = [i=='Y' for i in load_or_query]
                # load only those tables
                table_names_to_load = table_names[inx]
                # others should be just connected to
                table_names_for_conn = table_names[~inx]

        else:
            table_names_to_load = table_names
            table_names_for_conn = None

        # *as or *lz see what to do about db connections

        if file_type == 'excel':
            # load all tables found in the
            # file as a dict of dataframes
            dict_of_dfs = Excel(
                self.input_path).load(
                table_names=table_names_to_load
                )

        elif file_type == 'text':
            dict_of_dfs = dict()
            dict_of_dfs[
                self.la['extra_files']] = pd.read_csv(
                file_type
                )

        elif file_type == 'database':
            # load all tables found in the
            # file as a dict of dataframes
            dict_of_dfs = Db(
                file_type).load(
                table_names=table_names_to_load
                )

        return dict_of_dfs


    def create_db(self,
        dict_of_dfs, outpath=None, db_flavor='sqlite'):
        """Creates a database with all the input
        tables that were read in

        Parameters:

            dict_of_dfs:

            outpath:

            db_flavor:

        Returns:

            True to indicate the code succeeded
        """
        # *mig get db extension based on the db_flavor
        # for example
        if db_flavor=='sqlite':
            self.db_out_type = 'db'

        if outpath is None:
            # *mig create an `output` folder
            # under CWD
            outpath = os.path.join(os.getcwd(), 'output')

        if not os.path.exists(outpath):
            os.makedirs(outpath)

        # create an sql database within the output folder and connect
        db_con = sqlite3.connect(outpath + \
            '//results_' + run_tag + '.db')

        # write all input tables in the db
        for table_name in self.inputs.keys():
            self.inputs[table_name].to_sql(
                name=table_name,
                con=db_con,
                if_exists='append')

        return True
