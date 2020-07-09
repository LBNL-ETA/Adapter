import unittest
from adapter.to_python import Excel, Db

import logging
logging.basicConfig(level=logging.DEBUG)

from pdb import set_trace as bp

class ExcelTests(unittest.TestCase):

    @classmethod
    def setUp(self):
        """Instantiates an excel loader
        """
        self.exl_loader = Excel(
        r'adapter/tests/test.xlsx')


    def test_load(self):
        """Tests loading named tables
        and named ranges from excel.
        """
        all_tables = self.exl_loader.load(
            kind = 'all')

        self.assertTrue(
        set(all_tables.keys())=={
        'xlsx_table1','xlsx_table2',
        'run_parameters'})

        some_tables = self.exl_loader.load(
            data_object_names = ['xlsx_table1','xlsx_table2'],
            kind = 'tables')

        self.assertTrue(
        set(some_tables.keys())=={
        'xlsx_table1','xlsx_table2'})


class DbTests(unittest.TestCase):

    @classmethod
    def setUp(self):
        """Instantiates a DB loader
        """
        self.db_loader = Db(
        r'adapter/tests/test.db')


    def test_load_all_tables(self):
        """Tests loading all tables
        from sqlite databases.
        """
        all_tables = self.db_loader.load()

        self.assertTrue(
        set(all_tables.keys())=={
        'table2','table3','table1'})

    def test_load_some_tables(self):
        """Tests loading specified tables
        from sqlite databases.
        """
        some_tables = self.db_loader.load(
            table_names = ['table1','table2'])

        self.assertTrue(
        set(some_tables.keys())=={
        'table1','table2'})
