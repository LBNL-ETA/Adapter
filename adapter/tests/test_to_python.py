import unittest
from adapter.to_python import Excel, Db

import logging
logging.basicConfig(level=logging.DEBUG)

class ExcelTests(unittest.TestCase):

    @classmethod
    def setUp(self):
        """
        """
        self.exl_loader = Excel(
        r'adapter/tests/test.xlsx')


    def test_load(self):
        """Tests loading named tables
        and named ranges from excel.
        """
        all_tables = self.exl_loader.load()

        self.assertTrue(
        set(all_tables.keys())=={
        'xlsx_table1','xlsx_table2',
        'run_parameters'})

        some_tables = self.exl_loader.load(
            table_names = ['xlsx_table1','xlsx_table2'])

        self.assertTrue(
        set(some_tables.keys())=={
        'xlsx_table1','xlsx_table2'})

        # *lz add equivalent tests for loading
        # named ranges. If you add named
        # ranges to the same input file, then
        # you can simply extend the lists of
        # expected input table names.
