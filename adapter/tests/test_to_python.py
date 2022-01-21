import os
from unittest import TestCase
import unittest
from adapter.to_python import Excel, Db
import openpyxl
import pandas as pd
from pandas._testing import assert_frame_equal
import logging

logging.basicConfig(level=logging.DEBUG)

class ExcelTest(TestCase):
    """Tests for new Excel class"""
    @classmethod
    def setUp(self):
        """Loads an excel workbook"""
        self.exl_loader = Excel(os.path.join(os.path.dirname(__file__), "test.xlsx"))

    def test_load(self):
        dict_of_dfs = self.exl_loader.load(kind="all")
        self.assertTrue(
            set(dict_of_dfs.keys())
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

    def test_get_unnamed_range(self):
        range_name = "test!B2:C3"
        region = self.exl_loader.wb["test"]["B2:C3"]
        df1 = self.exl_loader.convert_data_object_to_df(region, range_name)
        df2 = self.exl_loader.get_named_data_object(range_name)
        assert_frame_equal(df1, df2)

    def test_get_named_range(self):
        range_name = "xlsx_named_range1"
        region = self.exl_loader.wb["test"]["J16:K18"]
        df1 = self.exl_loader.convert_data_object_to_df(region, range_name)
        df2 = self.exl_loader.get_named_data_object(range_name)
        assert_frame_equal(df1, df2)

    def test_convert_single_cell_to_df(self):
        ws = self.exl_loader.wb["test"]
        cell = ws["B2"]
        df1 = self.exl_loader.convert_data_object_to_df(cell, "Cell")
        df2 = pd.DataFrame([[cell.value]], columns=["Cell"])
        assert_frame_equal(df1, df2)

    def test_convert_multi_cell_to_df(self):
        ws = self.exl_loader.wb["test"]
        cells = ws["B2:C3"]
        df1 = self.exl_loader.convert_data_object_to_df(cells, "Cells")
        df2 = pd.DataFrame(
            [[cell.value for cell in row] for row in cells[1:]],
            columns=[cell.value for cell in cells[0]],
        )
        assert_frame_equal(df1, df2)

class TestDb(TestCase):
    def setUp(self):
        """creating DB objects"""
        self.db = Db(file_path=os.path.join(os.path.dirname(__file__), "test.db"), pre_existing_keys=['table1'])
        self.good_db = Db(file_path=os.path.join(os.path.dirname(__file__), "test.db"))
        self.bad_db = Db(file_path=os.path.join(os.path.dirname(__file__), "corrupt.db"))

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

if __name__ == "__main__":
    unittest.main()