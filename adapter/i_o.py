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
        # determine the file type
        # *mig extract the substring after
        # the last `.` in the path string
        self.input_path = path

        extns = re.split('\.', path)[-1]

        # extns = ...
        self.input_type = ''

        if extns=='xlsx':
            self.input_type += 'excel'

        elif extns=='db':
            self.input_type += 'database'

            # *mig add more file extension checks
            # as needed

        elif extns=='csv':
            self.input_type += 'text'

        else:
            msg = 'Passed an unsupported input file type: {}.'
            log.error(msg.format(extns))

        # set labels
        self.la = Labels().set_labels()


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
        if self.input_type == 'excel':
            # load all tables found in the
            # file as a dict of dataframes
            dict_of_dfs = Excel(
                self.input_path).load()

        elif self.input_type == 'text':
            dict_of_dfs = dict()
            dict_of_dfs[
                self.la['extra_files']] = pd.read_csv(self.input_path)

        elif self.input_file == 'database':
            # load all tables found in the
            # file as a dict of dataframes
            dict_of_dfs = Db(
                self.input_path).load()

        # are there any further input files?
        # if that is the case, the file paths and further info
        # should be placed in an `inputs_from_files` table
        if self.la['extra_files'] in dict_of_dfs.keys():
            # *as or *lz:
            # please walk through the list of files in the
            # input_from_files table and load
            # or establish db connection as needed
            # please see the drafted tests for functionality
            # requirements, I prepared the test files in the
            # test folder
            # it is desirable to have this broken into
            # separate methods
            pass

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
