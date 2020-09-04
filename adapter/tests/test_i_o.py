import unittest
import os

import pandas as pd

from adapter.i_o import IO

import logging

logging.basicConfig(level=logging.DEBUG)


class IOTests(unittest.TestCase):
    def test_load_from_excel(self):
        """Tests the typical LCC analysis case
        where all input tables are saved as
        named tables in an excel input sheet.
        """
        path = os.path.join(os.getcwd(), r"adapter/tests/test.xlsx")
        i_o = IO(path)

        res = i_o.load()

        self.assertTrue("db_path" in res.keys())

        res_no_db = i_o.load(create_db=False)
        self.assertFalse("db_path" in res_no_db.keys())

    def test_load_from_excel_w_input_from_files(self):
        """Tests the ability to load in input tables
        from various additional files based on an info provided
        in the usual excel sheet.
        """
        path = os.path.join(
            os.getcwd(), r"adapter/tests/test_w_inputs_from_files_table.xlsx"
        )

        i_o = IO(path)

        res = i_o.load()

        self.assertEqual(len(res["tables_as_dict_of_dfs"].keys()), 9)

    def test_load_from_csv_inputs_from_files(self):
        """Tests loading from a single csv file that
        points to further inputs of any supported type.
        """
        path = os.path.join(
            os.getcwd(), r"adapter/tests/inputs_from_files_vTest.csv"
        )

        i_o = IO(path)

        res = i_o.load()

        self.assertEqual(len(res["tables_as_dict_of_dfs"].keys()), 10)
        self.assertEqual(len(res.keys()), 5)

    def test_load_from_excel_no_run_parameters(self):
        """Tests loading from an excel table without
        defined version and output path parameters.
        """
        # *mig the code is supposed to notify user and
        # create a version and outpath
        path = os.path.join(
            os.getcwd(), r"adapter/tests/test_no_run_parameters.xlsx"
        )
        i_o = IO(path)

        res = i_o.load()

        self.assertEqual(len(res["tables_as_dict_of_dfs"].keys()), 2)

    def test_load_from_db(self):
        """Tests loading from a db.
        """
        # *mig the code is supposed to notify user and
        # create a version and outpath
        path = os.path.join(os.getcwd(), r"adapter/tests/test.db")
        i_o = IO(path)

        res = i_o.load()

        self.assertEqual(len(res["tables_as_dict_of_dfs"].keys()), 3)

    def test_first_col_to_index(self):
        """Tests if the first column is set as a index.
        """
        lst = [["A", 1, 1], ["A", 2, 1], ["B", 3, 1], ["B", 4, 1]]

        df1 = pd.DataFrame(lst, columns=["A", "B", "C"])
        df2 = pd.DataFrame(lst, columns=["X", "Y", "Z"])

        dict_of_dfs = {"df1": df1, "df2": df2}

        path = os.path.join(os.getcwd(), r"adapter/tests/test.db")
        i_o = IO(path)

        case1 = i_o.first_col_to_index(dict_of_dfs, table_names=None)
        case2 = i_o.first_col_to_index(dict_of_dfs, table_names=["df1"])

        case1_check = {
            "df1": df1.set_index("A", drop=True),
            "df2": df2.set_index("X", drop=True),
        }

        case2_check = {"df1": df1.set_index("A", drop=True), "df2": df2}

        # Case1: When all tables have to be modified with the first column as index
        for x in case1.keys():
            assert case1[x].equals(case1_check[x])

        # Case2: When only some tables are modified
        for x in case2.keys():
            assert case2[x].equals(case2_check[x])

    def test_process_column_labels(self):
        """Tests if undesired whitespace from column labels is removed.
        """
        path = os.path.join(os.getcwd(), r"adapter/tests/test_labels.xlsx")
        i_o = IO(path)

        labels = ["aa bb ", " cc   dd"]
        expected_labels = ["aa bb", "cc dd"]

        result_labels = i_o.process_column_labels(labels)

        self.assertEqual(result_labels, expected_labels)
