import unittest
from adapter.i_o import IO

import logging
logging.basicConfig(level=logging.DEBUG)

from pdb import set_trace as bp

class IOTests(unittest.TestCase):

    @classmethod
    def setUp(self):
        """
        """
        self.i_o = IO(
        r'adapter/tests/test.xlsx')

    def test_load_from_excel(self):
        """
        """
        pass

    def test_load_from_excel_w_input_from_files(self):
        """
        """
        pass

    def test_load_from_csv_inputs_from_files(self):
        """
        """
        pass

    def test_load_from_excel_no_run_parameters(self):
        """
        """
        # *mig the code is supposed to notify user and
        # create a version and outpath
        pass

    def test_load_from_db(self):
        """
        """
        # *mig the code is supposed to notify user and
        # create a version and outpath
        pass
