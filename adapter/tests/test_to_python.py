import unittest
from unittest import TestCase

from adapter.to_python import Excel, Db

import logging

logging.basicConfig(level=logging.DEBUG)


class ExcelTests(unittest.TestCase):
    @classmethod
    def setUp(self):
        """Instantiates an excel loader"""
        self.exl_loader = Excel(r"adapter/tests/test.xlsx")

    def test_load(self):
        """Tests loading named tables
        and named ranges from excel.
        """
        all_tables = self.exl_loader.load(kind="all")

        self.assertTrue(
            set(all_tables.keys())
            == {
                "xlsx_table1",
                "xlsx_table2",
                "run_parameters",
                "xlsx_single_col_table",
                "xlsx_named_range1",
                "xlsx_single_col_range",
                "xlsx_single_value_named_range",
            }
        )

        some_tables = self.exl_loader.load(
            data_object_names=["xlsx_table1", "xlsx_table2"], kind="tables"
        )

        self.assertTrue(
            set(some_tables.keys()) == {"xlsx_table1", "xlsx_table2"}
        )

        some_ranges = self.exl_loader.load(
            data_object_names=["xlsx_named_range1", "xlsx_single_col_range"],
            kind="ranges",
        )

        self.assertTrue(
            set(some_ranges.keys())
            == {"xlsx_named_range1", "xlsx_single_col_range"}
        )


class DbTests(unittest.TestCase):
    @classmethod
    def setUp(self):
        """Instantiates a DB loader"""
        self.db_loader = Db(r"adapter/tests/test.db")

    def test_load_all_tables(self):
        """Tests loading all tables
        from sqlite databases.
        """
        all_tables = self.db_loader.load()

        self.assertTrue(
            set(all_tables.keys()) == {"table2", "table3", "table1"}
        )

    def test_load_some_tables(self):
        """Tests loading specified tables
        from sqlite databases.
        """
        some_tables = self.db_loader.load(table_names=["table1", "table2"])

        self.assertTrue(set(some_tables.keys()) == {"table1", "table2"})


class TestDb(TestCase):
    def setUp(self):
        """creating DB objects"""
        self.db = Db(file_path="./test.db", pre_existing_keys=['table1'])
        self.good_db = Db(file_path="./test.db")
        self.bad_db = Db(file_path="./corrupt.db")

    def tearDown(self) -> None:
        # destroy objects
        del self.db
        del self.good_db
        del self.bad_db

    def test_load_good(self):
        # test file load with table_names
        self.assertEqual(len((self.good_db.load(table_names=['table1', 'table2'])).keys() - {'table1', 'table2'}), 0)

    def test_load_pre_keys(self):
        # test file load with pre_existing_keys
        with self.assertRaises(ValueError):
            self.db.load()

    def test_load_bad_db(self):
        # test corrupt file load
        with self.assertRaises(IOError):
            self.bad_db.load()

    def test_load_df(self):
        # test dataframe not empty
        self.assertIsNotNone((self.good_db.load(table_names=['table3'])['table3']).head())
