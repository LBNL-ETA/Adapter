from unittest import TestCase

from adapter.to_python import (
    convert_data_object_to_df,
    Excel,
    Db,
)
import openpyxl
import pandas as pd
from pandas._testing import assert_frame_equal
import logging

logging.basicConfig(level=logging.DEBUG)


class UtilTest(TestCase):
    """Tests for general functions"""

    @classmethod
    def setUp(self):
        """Loads an excel workbook"""
        self.file_path = r"adapter/tests/test.xlsx"
        self.wb = openpyxl.load_workbook(
            self.file_path, data_only=True, read_only=False, keep_vba=True
        )

    def test_convert_single_cell_to_df(self):
        ws = self.wb["test"]
        cell = ws["B2"]
        df1 = convert_data_object_to_df(cell, "Cell")
        df2 = pd.DataFrame([[cell.value]], columns=["Cell"])
        assert_frame_equal(df1, df2)

    def test_convert_multi_cell_to_df(self):
        ws = self.wb["test"]
        cells = ws["B2:C3"]
        df1 = convert_data_object_to_df(cells, "Cells")
        df2 = pd.DataFrame(
            [[cell.value for cell in row] for row in cells[1:]],
            columns=[cell.value for cell in cells[0]],
        )
        assert_frame_equal(df1, df2)


class ExcelTest(TestCase):
    """Tests for new Excel class"""
    @classmethod
    def setUp(self):
        """Loads an excel workbook"""
        self.data = Excel(r"adapter/tests/test.xlsx")

    def test_load(self):
        dict_of_dfs = self.data.load()
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

    def test_get_unnamed_range(self):
        range_name = "test!B2:C3"
        region = self.data.wb["test"]["B2:C3"]
        df1 = convert_data_object_to_df(region, range_name)
        df2 = self.data.get_named_data_objects(range_name)
        assert_frame_equal(df1, df2)

    def test_get_named_range(self):
        range_name = "xlsx_named_range1"
        region = self.data.wb["test"]["J16:K18"]
        df1 = convert_data_object_to_df(region, range_name)
        df2 = self.data.get_named_data_objects(range_name)
        assert_frame_equal(df1, df2)

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
