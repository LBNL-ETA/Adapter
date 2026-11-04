import filecmp
import gzip
import json
import logging
import os
import pickle
import re
import shutil
import sqlite3

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from adapter.i_o import IO, from_pickle, to_pickle

logging.basicConfig(level=logging.DEBUG)

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
INPUTS_DIR = os.path.join(TESTS_DIR, "inputs")
TEST_XLSX = os.path.join(INPUTS_DIR, "test.xlsx")
TEST1_XLSX = os.path.join(INPUTS_DIR, "test1.xlsx")
TEST_DB = os.path.join(INPUTS_DIR, "test.db")
TEST_LABELS_XLSX = os.path.join(INPUTS_DIR, "test_labels.xlsx")

SHORT_TS = r"\d{6}_\d{4}"
LONG_TS = r"\d{4}_\d{2}_\d{2}_\d{2}h_\d{2}m"

LOAD_KEYS = {"tables_as_dict_of_dfs", "outpath", "run_tag"}
DB_KEYS = {"db_path", "db_conn"}

# Golden fixtures for the tables returned by IO.load(); see "Golden
# fixtures" in the root README.md. Keys are input files in
# adapter/tests/inputs; the value is True when the input references other
# inputs with repo-relative paths, so it must be loaded from the repo root.
REPO_ROOT = os.path.dirname(os.path.dirname(TESTS_DIR))
GOLDEN_DIR = os.path.join(TESTS_DIR, "fixtures", "golden")
GOLDEN_RTOL = 1e-9  # relative tolerance for floating point values
GOLDEN_CASES = {
    "test.xlsx": False,
    "test.csv": False,
    "test.db": False,
    "test_no_named_ranges.xlsx": False,
    "inputs_from_files_vTest.csv": True,
    "test_w_inputs_from_files_table.xlsx": True,
}


def golden_path(input_file):
    return os.path.join(GOLDEN_DIR, input_file.replace(".", "_") + ".json")


def frame_to_golden(df):
    """Converts a dataframe to the JSON-serializable golden format.
    Missing values are stored as None (null)."""
    values = df.astype(object).where(df.notna(), None)
    return {
        "columns": [str(c) for c in df.columns],
        "dtypes": {str(c): str(t) for c, t in df.dtypes.items()},
        "index": df.index.tolist(),
        # numpy scalars -> python scalars
        "data": [
            [v.item() if hasattr(v, "item") else v for v in row]
            for row in values.values.tolist()
        ],
    }


def golden_to_frame(golden):
    """Rebuilds a dataframe from the golden format."""
    df = pd.DataFrame(golden["data"], columns=golden["columns"], index=golden["index"])
    return df.astype(golden["dtypes"])


@pytest.mark.usefixtures("clean_output")
class IOTests:
    """IO.load() and IO.write() on the stored test inputs. Runs from the repo root
    (inputs use repo-relative paths); clean_output removes the output folders.
    """

    def setup_method(self):
        self.test_dir = os.path.join(os.path.dirname(__file__), "inputs")

    # uncomment only if you have a haggis
    # server connection set up with a
    # Secret.py file based on the Secret_example.py
    # def test_load_from_excel_w_sqalchemy(self):
    #     """Tests the typical LCC analysis case
    #     where all input tables are saved as
    #     named tables in an excel input sheet.
    #     """
    #     path = os.path.join(os.getcwd(),
    #         r"adapter/tests/inputs/test_w_inputs_from_files_table_sqlalchemy.xlsx")

    #     i_o = IO(path)

    #     res = i_o.load()

    #     self.assertTrue(
    #         set(['adapter_example_table1',
    #              'adapter_example_table2',
    #              'adapter_example_table3']).issubset(
    #                  set(res['tables_as_dict_of_dfs'].keys())))

    def test_throws_error_at_duplication(self):
        """IO.load() raises ValueError when inputs listed in `inputs_from_files` share a
        table name (xlsx_table1), via Debugger.check_for_duplicates() in Excel.load().
        """
        path = os.path.join(
            os.getcwd(),
            r"adapter/tests/inputs/inputs_from_files_vDuplicationError.csv",
        )

        i_o = IO(path)

        with pytest.raises(ValueError):
            i_o.load()

    def test_load_from_excel_no_run_parameters(self):
        """IO.load() loads an Excel file's tables when it has no `run_parameters` table."""

        path = os.path.join(
            os.getcwd(), r"adapter/tests/inputs/test_no_run_parameters.xlsx"
        )
        i_o = IO(path)

        res = i_o.load()

        assert len(res["tables_as_dict_of_dfs"].keys()) == 2

    def test_load_from_excel_no_named_ranges(self):
        """IO.load() reads each worksheet as a table (pd.read_excel) when an Excel file
        has no named tables or ranges.
        """
        path = os.path.join(self.test_dir, "test_no_named_ranges.xlsx")
        i_o = IO(path)

        res = i_o.load()

        assert len(res["tables_as_dict_of_dfs"].keys()) == 2

    def test_write_to_db(self):
        """IO.write(type="db") writes load()'s tables, or new dataframes, to the run's db,
        recreating the output folder if it was removed.
        """
        path = os.path.join(
            os.getcwd(), r"adapter/tests/inputs/inputs_from_files_vTest.csv"
        )
        i_o = IO(path)
        data_conn = i_o.load()

        # write to db based on load method output only
        i_o.write(type="db", data_connection=data_conn)

        assert os.path.isfile(data_conn["db_path"])
        assert os.path.isdir(data_conn["outpath"])

        # remove the output, so the writes below must recreate it
        shutil.rmtree(data_conn["outpath"])

        # write to db based on load method output but
        # write new dataframes
        new = {"df1": pd.DataFrame([1, 2]), "df2": pd.DataFrame(["a", "b"])}

        i_o.write(type="db", data_connection=data_conn, data_as_dict_of_dfs=new)

        # add the input tables to the same db
        i_o.write(
            type="db",
            data_connection=data_conn,
        )

        assert os.path.isfile(data_conn["db_path"])
        assert os.path.isdir(data_conn["outpath"])

    def test_write_to_csv(self):
        """IO.write(type="csv") writes load()'s tables, or new dataframes, as csv files,
        recreating the output folder if it was removed.
        """
        path = os.path.join(
            os.getcwd(), r"adapter/tests/inputs/inputs_from_files_vTest.csv"
        )
        i_o = IO(path)
        data_conn = i_o.load()

        # write to db based on load method output only
        i_o.write(type="csv", data_connection=data_conn)

        assert os.path.isfile(data_conn["db_path"])
        assert os.path.isdir(data_conn["outpath"])

        # remove the output, so the writes below must recreate it
        shutil.rmtree(data_conn["outpath"])

        # write to db based on load method output but
        # write new dataframes
        new = {"df1": pd.DataFrame([1, 2]), "df2": pd.DataFrame(["a", "b"])}

        i_o.write(type="csv", data_connection=data_conn, data_as_dict_of_dfs=new)

        # add the input tables to the same db
        i_o.write(
            type="csv",
            data_connection=data_conn,
        )

        assert os.path.isdir(data_conn["outpath"])


@pytest.mark.usefixtures("in_tmp_path")
class TestPickle:
    """to_pickle() and from_pickle() with gzip-compressed pickle files.
    Runs in a temporary working directory (in_tmp_path).
    """

    def test_single_object_pickle(self):
        """to_pickle() writes a gzip-compressed pickle that pickle.load() reads back."""
        data = {"name": "John", "age": 30, "city": "New York"}
        out_path = "data.pickle.gz"
        to_pickle(data, out_path)

        # Check that the output file exists and is not empty
        assert os.path.exists(out_path)
        assert os.path.getsize(out_path) > 0

        # Load the pickled data from the output file and check that it matches the original data
        with gzip.open(out_path, "rb") as f:
            py_data = pickle.load(f)
        assert data == py_data

    def setup_method(self):
        self.data = {"a": 1, "b": 2, "c": 3}
        self.out_path = "test.pkl.gz"
        self.in_path = "test.pkl.gz"

    def test_from_pickle_existing_file(self):
        """from_pickle() reads back an object written by to_pickle()."""
        to_pickle(self.data, self.out_path)
        result = from_pickle(self.in_path)
        assert result == self.data

    def test_from_pickle_non_existing_file(self):
        """from_pickle() raises FileNotFoundError for a missing file."""
        with pytest.raises(FileNotFoundError):
            from_pickle("non_existing_file.pkl.gz")

    def test_from_pickle_empty_file(self):
        """from_pickle() raises EOFError for an empty gzip file."""
        with gzip.open("empty.pkl.gz", "wb"):
            pass
        with pytest.raises(EOFError):
            from_pickle("empty.pkl.gz")


# Tests of the IO public API below run in a fresh temporary working
# directory (in_tmp_path), which is where load() and write() put their
# output. Paths passed to write() are kept under that directory (see
# issue-log.md #22). Code paths with known bugs (issue-log.md) are
# intentionally not tested here; their tests should come with the fixes.


def write_inputs_from_files(rows, file_name="inputs_from_files.csv"):
    """Writes an `inputs_from_files` table in the working directory.

    rows: list of (file path, table names, query only) tuples
    """
    df = pd.DataFrame(rows, columns=["File Path", "Table Name", "Query Only"])
    path = os.path.join(os.getcwd(), file_name)
    df.to_csv(path, index=False)
    return path


def write_db(file_name, tables):
    """Writes a dict of dataframes to a new sqlite db in the working directory."""
    path = os.path.join(os.getcwd(), file_name)
    with sqlite3.connect(path) as con:
        for name, df in tables.items():
            df.to_sql(name, con, index=False)
    con.close()
    return path


def read_db_table(db_path, table_name):
    with sqlite3.connect(db_path) as con:
        df = pd.read_sql(f"SELECT * FROM '{table_name}'", con)
    con.close()
    return df


@pytest.mark.usefixtures("in_tmp_path")
class TestLoadOutput:
    """What IO.load() returns and writes for test.xlsx, which has a
    `run_parameters` table (version v123, output path `output`).
    """

    def test_return_keys_run_tag_and_outpath(self):
        """load() returns tables, outpath, run_tag and db keys; the outpath is
        `<cwd>/output/<run_tag>` and the run tag is `<version>_<timestamp>`.
        """
        res = IO(TEST_XLSX).load()

        assert set(res) == LOAD_KEYS | DB_KEYS
        # version 'v123' comes from the run_parameters table
        assert re.fullmatch(r"v123_" + SHORT_TS, res["run_tag"])
        # run_parameters 'Output Path' is 'output', relative to the CWD
        assert res["outpath"] == os.path.join(os.getcwd(), "output", res["run_tag"])
        assert os.path.isdir(res["outpath"])

    def test_saves_copy_of_input_file(self):
        """load() copies the input file into the outpath as `<name>_<run_tag>.<ext>`."""
        res = IO(TEST_XLSX).load()

        copied = os.path.join(res["outpath"], "test_" + res["run_tag"] + ".xlsx")
        assert os.path.isfile(copied)
        assert filecmp.cmp(copied, TEST_XLSX, shallow=False)

    def test_db_contains_loaded_tables(self):
        """load() writes every loaded table to `<outpath>/<run_tag>.db`."""
        res = IO(TEST_XLSX).load()

        assert res["db_path"] == os.path.join(res["outpath"], res["run_tag"] + ".db")
        tables = res["tables_as_dict_of_dfs"]
        for name, df in tables.items():
            assert_frame_equal(read_db_table(res["db_path"], name), df, obj=name)

    def test_db_connection_closed_by_default(self):
        """load() closes the returned db connection by default (close_db=True)."""
        res = IO(TEST_XLSX).load()

        with pytest.raises(sqlite3.ProgrammingError):
            res["db_conn"].execute("SELECT 1")

    def test_close_db_false_keeps_connection_open(self):
        """load(close_db=False) returns an open, usable db connection."""
        res = IO(TEST_XLSX).load(close_db=False)

        try:
            (count,) = (
                res["db_conn"].execute("SELECT COUNT(*) FROM xlsx_table1").fetchone()
            )
        finally:
            res["db_conn"].close()

        assert count == len(res["tables_as_dict_of_dfs"]["xlsx_table1"])

    def test_create_db_false(self):
        """load(create_db=False) writes no db and returns no db keys."""
        res = IO(TEST_XLSX).load(create_db=False)

        assert set(res) == LOAD_KEYS
        assert os.listdir(res["outpath"]) == ["test_" + res["run_tag"] + ".xlsx"]

    def test_save_input_false(self):
        """load(save_input=False) writes the db but no copy of the input file."""
        res = IO(TEST_XLSX).load(save_input=False)

        assert os.listdir(res["outpath"]) == [res["run_tag"] + ".db"]

    def test_skip_writeout_writes_nothing(self, caplog):
        """load(skip_writeout=True) writes nothing, returns no db keys, and warns that
        save_input and create_db are ignored.
        """
        with caplog.at_level(logging.WARNING, logger="adapter.i_o"):
            res = IO(TEST_XLSX).load(skip_writeout=True)

        assert set(res) == LOAD_KEYS
        assert res["outpath"].endswith("_will_not_be_used")
        assert os.listdir(os.getcwd()) == []
        assert "No input will be written out" in caplog.text
        assert "No database will be created" in caplog.text

    def test_quick_db_out_filename(self):
        """load(quick_db_out_filename=...) writes `<name>.db` and the input copy to the cwd,
        using the given name instead of a run tag.
        """
        res = IO(TEST_XLSX).load(quick_db_out_filename="quick")

        assert res["run_tag"] == "quick"
        assert res["outpath"] == os.getcwd()
        assert res["db_path"] == os.path.join(os.getcwd(), "quick.db")
        assert os.path.isfile(res["db_path"])
        assert os.path.isfile(os.path.join(os.getcwd(), "test_quick.xlsx"))

    def test_skip_writeout_without_save_input_or_db_logs_no_warnings(self, caplog):
        """load(skip_writeout=True) doesn't warn when save_input and create_db are off."""
        with caplog.at_level(logging.WARNING, logger="adapter.i_o"):
            IO(TEST_XLSX).load(skip_writeout=True, save_input=False, create_db=False)

        assert caplog.text == ""

    def test_long_timestamp_format(self):
        """load(ts_format="long") uses a `YYYY_MM_DD_HHh_MMm` timestamp in the run tag."""
        res = IO(TEST_XLSX).load(skip_writeout=True, ts_format="long")

        assert re.fullmatch(r"v123_" + LONG_TS, res["run_tag"])


@pytest.mark.usefixtures("in_tmp_path")
class TestLoadRunParameters:
    """How IO.load() builds the run tag and outpath from `run_parameters`."""

    def test_without_run_parameters_uses_cwd_output_folder(self):
        """Without a `run_parameters` table, load() writes to `<cwd>/output` and the run
        tag has no version.
        """
        res = IO(TEST_DB).load()

        assert re.fullmatch(r"_" + SHORT_TS, res["run_tag"])
        assert res["outpath"] == os.path.join(os.getcwd(), "output", res["run_tag"])
        assert os.path.isfile(res["db_path"])

    def test_first_run_parameters_table_alphabetically_is_used(self, caplog):
        """With several `run_parameters*` tables, load() uses the alphabetically first
        one and logs a warning.
        """
        # test1.xlsx (loaded first) has `run_parameters30` with version
        # 'vTest'; test.xlsx has `run_parameters` with version 'v123'
        path = write_inputs_from_files(
            [(TEST1_XLSX, None, None), (TEST_XLSX, None, None)]
        )

        with caplog.at_level(logging.WARNING, logger="adapter.i_o"):
            res = IO(path).load(skip_writeout=True)

        assert {"run_parameters", "run_parameters30"} <= set(
            res["tables_as_dict_of_dfs"]
        )
        assert re.fullmatch(r"v123_" + SHORT_TS, res["run_tag"])
        assert "Additional run parameters table(s)" in caplog.text

    def test_float_version_drops_trailing_zero_decimal(self):
        """A numeric version read as 123.0 becomes `123` in the run tag."""
        # e.g. a version '123' stored as a number in a db or Excel cell
        run_parameters = pd.DataFrame({"Output Path": ["output"], "Version": [123.0]})
        path = write_db("run.db", {"run_parameters": run_parameters})

        res = IO(path).load(skip_writeout=True)

        assert re.fullmatch(r"123_" + SHORT_TS, res["run_tag"])

    def test_version_dots_and_slashes_are_removed(self):
        """`.`, `/` and `\\` are removed from the version in the run tag."""
        run_parameters = pd.DataFrame(
            {"Output Path": ["output"], "Version": ["v1.2/3\\4"]}
        )
        path = write_db("run.db", {"run_parameters": run_parameters})

        res = IO(path).load(skip_writeout=True)

        assert re.fullmatch(r"v1234_" + SHORT_TS, res["run_tag"])


@pytest.mark.usefixtures("in_tmp_path")
class TestLoadInputsFromFiles:
    """IO.load() of an `inputs_from_files` table that lists further input files."""

    def test_query_only_tables_are_not_loaded(self):
        """Tables flagged `Query Only` = Y are not loaded."""
        path = write_inputs_from_files([(TEST_DB, "table1, table2, table3", "N, Y, N")])

        tables = IO(path).load(skip_writeout=True)["tables_as_dict_of_dfs"]

        assert set(tables) == {"inputs_from_files", "table1", "table3"}

    def test_table_names_select_tables_from_excel(self):
        """`Table Name` limits which tables are loaded from a listed Excel file."""
        path = write_inputs_from_files([(TEST_XLSX, "xlsx_table1, xlsx_table2", None)])

        tables = IO(path).load(skip_writeout=True)["tables_as_dict_of_dfs"]

        assert set(tables) == {"inputs_from_files", "xlsx_table1", "xlsx_table2"}

    def test_inputs_from_files_table_is_returned(self):
        """The `inputs_from_files` table itself is returned with the loaded tables."""
        rows = [(TEST_DB, "table1", "N")]
        path = write_inputs_from_files(rows)

        tables = IO(path).load(skip_writeout=True)["tables_as_dict_of_dfs"]

        assert tables["inputs_from_files"]["File Path"].tolist() == [TEST_DB]


@pytest.mark.usefixtures("in_tmp_path")
class TestLoadOptions:
    """Other IO.load() options and input handling."""

    def test_csv_unnamed_index_column_is_dropped(self):
        """load() drops a CSV's unnamed index column (`Unnamed: 0`)."""
        df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        df.to_csv("data.csv")  # writes the index as an unnamed first column

        tables = IO(os.path.abspath("data.csv")).load(skip_writeout=True)[
            "tables_as_dict_of_dfs"
        ]

        assert list(tables) == ["data"]
        assert_frame_equal(tables["data"], df)

    def test_set_first_col_as_index_for_all_tables(self):
        """load(set_first_col_as_index=True) indexes every table by its first column."""
        expected = IO(TEST_DB).load(skip_writeout=True)["tables_as_dict_of_dfs"]

        tables = IO(TEST_DB).load(skip_writeout=True, set_first_col_as_index=True)[
            "tables_as_dict_of_dfs"
        ]

        for name, df in expected.items():
            first_col = df.columns[0]
            assert_frame_equal(tables[name], df.set_index(first_col), obj=name)

    def test_set_first_col_as_index_for_listed_tables(self):
        """load(set_first_col_as_index=[...]) indexes only the listed tables."""
        expected = IO(TEST_DB).load(skip_writeout=True)["tables_as_dict_of_dfs"]

        tables = IO(TEST_DB).load(
            skip_writeout=True, set_first_col_as_index=["table1"]
        )["tables_as_dict_of_dfs"]

        assert_frame_equal(tables["table1"], expected["table1"].set_index("column1"))
        assert_frame_equal(tables["table2"], expected["table2"])
        assert_frame_equal(tables["table3"], expected["table3"])

    def test_to_numeric_converts_listed_numeric_text_table(self):
        """load(to_numeric=[...]) converts a listed table of numeric text to numbers and
        leaves unlisted tables as text.
        """
        text_numbers = pd.DataFrame({"a": ["1", "2"], "b": ["3.5", "4"]})
        path = write_db("numbers.db", {"numbers": text_numbers, "other": text_numbers})

        tables = IO(path).load(skip_writeout=True, to_numeric=["numbers"])[
            "tables_as_dict_of_dfs"
        ]

        numbers = tables["numbers"]
        assert all(pd.api.types.is_numeric_dtype(t) for t in numbers.dtypes)
        assert numbers["a"].tolist() == [1, 2]
        assert numbers["b"].tolist() == [3.5, 4]
        # tables not listed are left as text
        assert_frame_equal(tables["other"], text_numbers)

    def test_column_labels_are_cleaned_by_default(self):
        """load() strips column labels and collapses repeated spaces (clean_labels=True)."""
        # the Excel table's raw labels are ' label 1 ' and 'label 2 '
        tables = IO(TEST_LABELS_XLSX).load(skip_writeout=True)["tables_as_dict_of_dfs"]

        assert list(tables["Table1"].columns) == ["label 1", "label 2"]

    def test_load_from_none_returns_no_tables(self):
        """IO(None).load() reads no input: it returns no tables, with the usual result keys."""
        res = IO(None).load()

        assert res["tables_as_dict_of_dfs"] == {}
        assert set(res) == LOAD_KEYS | DB_KEYS


@pytest.mark.usefixtures("in_tmp_path")
class TestWrite:
    """IO.write() of a dict of dataframes to csv files and/or a sqlite db."""

    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})

    def test_csv_to_explicit_outpath(self):
        """write(type="csv") writes each table to `<outpath>/<name>_<run_tag>.csv`."""
        outpath = os.path.join(os.getcwd(), "out")

        IO(None).write(
            type="csv",
            data_as_dict_of_dfs={"t": self.df},
            outpath=outpath,
            run_tag="r1",
        )

        written = pd.read_csv(os.path.join(outpath, "t_r1.csv"), index_col=0)
        assert_frame_equal(written, self.df)

    def test_csv_defaults_to_cwd(self):
        """write() without a data_connection or outpath writes to the cwd."""
        IO(None).write(type="csv", data_as_dict_of_dfs={"t": self.df})

        assert os.listdir(os.getcwd()) == ["t_.csv"]

    def test_db_from_load_result(self):
        """write(type="db") adds tables to the db created by load(), keeping its tables."""
        data_conn = IO(TEST_DB).load()

        IO(TEST_DB).write(
            type="db",
            data_connection=data_conn,
            data_as_dict_of_dfs={"new_table": self.df},
        )

        assert_frame_equal(read_db_table(data_conn["db_path"], "new_table"), self.df)
        # tables written by load() are kept
        assert_frame_equal(
            read_db_table(data_conn["db_path"], "table1"),
            data_conn["tables_as_dict_of_dfs"]["table1"],
        )

    def test_db_and_csv_from_load_result(self):
        """write(type="db&csv") writes new tables to load()'s db and as csv files in its
        outpath.
        """
        data_conn = IO(TEST_DB).load()

        IO(TEST_DB).write(
            type="db&csv",
            data_connection=data_conn,
            data_as_dict_of_dfs={"new_table": self.df},
        )

        assert_frame_equal(read_db_table(data_conn["db_path"], "new_table"), self.df)
        csv_path = os.path.join(
            data_conn["outpath"], "new_table_" + data_conn["run_tag"] + ".csv"
        )
        assert_frame_equal(pd.read_csv(csv_path, index_col=0), self.df)

    def test_explicit_outpath_overrides_load_result(self):
        """An explicit outpath takes precedence over the outpath in load()'s result."""
        data_conn = IO(TEST_DB).load()
        outpath = os.path.join(os.getcwd(), "other")

        IO(TEST_DB).write(
            type="csv",
            data_connection=data_conn,
            data_as_dict_of_dfs={"t": self.df},
            outpath=outpath,
        )

        assert os.listdir(outpath) == ["t_" + data_conn["run_tag"] + ".csv"]

    def test_raises_without_data(self):
        """write() raises ValueError when there is no data to write."""
        with pytest.raises(ValueError):
            IO(None).write(type="csv")

    def test_raises_when_data_is_not_a_dict(self):
        """write() raises ValueError when the data isn't a dict of dataframes."""
        with pytest.raises(ValueError):
            IO(None).write(type="csv", data_as_dict_of_dfs=self.df)

    def test_db_raises_without_db_connection(self):
        """write(type="db") raises ValueError without a db connection."""
        with pytest.raises(ValueError):
            IO(None).write(type="db", data_as_dict_of_dfs={"t": self.df})


@pytest.mark.usefixtures("in_tmp_path")
class TestHelpers:
    """Smaller IO methods that downstream packages may call directly."""

    @pytest.mark.parametrize(
        "path, file_type",
        [
            ("inputs.xlsx", "excel"),
            ("inputs.db", "database"),
            ("inputs.sqlite", "database"),
            ("inputs.csv", "text"),
            ("server.lbl.gov/database", "sqlalchemy"),
        ],
    )
    def test_get_file_type(self, path, file_type):
        """IO.get_file_type() maps file extensions (and lbl.gov hosts) to input types."""
        assert IO(None).get_file_type(path) == file_type

    def test_os_mapping_list_of_tuples_is_converted(self):
        """IO accepts the legacy list-of-tuples os_mapping and converts it to a dict."""
        i_o = IO(None, os_mapping=[("A:", "/Volumes/A")])

        assert i_o.os_mapping["win32"] == "A:"
        assert i_o.os_mapping["darwin"] == "/Volumes/A"

    def test_default_os_mapping_is_not_shared_between_instances(self):
        """Changing one IO's default os_mapping doesn't change the default for new IOs."""
        IO(None).os_mapping["darwin"] = "/Volumes/Changed"

        assert IO(None).os_mapping == {
            "win32": "X:",
            "darwin": "/Volumes/A",
            "linux": "/media/b",
        }

    def test_first_col_to_index_raises_for_unsupported_table_names(self):
        """IO.first_col_to_index() raises ValueError for table_names other than a bool or list."""
        with pytest.raises(ValueError):
            IO(None).first_col_to_index(
                {"t": pd.DataFrame({"a": [1]})}, table_names="t"
            )

    def test_process_column_labels_converts_to_str_and_strips(self):
        """IO.process_column_labels() also converts non-string labels to str."""
        assert IO(None).process_column_labels([1, " a  b ", "c"]) == ["1", "a b", "c"]

    def test_create_db_defaults_to_cwd_output_folder(self):
        """IO.create_db() without an outpath writes `<cwd>/output/<run_tag>.db`."""
        df = pd.DataFrame({"a": [1, 2]})

        res = IO(None).create_db({"t": df}, run_tag="r1")

        assert res["db_path"] == os.path.join(os.getcwd(), "output", "r1.db")
        assert_frame_equal(read_db_table(res["db_path"], "t"), df)

    def test_create_db_raises_when_a_table_cannot_be_written(self):
        """IO.create_db() raises ValueError, caused by the original error, when a table
        can't be written to sqlite.
        """
        # sqlite can't store a table with duplicate column labels
        df = pd.DataFrame([[1, 2]], columns=["a", "a"])

        with pytest.raises(ValueError) as exc_info:
            IO(None).create_db({"t": df}, run_tag="r1")

        assert exc_info.value.__cause__ is not None

    def test_create_db_skip_writeout(self):
        """IO.create_db(skip_writeout=True) writes nothing and returns placeholder values."""
        res = IO(None).create_db({"t": pd.DataFrame({"a": [1]})}, skip_writeout=True)

        assert res == {"db_path": "no_output_written", "db_conn": "no_output_written"}
        assert os.listdir(os.getcwd()) == []


@pytest.mark.parametrize("input_file", sorted(GOLDEN_CASES))
def test_load_matches_golden(input_file, tmp_path, monkeypatch):
    """IO.load() of each GOLDEN_CASES input matches its golden fixture (tables,
    columns, dtypes, values); see "Golden fixtures" in the root README.md.
    """
    if GOLDEN_CASES[input_file]:
        # the input references other files with repo-relative paths
        monkeypatch.chdir(REPO_ROOT)
    else:
        monkeypatch.chdir(tmp_path)

    tables = IO(os.path.join(INPUTS_DIR, input_file)).load(skip_writeout=True)[
        "tables_as_dict_of_dfs"
    ]
    with open(golden_path(input_file)) as f:
        golden = json.load(f)

    assert sorted(tables) == sorted(golden["tables"])

    for name, expected in golden["tables"].items():
        actual = tables[name]
        assert [str(c) for c in actual.columns] == expected["columns"], name
        assert {str(c): str(t) for c, t in actual.dtypes.items()} == expected[
            "dtypes"
        ], name
        # compare both in the golden representation, where None and NaN
        # missing values in object columns are the same
        assert_frame_equal(
            golden_to_frame(frame_to_golden(actual)),
            golden_to_frame(expected),
            check_exact=False,
            rtol=GOLDEN_RTOL,
            obj=name,
        )
