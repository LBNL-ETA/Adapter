import unittest
import os

from adapter.i_o import IO

import logging
logging.basicConfig(level=logging.DEBUG)

from pdb import set_trace as bp

class IOTests(unittest.TestCase):

    def test_load_from_excel(self):
        """Tests the typical LCC analysis case
        where all input tables are saved as
        named tables in an excel input sheet.
        """
        path = os.path.join(os.getcwd(),
            r'adapter/tests/test.xlsx')
        i_o = IO(path)

        res = i_o.load()

        self.assertTrue(res['tables_to_query'] is None)
        self.assertTrue('db_path' in res.keys())

        res_no_db = i_o.load(create_db=False)
        self.assertFalse('db_path' in res_no_db.keys())


    def test_load_from_excel_w_input_from_files(self):
        """Tests the ability to load in input tables
        from various additional files based on an info provided
        in the usual excel sheet.
        """
        path = os.path.join(os.getcwd(),
            r'adapter/tests/test_w_inputs_from_files_table.xlsx')
        i_o = IO(path)

        res = i_o.load()

        self.assertEqual(len(res['tables_as_dict_of_dfs'].keys()), 8)
        self.assertEqual(len(res['tables_to_query'].keys()), 3)


    def test_load_from_csv_inputs_from_files(self):
        """
        """
        path = os.path.join(os.getcwd(),
            r'adapter/tests/inputs_from_files_vTest.csv')
        i_o = IO(path)

        res = i_o.load()

        bp()

    def test_load_from_excel_no_run_parameters(self):
        """
        """
        # *mig the code is supposed to notify user and
        # create a version and outpath
        path = os.path.join(os.getcwd(),
            r'adapter/tests/test_no_run_parameters.xlsx')
        i_o = IO(path)

        res = i_o.load()

        bp()

    def test_load_from_db(self):
        """
        """
        # *mig the code is supposed to notify user and
        # create a version and outpath
        path = os.path.join(os.getcwd(),
            r'adapter/tests/test.db')
        i_o = IO(path)

        res = i_o.load()

        bp()
