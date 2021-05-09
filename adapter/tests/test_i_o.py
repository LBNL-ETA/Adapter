import unittest
import os, shutil

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

        # tear down
        shutil.rmtree(res["outpath"])

        res_no_db = i_o.load(create_db=False)

        self.assertFalse("db_path" in res_no_db.keys())

    # uncomment only if you have a haggis connection set up with a
    # Secret.py file based on the Secret_example.py
    # def test_load_from_excel_w_sqalchemy(self):
    #     """Tests the typical LCC analysis case
    #     where all input tables are saved as
    #     named tables in an excel input sheet.
    #     """
    #     path = os.path.join(os.getcwd(),
    #         r"adapter/tests/test_w_inputs_from_files_table_sqlalchemy.xlsx")

    #     i_o = IO(path)

    #     res = i_o.load()

    #     self.assertTrue(
    #         set(['adapter_example_table1',
    #              'adapter_example_table2',
    #              'adapter_example_table3']).issubset(
    #                  set(res['tables_as_dict_of_dfs'].keys())))

    def test_throws_error_at_duplication(self):
        """Errors when same-named table is identified."""
        path = os.path.join(
            os.getcwd(),
            r"adapter/tests/inputs_from_files_vDuplicationError.csv",
        )

        i_o = IO(path)

        self.assertRaises(ValueError, i_o.load)

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

        self.assertEqual(len(res["tables_as_dict_of_dfs"].keys()), 10)

        # tear down
        shutil.rmtree(res["outpath"])

    def test_load_from_csv_inputs_from_files(self):
        """Tests loading from a single csv file that
        points to further inputs of any supported type.
        """
        path = os.path.join(
            os.getcwd(), r"adapter/tests/inputs_from_files_vTest.csv"
        )

        i_o = IO(path)

        res = i_o.load(to_numeric=["xlsx_table2"])

        self.assertEqual(len(res["tables_as_dict_of_dfs"].keys()), 11)
        self.assertEqual(len(res.keys()), 5)

    def test_load_from_excel_no_run_parameters(self):
        """Tests loading from an excel table without
        defined version and output path parameters.
        """

        path = os.path.join(
            os.getcwd(), r"adapter/tests/test_no_run_parameters.xlsx"
        )
        i_o = IO(path)

        res = i_o.load()

        self.assertEqual(len(res["tables_as_dict_of_dfs"].keys()), 2)

        # tear down
        shutil.rmtree(res["outpath"])

    def test_load_from_db(self):
        """Tests loading from a db."""

        path = os.path.join(os.getcwd(), r"adapter/tests/test.db")
        i_o = IO(path)

        res = i_o.load()

        self.assertEqual(len(res["tables_as_dict_of_dfs"].keys()), 3)

    def test_load_from_none(self):
        """Tests loading from a path specified as None."""

        i_o = IO(None)

        res = i_o.load()

        self.assertEqual(isinstance(res, dict), True)

    def test_first_col_to_index(self):
        """Tests if the first column is set as a index."""
        lst = [["A", 1, 1], ["A", 2, 1], ["B", 3, 1], ["B", 4, 1]]

        df1 = pd.DataFrame(lst, columns=["A", "B", "C"])
        df2 = pd.DataFrame(lst, columns=["X", "Y", "Z"])

        dict_of_dfs = {"df1": df1, "df2": df2}

        path = os.path.join(os.getcwd(), r"adapter/tests/test.db")
        i_o = IO(path)

        case1 = i_o.first_col_to_index(dict_of_dfs, table_names=True)
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
        """Tests if undesired whitespace from column labels is removed."""
        path = os.path.join(os.getcwd(), r"adapter/tests/test_labels.xlsx")
        i_o = IO(path)

        labels = ["aa bb ", " cc   dd"]
        expected_labels = ["aa bb", "cc dd"]

        result_labels = i_o.process_column_labels(labels)

        self.assertEqual(result_labels, expected_labels)

    def test_write_to_db(self):
        """Tests main write method for type db"""
        path = os.path.join(
            os.getcwd(), r"adapter/tests/inputs_from_files_vTest.csv"
        )
        i_o = IO(path)
        data_conn = i_o.load()

        # write to db based on load method output only
        i_o.write(type="db", data_connection=data_conn)

        self.assertTrue(os.path.isfile(data_conn["db_path"]))
        self.assertTrue(os.path.isdir(data_conn["outpath"]))

        # tear down files
        shutil.rmtree(data_conn["outpath"])

        # write to db based on load method output but
        # write new dataframes
        new = {"df1": pd.DataFrame([1, 2]), "df2": pd.DataFrame(["a", "b"])}

        i_o.write(
            type="db", data_connection=data_conn, data_as_dict_of_dfs=new
        )

        # add the input tables to the same db
        i_o.write(
            type="db",
            data_connection=data_conn,
        )

        self.assertTrue(os.path.isfile(data_conn["db_path"]))
        self.assertTrue(os.path.isdir(data_conn["outpath"]))

        # tear down files
        shutil.rmtree(data_conn["outpath"])

    def test_write_to_csv(self):
        """Tests main write method for type csv"""
        path = os.path.join(
            os.getcwd(), r"adapter/tests/inputs_from_files_vTest.csv"
        )
        i_o = IO(path)
        data_conn = i_o.load()

        # write to db based on load method output only
        i_o.write(type="csv", data_connection=data_conn)

        self.assertTrue(os.path.isfile(data_conn["db_path"]))
        self.assertTrue(os.path.isdir(data_conn["outpath"]))

        # tear down files
        shutil.rmtree(data_conn["outpath"])

        # write to db based on load method output but
        # write new dataframes
        new = {"df1": pd.DataFrame([1, 2]), "df2": pd.DataFrame(["a", "b"])}

        i_o.write(
            type="csv", data_connection=data_conn, data_as_dict_of_dfs=new
        )

        # add the input tables to the same db
        i_o.write(
            type="csv",
            data_connection=data_conn,
        )

        self.assertTrue(os.path.isdir(data_conn["outpath"]))

        # tear down files
        shutil.rmtree(data_conn["outpath"])

    def test_write_to_csv_and_db(self):
        """Tests main write method for both csv and db"""
        path = os.path.join(
            os.getcwd(), r"adapter/tests/inputs_from_files_vTest.csv"
        )
        i_o = IO(path)
        data_conn = i_o.load()

        # write to db based on load method output only
        i_o.write(type="db&csv", data_connection=data_conn)

        self.assertTrue(os.path.isfile(data_conn["db_path"]))
        self.assertTrue(os.path.isdir(data_conn["outpath"]))

        # tear down files
        shutil.rmtree(data_conn["outpath"])
