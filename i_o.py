from data_types import Excel, Db, Text


class IO(object):
    """

    Parameters:

        db_db_flavor:
    """
    def __init__(path, db_flavor = 'sqlite'):
        # determine the file type
        # *mig extract the substring after
        # the last `.` in the path string

        # extns = ...
        self.input_type = ''

        if extns=='xlsx':
            self.input_type += 'excel'

        elif extns=='db':
            self.input_type += 'db'

            # *mig add more file extension checks
            # as needed

        elif extns=='csv':
            self.input_type += 'excel'

        else:
            msg = 'Passed an unsupported input file type {}.'
            log.error(msg.format(extns))


    def load(create_db = True):
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


        # *mig extract outpath from
        # `run_parameters`
        # if not found, set to None
        outpath =

        if create_db = True:
            self.create(
                create_db=create_db,
                outpath=outpath
                db_flavor=db_flavor)

        return dict_of_dfs, tables_to_query


    def create_db(dict_of_dfs, outpath=None, db_flavor='sqlite'):
        """Creates a database with all the input
        tables that were read in

        Parameters:

            dict_of_dfs:

            outpath:

            db_flavor:

        Returns:

            True to indicate the code succeeded
        """
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


    def read():
        """
        """
        # figure out how to open the file
        # provided in the path based on the
        # data type (file extension)
        pass
