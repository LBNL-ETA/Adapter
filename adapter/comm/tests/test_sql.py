import logging
import os
import sqlite3

from pathlib import Path

import pytest

from adapter.comm.sql import Sql

import pandas as pd

logging.basicConfig(level=logging.DEBUG)


# each test gets a fresh test db in a temporary folder,
# so tests don't depend on each other or on the run order
class SqlTests:
    """comm.sql.Sql: writing and reading pandas dataframes to and from a sqlite db."""

    @pytest.fixture(autouse=True)
    def _setup_db(self, tmp_path):
        """Creates a fresh sqlite db in a temporary folder, and the example
        data, for each test.
        """
        test_db_name = "test.db"
        test_db_fulpath = str(tmp_path / test_db_name)
        self.test_db_fulpath = test_db_fulpath

        print(test_db_fulpath)
        # create test db

        # https://stackoverflow.com/questions/1158076/implement-touch-using-python
        Path(test_db_fulpath).touch()

        self.sql_api = Sql(test_db_fulpath)

        # example dict to write to db
        self.df = pd.DataFrame(data=[["a", 1], ["b", 2]], columns=["comp", "cost"])

        # example dict to write to db as table
        self.dict = {"k1": [12, 13, 14], "k2": ["a", "b", "c"]}

        # example csv data
        self.path_to_csv = os.path.join(os.path.dirname(__file__), "table.csv")

        # sql code to execute
        self.raw_sql = """CREATE TABLE sys_components
(
 Component TEXT NOT NULL ,
 Function  TEXT NOT NULL ,

PRIMARY KEY (Component)
);"""

        yield

        # close the test db; tmp_path is cleaned up by pytest
        self.sql_api.db.close()

    def test_b_csv2table(self):
        """Sql.csv2table() writes a csv file to the db as a table."""
        self.sql_api.csv2table(self.path_to_csv, "csv2table")

    def test_c_table2pd(self):
        """Sql.table2pd() reads a table back as the dataframe that was written."""
        # write the table first, so this test does not depend on other tests
        self.sql_api.pd2table(self.df, "pd2table")
        df = self.sql_api.table2pd("pd2table")
        assert (df == self.df).all().all()

    def test_d_commit(self):
        """Sql.commit() executes a raw SQL statement (here CREATE TABLE)."""
        assert self.sql_api.commit(self.raw_sql)

    def test_e_tables2dict(self):
        """Sql.tables2dict() reads all tables into a dict of dataframes."""
        # write the table first, so this test does not depend on other tests
        self.sql_api.pd2table(self.df, "pd2table")
        data = self.sql_api.tables2dict()
        assert data["pd2table"].iloc[1, 1] == 2

    def test_accepts_existing_connection(self):
        """Sql() wraps an already open sqlite3 connection."""
        assert Sql(self.sql_api.db).db is self.sql_api.db

    def test_raises_for_unsupported_argument(self):
        """Sql() raises ValueError for anything but a path or a sqlite3 connection."""
        with pytest.raises(ValueError):
            Sql(42)

    def test_pd2table_close_closes_connection(self):
        """Sql.pd2table(close=True) closes the connection after writing."""
        self.sql_api.pd2table(self.df, "pd2table", close=True)

        with pytest.raises(sqlite3.ProgrammingError):
            self.sql_api.db.execute("SELECT 1")

    def test_commit_close_closes_connection(self):
        """Sql.commit(close=True) closes the connection after executing."""
        assert self.sql_api.commit(self.raw_sql, close=True)

        with pytest.raises(sqlite3.ProgrammingError):
            self.sql_api.db.execute("SELECT 1")

    def test_tables2dict_close_false_keeps_connection_open(self):
        """Sql.tables2dict(close=False) leaves the connection open."""
        self.sql_api.pd2table(self.df, "pd2table")

        data = self.sql_api.tables2dict(close=False)

        assert data["pd2table"].equals(self.df)
        self.sql_api.db.execute("SELECT 1")  # still open
