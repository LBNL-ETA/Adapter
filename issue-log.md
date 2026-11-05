# Issue Log

Pre-existing bugs and edge cases discovered during modernization. Each entry
records where the problem is and how to reproduce it. Fixes go in separate,
dedicated changes.

## 1. `test_load_from_excel_no_named_ranges` looks for its fixture in the wrong directory

- **File:** `adapter/tests/test_i_o.py:17`, `adapter/tests/test_i_o.py:124`
- **Found:** 2026-10-22, while converting the test suite from unittest to pytest
  (the failure is present under both runners).
- **Problem:** `setup_method` (previously `setUp`) sets `self.test_dir = os.getcwd()`,
  and the test builds `os.path.join(self.test_dir, "test_no_named_ranges.xlsx")`.
  The fixture actually lives at `adapter/tests/test_no_named_ranges.xlsx`, so
  the path is only correct if the suite is run from inside `adapter/tests/`.
  The other tests in the class use `os.path.join(os.getcwd(), r"adapter/tests/...")`.
- **Reproduce:** from the repo root, run
  `uv run pytest adapter/tests/test_i_o.py -k no_named_ranges`
  → `FileNotFoundError: [Errno 2] No such file or directory: '<repo>/test_no_named_ranges.xlsx'`.
  (`uv run python -m unittest discover` gives the same error.)
- **Cause:** regression from commit `55f7b67` ("fixed the path compatibility for
  windows"), which replaced `os.path.join(os.getcwd(), r"adapter/tests/test_no_named_ranges.xlsx")`
  with `os.path.join(self.test_dir, "test_no_named_ranges.xlsx")` where `self.test_dir = os.getcwd()`.
- **Status:** Resolved. `self.test_dir` is now `os.path.dirname(__file__)`, so the
  path is correct from any working directory. The test's assertion is unchanged.

## 2. `SqlTests` modifies a tracked file on every run

- **File:** `adapter/comm/tests/test_sql.py:61-71`
- **Problem:** `teardown_class` (previously `tearDownClass`) renames the working
  `test.db` to `adapter/comm/tests/test_done.db`, overwriting it. That file is
  committed, so every test run leaves it modified in `git status`.
- **Reproduce:** start from a clean checkout, run `uv run pytest adapter/comm/tests/test_sql.py`,
  then `git status` → `modified: adapter/comm/tests/test_done.db`.
- **Status:** Resolved. Each test now uses a fresh db in pytest's `tmp_path`, and nothing
  is written to `test_done.db`. The committed file is no longer used by any test
  (`test_tools.py` only uses its name as a relative-path string), so it can be removed.

## 3. Test order dependency in `SqlTests`

- **File:** `adapter/comm/tests/test_sql.py`
- **Problem:** `test_c_table2pd` and `test_e_tables2dict` read the `pd2table`
  table that `test_a_pd2table` writes. They pass only because the tests run in
  alphabetical/definition order against a shared class-level database.
- **Reproduce:** `uv run pytest adapter/comm/tests/test_sql.py -k table2pd`
  (runs `test_c` without `test_a`) → fails because `pd2table` doesn't exist.
- **Status:** Resolved. `test_c_table2pd` and `test_e_tables2dict` write `pd2table`
  themselves, and each test gets its own db.
  `test_a_pd2table` (which had no assertions) was later removed as redundant.

## 4. Tests write scratch files to the current working directory

- **File:** `adapter/tests/test_i_o.py` (`TestPickle`), `adapter/tests/test_i_o.py`
  (`IOTests` writes to `./output/`)
- **Problem:** pickle tests create `data.pickle.gz`, `test.pkl.gz`, and `empty.pkl.gz`
  in the CWD. Some `IOTests` load calls (e.g. `test_load_from_csv_inputs_from_files`,
  `test_load_from_db`) create `output/<version>_<timestamp>/` without removing it.
  If an assertion fails before the manual `os.remove`/`shutil.rmtree`, files are left behind.
- **Reproduce:** run `uv run pytest` from the repo root, then `ls output/`.
- **Status:** Resolved for test runs. `TestPickle` and all new tests run in a temporary
  working directory. `IOTests` still has to run from the repo root (its inputs, such as
  `inputs_from_files_vTest.csv`, use repo-relative paths), so the `clean_output` fixture
  in `adapter/tests/conftest.py` removes the `output/` entries each test creates.

## 5. Deprecated `pd.to_numeric(errors="ignore")`

- **File:** `adapter/i_o.py:387-389`
- **Problem:** `errors="ignore"` emits a pandas `FutureWarning` and will raise in
  pandas 3.x. This blocks the planned pandas upgrade.
- **Reproduce:** `uv run pytest adapter/tests/test_i_o.py -k to_numeric`
  → `FutureWarning: errors='ignore' is deprecated ...`.
- **Status:** Resolved on branch `upgrade_pandas_3` together with #21: `to_numeric`
  conversion no longer passes `errors="ignore"` (removed in pandas 3.0); see #21.

## 6. Duplicate table from a CSV input silently overwrites an existing table

- **File:** `adapter/to_python.py:398-406` (`Debugger.check_for_duplicates`, string branch),
  reached from `adapter/i_o.py:529`.
- **Problem:** when `table_names` is a single string (the CSV path), a duplicate
  raises `ValueError` inside a bare `try/except`, which catches it, logs
  "Unexpected table_name format", and returns. The CSV then replaces the
  previously loaded table with no error. The list branch (Excel/db) raises correctly,
  which is why `test_throws_error_at_duplication` passes: its CSV is listed *before* the Excel file.
- **Reproduce:** create an `inputs_from_files.csv` listing `adapter/tests/inputs/test.xlsx`
  first and `adapter/tests/inputs/xlsx_table1.csv` second, then `IO(<that csv>).load(skip_writeout=True)`
  → no error; `xlsx_table1` holds the CSV's data. Directly:
  `Debugger.check_for_duplicates(["xlsx_table1"], "xlsx_table1")` returns `None`.
- **Expected:** `ValueError` regardless of input order, matching the list branch.
- **Status:** Resolved on branch `upgrade_pandas_3`: the self-catching `try`/`except` in
  the string branch is removed, so a single duplicate name logs and raises `ValueError`
  like the list branch (see #34). Tests: `TestDebugger.test_duplicate_single_table_name_raises`,
  `TestLoadInputsFromFiles.test_duplicate_table_from_later_csv_raises` (both fail on the
  old code).

## 7. `from_pickle` fails on DataFrames and on falsy objects

- **File:** `adapter/i_o.py:913-914`
- **Problem:** `if not py_object:` is used as an emptiness check. For a DataFrame it raises
  `ValueError: The truth value of a DataFrame is ambiguous`. For valid falsy objects
  (`{}`, `[]`, `0`) it raises `EOFError("The file is empty.")`.
- **Reproduce:** `to_pickle(pd.DataFrame({"a": [1]}), "p.gz"); from_pickle("p.gz")` → `ValueError`.
  `to_pickle({}, "p.gz"); from_pickle("p.gz")` → `EOFError`.
- **Expected:** round-trips any picklable object. An empty file still raises `EOFError`
  (already raised by `pickle`/`pd.read_pickle` itself).

## 8. Unsupported input path types/extensions crash with `UnboundLocalError`

- **File:** `adapter/i_o.py:74-75`, `adapter/i_o.py:508-566` (`get_tables`)
- **Problem:** a `pathlib.Path` input is not a `str`, so `get_tables` takes the
  "unsupported value" branch, logs, and returns an unassigned `dict_of_dfs`.
  An unsupported extension (e.g. `.txt`) gets `file_type == ""`, matches no branch,
  and hits the same unassigned variable.
- **Reproduce:** `IO(pathlib.Path("adapter/tests/inputs/test.db")).load(skip_writeout=True)` or
  `IO("x.txt").load(skip_writeout=True)` → `UnboundLocalError: cannot access local variable 'dict_of_dfs'`.
- **Expected:** `pathlib.Path` is accepted like `str` (common for downstream callers);
  unsupported types/extensions raise a clear `ValueError`/`TypeError`.
- **Status:** Resolved on branch `fix_pyrefly_errors`. `IO()` and `IO.get_tables()` accept
  `os.PathLike` (converted with `os.fspath`); `IO()` raises `TypeError` for any other type but
  `str`/`None`; `get_tables()` raises `ValueError("Unsupported input file type for <path>.")`
  for unknown extensions (`get_file_type()` still returns `""` for them, so constructing an
  `IO` doesn't fail). Tests: `TestLoadOptions.test_accepts_pathlib_path`,
  `test_unsupported_file_extension_raises`, `TestHelpers.test_unsupported_path_type_raises`.

## 9. Blank "Table Name" for a `.db` row in `inputs_from_files` crashes

- **File:** `adapter/i_o.py:235-252`, `adapter/to_python.py:290-292` (`Db.load`)
- **Problem:** a blank cell is read as `NaN` (a float) and passed as `table_names`.
  `Excel.load` treats `NaN` as "load all", but `Db.load` does `set(table_names)`.
- **Reproduce:** `inputs_from_files.csv` with one row `adapter/tests/inputs/test.db,,` →
  `IO(<that csv>).load(skip_writeout=True)` → `TypeError: 'numpy.float64' object is not iterable`.
- **Expected:** blank means "load all tables", as for Excel and CSV rows.
- **Status:** Resolved on branch `fix_pyrefly_errors`: `IO.load()` treats blank (NaN)
  `Table Name` and `Query Only` cells as not given (`None`), so a db row with a blank
  `Table Name` loads all its tables. Test:
  `TestLoadInputsFromFiles.test_blank_table_name_loads_all_tables_from_db`.

## 10. Non-string, non-".0" `Version` in `run_parameters` crashes

- **File:** `adapter/i_o.py:306-317`
- **Problem:** only floats ending in `.0` are converted to `str`. An int (e.g. from a
  CSV or db `run_parameters` table) or a float such as `1.5` reaches `re.sub` and
  raises `TypeError: expected string or bytes-like object`.
- **Reproduce:** a `run_parameters` table with `Version` = `5` (integer column) →
  `IO(...).load()` → `TypeError`.
- **Expected:** any scalar version is converted to a string before cleaning.

## 11. Swallowed `create_db` failure turns into `UnboundLocalError`

- **File:** `adapter/i_o.py:352-366`, `adapter/i_o.py:397-399`
- **Problem:** a bare `except:` around `self.create_db(...)` logs the error, leaving
  `db_res` unassigned; `res.update(db_res)` then raises `UnboundLocalError`, hiding the
  original exception.
- **Reproduce:** any `db_flavor` other than `"sqlite"` (the only implemented one) makes
  `create_db` fail (`db_out_type` is unassigned, `i_o.py:626-633`):
  `IO("adapter/tests/inputs/test.db").load(db_flavor="postgres")` →
  `UnboundLocalError: cannot access local variable 'db_res'`.
- **Expected:** the original exception propagates (or a clear error is raised).
- **Status:** Resolved on branch `fix_pyrefly_errors`. `IO.load()` logs and then raises
  `ValueError("Not able to create a db ...")` from the original error (decision: raise rather
  than continue). `IO.create_db()` raises `ValueError("Unsupported db flavor ...")` for any
  flavor but `"sqlite"`, before creating anything. Tests:
  `TestLoadOutput.test_raises_when_db_cannot_be_created`,
  `TestHelpers.test_create_db_raises_for_unsupported_flavor`.
  - Changed on branch `upgrade_pandas_3` (#34): `IO.load()` now re-raises the original
    error with a note naming the input file, instead of a `ValueError("Not able to create
    a db ...")`.

## 12. `to_numeric` passed as a string is silently ignored

- **File:** `adapter/i_o.py:375-389`
- **Problem:** a non-list value is logged as an error, but processing continues:
  `key in tb_nm for tb_nm in "table1"` compares table names with single characters,
  so nothing is converted and no exception is raised. Note also that matching is
  `key in tb_nm` (table name is a *substring* of a requested name).
- **Reproduce:** `IO("adapter/tests/inputs/test.db").load(skip_writeout=True, to_numeric="table1")`
  → no conversion, no exception.
- **Expected:** raise `TypeError`/`ValueError` for non-list input (or accept a single string).

## 13. `comm.tools.process_column_labels` never cleans anything

- **File:** `adapter/comm/tools.py:23-26`
- **Problem:** the condition `lbl is str` compares a value with the `str` type and is
  always `False`, so labels are returned unchanged. `Excel.load` (`to_python.py:154`)
  relies on it. `IO.load(clean_labels=True)` masks this by cleaning again with
  `IO.process_column_labels`, but `clean_labels=False` and direct `Excel` users get raw labels.
- **Reproduce:** `process_column_labels(["  a   b "])` → `["  a   b "]`.
- **Expected:** `["a b"]` (presumably `isinstance(lbl, str)` was intended).
- **Status:** Resolved on branch `fix_pyrefly_errors`: `isinstance(lbl, str)`. Excel tables now
  have cleaned labels when loaded, including with `IO.load(clean_labels=False)` (CSV and db
  inputs still keep their raw labels then). Tests: `Test.test_process_column_labels`,
  `ExcelTest.test_load_cleans_column_labels`; golden fixtures unchanged.

## 14. `IO.write` returns `None`, docstring says `True`

- **File:** `adapter/i_o.py:737-739`
- **Reproduce:** `IO(...).write(type="csv", data_as_dict_of_dfs={"t": df}, outpath=d)` → `None`.
- **Expected:** decide on one; either return `True` or fix the docstring.

## 15. Module-level `tkinter` import makes `IO` unimportable without Tk

- **File:** `adapter/comm/tools.py:6-7`
- **Problem:** `tkinter` is imported at module import time only for `user_select_file`.
  `adapter.i_o` imports `adapter.comm.tools`, so `from adapter.i_o import IO` fails with
  `ModuleNotFoundError: No module named '_tkinter'` on Python builds without Tk
  (e.g. many slim Docker images). Packaging risk; not reproduced locally.
- **Expected:** import `tkinter` lazily inside `user_select_file`.

## 16. `adapter/comm/excel.py` is unused

- **File:** `adapter/comm/excel.py` (711 lines)
- **Problem:** not imported by the package or by any test (0% coverage). It is the only
  user of the `xlwings` dependency. Decide whether to remove it (and possibly `xlwings`)
  in a dedicated change.
- **Status:** Resolved on branch `upgrade_pandas_3`: `excel.py` and the `xlwings` dependency
  are removed (with `appscript`, `lxml`, `psutil` and `pywin32`, which only `xlwings`
  needed). Its last user was removed in commit `cc920af` (2022), when the openpyxl-based
  `to_python.Excel` replaced it. **Breaking** for any downstream code that imports
  `adapter.comm.excel` (`Book`, `xl2pd`, `pd2xl`, ...). Its ruff and pyrefly exclusions
  (#31) are removed; total test coverage rises from 64% to 92%.

## 17. `IO.first_col_to_index(..., table_names=False)` raises `TypeError`

- **File:** `adapter/i_o.py:837-847`
- **Problem:** the `False` branch is accepted (`pass`), but the loop then runs
  `x in table_names` with `table_names=False`.
- **Reproduce:** `IO(None).first_col_to_index({"a": pd.DataFrame({"x": [1]})}, table_names=False)`
  → `TypeError: argument of type 'bool' is not iterable`.
  (`IO.load` never calls it with `False`, so `load()` is unaffected.)
- **Expected:** returns copies of all tables unchanged.
- **Status:** Resolved on branch `fix_pyrefly_errors`: `False` now selects no tables, so all
  tables are returned as unchanged copies. Test:
  `TestHelpers.test_first_col_to_index_false_returns_unchanged_copies`.

## 18. Legacy list-of-tuples `os_mapping` breaks on Linux

- **File:** `adapter/i_o.py:61-70`, `adapter/comm/tools.py:63-74`
- **Problem:** the backwards-compatible list form `[("X:", "/Volumes/A")]` is converted to
  a dict with only `win32` and `darwin` keys. On Linux, `mapping[sys.platform]` raises
  `KeyError: 'linux'` for any absolute or drive-letter path.
- **Reproduce:** with `sys.platform` patched to `"linux"`:
  `IO("/Volumes/A/x.db", os_mapping=[("X:", "/Volumes/A")])` → `KeyError: 'linux'`.
- **Expected:** a clear error explaining the list form doesn't support Linux, or
  unconverted paths returned unchanged.

## 19. `Excel.load` with a string `data_object_names` raises `TypeError`

- **File:** `adapter/to_python.py:81-91`
- **Problem:** a non-list value reaches `np.isnan(data_object_names)`, which raises
  `TypeError` for strings, so the intended "Unsupported type" `ValueError` is unreachable.
- **Reproduce:** `Excel("adapter/tests/inputs/test.xlsx").load(data_object_names="xlsx_table1")` → `TypeError: ufunc 'isnan' not supported ...`.
- **Expected:** the documented `ValueError` (or accept a single name).

## 20. `Excel.get_named_data_object` raises `KeyError` for unknown names

- **File:** `adapter/to_python.py:194-196`
- **Problem:** `self.wb.defined_names[name]` raises `KeyError` for a missing name, so
  the intended `ValueError('Range "..." not found in workbook.')` is unreachable.
- **Reproduce:** `Excel("adapter/tests/inputs/test.xlsx").get_named_data_object("nope")` → `KeyError: 'nope'`.
- **Expected:** the intended `ValueError` (e.g. use `.get(name)`).

## 21. `IO.load(to_numeric=[...])` converts row-wise, so mixed tables are untouched

- **File:** `adapter/i_o.py:387-389`
- **Problem:** `df.apply(pd.to_numeric, errors="ignore", axis=1)` converts each *row*.
  A row with any non-numeric value fails and is left as-is, so a table with one text
  column gets no conversion even in its numeric columns. Fully numeric tables are
  converted, but integer-like strings come back as `float64` because rows mix types.
  Needs a decision on intended behavior (column-wise is likely); interacts with #5 and #12.
- **Reproduce:** a db table `mixed` with columns `a=["1","2"]`, `b=["x","y"]` →
  `load(skip_writeout=True, to_numeric=["mixed"])` → column `a` stays `object`.
- **Expected:** to be decided; likely column-wise conversion of convertible columns.
- **Status:** Resolved on branch `upgrade_pandas_3` (decision: column by column). Each
  column of a listed table is converted with `pd.to_numeric` if all its values are numeric
  and left unchanged otherwise (only `ValueError`/`TypeError` are caught). Mixed tables now
  get their numeric columns converted, and integer text becomes `int64` instead of
  `float64`. #12 (non-list `to_numeric`, substring matching of table names) is unchanged.
  Tests: `TestLoadOptions.test_to_numeric_converts_numeric_columns_of_mixed_table` (new),
  `test_to_numeric_converts_listed_numeric_text_table` (unchanged, still passes).

## 22. New local absolute paths are rewritten onto the network drive

- **File:** `adapter/comm/tools.py:76-95` (`convert_network_drive_path`), used by
  `IO.__init__`, `IO.get_tables`, `IO.load` (run_parameters `Output Path`) and `IO.write`.
- **Problem:** an absolute POSIX path that doesn't exist yet and isn't under the current
  working directory is treated as a network-drive path and prefixed with the current
  OS's mount point (e.g. `/Volumes/A` on macOS). So writing to a *new* local folder
  outside the CWD fails.
- **Reproduce:** on macOS,
  `convert_network_drive_path("/tmp/adapter_new_dir")` → `"/Volumes/A/tmp/adapter_new_dir"`;
  `IO(None).write(type="csv", data_as_dict_of_dfs={"t": pd.DataFrame([1])}, outpath="/tmp/adapter_new_dir")`
  → `FileNotFoundError: ... '/Volumes/A/tmp/adapter_new_dir'`.
  The same applies to an absolute, not-yet-existing `Output Path` in `run_parameters`.
- **Expected:** only paths that start with another OS's configured mount point
  (or a drive letter) are converted; other absolute paths are returned unchanged.

## 23. `Query Only` flags without `Table Name` crash

- **File:** `adapter/i_o.py:474-502` (`get_tables`)
- **Problem:** a blank `Table Name` cell is read as `NaN`, not `None`, so the
  `table_names is None` branch (which handles "query all tables") is never taken; the
  `else` branch indexes `np.array(NaN)` with the flags and fails. The `None` branch is
  itself incomplete: for more than one flag, or a single `"N"`, `table_names_to_load`
  is never assigned.
- **Reproduce:** `inputs_from_files.csv` row `adapter/tests/inputs/test.db,,Y` (or `N`, or `"N, Y"`)
  → `IO(<that csv>).load(skip_writeout=True)` →
  `IndexError: too many indices for array: array is 0-dimensional, but 1 were indexed`.
- **Expected:** to be decided; e.g. a single flag applies to all tables, and multiple flags
  without table names raise a clear `ValueError`.
- **Status:** Resolved on branch `fix_pyrefly_errors` (decision: flags always need table
  names). `Query Only` flags without table names raise `ValueError("... without table
  names ...")`, and a different number of flags and table names raises
  `ValueError("... one flag per table.")` (it used to fail with a numpy `IndexError`).
  Tests: `TestLoadInputsFromFiles.test_query_only_flags_without_table_names_raise`,
  `test_query_only_flag_count_must_match_table_names`.

## 24. Leftover debugger import in `comm/sql.py`

- **File:** `adapter/comm/sql.py:10`
- **Problem:** `from pdb import set_trace as bp` is imported but never used. It is dead
  code, and the `debug-statements` pre-commit hook rejects any commit that includes
  this file until it is removed.
- **Reproduce:** `uv run ruff check adapter/comm/sql.py --select F401` → `F401 'pdb.set_trace' imported but unused`;
  `uv run pre-commit run debug-statements --files adapter/comm/sql.py` (after hooks are set up) fails.
- **Expected:** the import is removed.
- **Status:** Resolved. The import is removed (`bp` was never used). No test changes needed.

## 25. Invalid escape sequences in string literals

- **File:** `adapter/i_o.py:88`, `:343`, `:344`, `:520` (regex patterns `"\."`);
  `adapter/comm/tools.py:99`, `:107` (Windows paths in the `get_mount_point_len` docstring)
- **Problem:** `"\."` is not a valid Python escape sequence. Python 3.12 treats it as a
  backslash and a dot (so the regexes work) but emits `SyntaxWarning: invalid escape
  sequence` when compiling the module, and a future Python version will make it a
  `SyntaxError`, at which point `adapter.i_o` can't be imported. Found when
  reformatting forced recompilation and the warnings appeared in the pytest output.
- **Reproduce:** `uv run ruff check . --select W605` → 6 findings; or
  `python -W error::SyntaxWarning -c "import ast; ast.parse(open('adapter/i_o.py').read())"`.
- **Expected:** raw strings (`r"\."`), which compile to the same values without warnings
  (ruff's W605 fix).
- **Status:** Resolved. The regex patterns are raw strings (`r"\."`, identical patterns) and
  the `get_mount_point_len` docstring is a raw string, so its example path now reads
  `X:\Abc\1.txt` instead of containing a `\x01` character. No test changes needed.

## 26. `adapter/tests/__init__.py` imports the `comm` test module

- **File:** `adapter/tests/__init__.py:1`
- **Problem:** `import adapter.comm.tests.test_sql` was added (commit `f3fc051`) so that
  `python -m unittest discover` would find the `comm` tests. With pytest, those tests are
  collected through `testpaths`, so the import only makes importing `adapter.tests`
  also import (and configure logging in) `test_sql`.
- **Reproduce:** `python -c "import adapter.tests, sys; print('adapter.comm.tests.test_sql' in sys.modules)"` → `True`.
- **Expected:** an empty `__init__.py`.
- **Status:** Resolved. `adapter/tests/__init__.py` is empty; pytest still collects all
  89 tests (the `comm` tests via `testpaths`). No test changes needed. `python -m unittest
  discover` no longer finds the `comm` tests, but the suite now runs with pytest.

## 27. `Db_sqlalchemy.load()` fails unless `Query Only` flags are given

- **File:** `adapter/to_python.py:338-365` (`Db_sqlalchemy.load`), `adapter/i_o.py:497-499`, `:543-548`
- **Problem:** the docstring says `table_names=None` loads all tables, but the method
  iterates `for table_name in table_names`, which raises `TypeError` for `None`; the bare
  `except` turns it into `ValueError("Failed to read input tables ...")`. `IO.get_tables`
  passes `table_names_for_conn`, which is `None` unless the `inputs_from_files` row has
  `Query Only` flags, so a sqlalchemy input without flags always fails. Also flagged by
  pyrefly (`Type None is not iterable`). Found by reading the code; not reproduced
  (needs a Postgres server).
- **Reproduce:** with a reachable server and `adapter/Secret.py`, an `inputs_from_files`
  row `<host>.lbl.gov/<db>,,` (no table names or flags) → `ValueError`.
- **Expected:** `None` loads all tables, as documented (or a clear error asking for table names).
- **Status:** Resolved on branch `fix_pyrefly_errors` (decision: load all tables).
  `Db_sqlalchemy.load(None)` lists the database's tables with SQLAlchemy's `inspect` and
  loads them all. Tests: `TestDbSqlalchemy.test_load_without_table_names_loads_all_tables`
  and `test_load_named_tables`, which run `load()` against `test.db` through a sqlite
  engine (the loader is created without `__init__`, which needs Postgres credentials).
  Not yet verified against a real Postgres server.

## 28. Behavior changes from ruff lint fixes (group B)

Some ruff findings (outside `adapter/comm/excel.py`) can only be fixed by slightly
changing behavior. Each was fixed in its own commit; this entry records what changed
and the effect on the tests.

- **E721, `type(x) == T` → `isinstance(x, T)`** (`adapter/comm/sql.py`, `Sql.__init__`):
  subclasses are now accepted. A `str` subclass path, e.g. `numpy.str_`, used to raise
  `ValueError` and now opens the db; a `sqlite3.Connection` subclass (custom `factory=`)
  is now accepted as a connection. Tests: added
  `SqlTests.test_accepts_str_subclass_path` (fails on the old code); no existing test
  changed.
- **E712, comparisons to `True`/`False`** (`adapter/i_o.py`):
  - `IO.load()` flags `skip_writeout`, `save_input`, `create_db`, `clean_labels` and
    `set_first_col_as_index` now use truth tests (`if x:`) instead of `== True` /
    `!= False`. Same result for `True`/`False`, `0`/`1` and numpy booleans. Different
    only for unusual values: e.g. `create_db="yes"` or `2` used to mean "no db" and now
    create one; `set_first_col_as_index=None` used to raise `ValueError` and now means
    "don't index"; `set_first_col_as_index=[]` now skips indexing (same tables returned).
  - `IO.first_col_to_index()` keeps strict checks, now `table_names is True` /
    `is False` (a list or a string like `"t"` must not count as `True`). Different only
    for `1`, `0` and numpy booleans, which now raise `ValueError` (`1` used to index all
    tables; `0` hit #17).
  - Tests: no changes needed; existing tests cover `True`, `False` and list values.
- **E722, bare `except:`** (`comm/sql.py`, `i_o.py`, `to_python.py`):
  - Seven handlers are now `except Exception:`. The only difference: `KeyboardInterrupt`
    and `SystemExit` (Ctrl-C, interpreter exit) now propagate instead of being caught,
    retried or converted to `ValueError`. The handlers behind #6 (`Debugger` swallowing
    its own `ValueError`) and #11 (`IO.load` swallowing `create_db` failures) keep their
    current behavior; fixing those stays separate.
  - The `Secret.py` import in `Db_sqlalchemy.__init__` now catches `ImportError` only. A
    `Secret.py` that exists but fails to import (e.g. a `NameError` in it) now raises that
    error instead of the misleading "You must define your Secret.py" `ValueError`.
  - Tests: no changes needed. `TestDbSqlalchemy.test_raises_without_secret_file` still
    passes (a missing module raises `ModuleNotFoundError`, an `ImportError`).
- **B904, `raise` inside `except` without `from`** (`i_o.py` `create_db`; `to_python.py`
  `Excel.load` ×2, `Db_sqlalchemy.__init__`, `Db_sqlalchemy.load`): the same `ValueError`s
  are raised, now `from err`, so the original error is the exception's `__cause__` and the
  traceback says "The above exception was the direct cause of the following exception"
  instead of "During handling of the above exception, another exception occurred".
  Tests: `TestHelpers.test_create_db_raises_when_a_table_cannot_be_written` and
  `TestDbSqlalchemy.test_raises_without_secret_file` now also assert the cause (both fail
  on the previous code); their docstrings mention it.
  - Superseded for `IO.create_db` on branch `upgrade_pandas_3` (#33): a table that can't be
    written now raises the original error (e.g. `sqlite3.OperationalError`) instead of a
    `ValueError`; the test asserts that instead. `IO.load()` re-raises it with a note
    naming the input file (#11, #34).
- **B006, mutable default arguments** (`IO.__init__` `os_mapping`,
  `comm.tools.convert_network_drive_path` `mapping`): both now default to `None`, meaning
  the same mapping as before, now held once in `adapter.comm.tools.DEFAULT_OS_MAPPING`.
  `IO` copies it per instance, which fixes #29. Visible differences: the signatures show
  `None` as the default, and `IO(path, os_mapping=None)` now uses the default mapping
  (it used to raise `TypeError`). The `IO` docstring's `os_mapping` entry was corrected
  (it named the parameter `mapping` and gave a default that was never used).
  Tests: added `TestHelpers.test_default_os_mapping_is_not_shared_between_instances`
  (fails on the old code).

## 29. Default `os_mapping` dict shared by all `IO` instances

- **File:** `adapter/i_o.py:58-68` (`IO.__init__`)
- **Problem:** the default `os_mapping` was a dict literal in the signature, created once
  and stored as `self.os_mapping` by every `IO` created without `os_mapping`. Changing
  one instance's mapping changed the default for every later instance. Found while fixing
  ruff B006.
- **Reproduce (before the fix):** `a = IO(None); a.os_mapping["darwin"] = "/Volumes/Changed";
  IO(None).os_mapping["darwin"]` → `"/Volumes/Changed"`.
- **Expected:** each instance gets its own copy of the default.
- **Status:** Resolved with the B006 fix (see #28); covered by
  `TestHelpers.test_default_os_mapping_is_not_shared_between_instances`.

## 30. `Excel.load` error message could fail to build

- **File:** `adapter/to_python.py` (`Excel.load`, the named range and named table
  `try`/`except` blocks)
- **Problem:** the `ValueError` message uses the loop variable (`name` / `table_name`).
  If reading failed before the loop assigned it, building the message raised
  `UnboundLocalError`, hiding the real error. Unlikely in practice; found by pyrefly
  (`unbound-name`).
- **Status:** Resolved. Both variables are set to `None` before their `try`, so the
  message always builds (it says "None" in that rare case). No test changes needed.
  - Superseded on branch `upgrade_pandas_3` (#34): the handlers no longer build a message
    from the loop variable (they add a note naming the file), so those lines are removed.

## 31. Temporary pyrefly and ruff ignores

- **File:** `pyproject.toml`, `[tool.pyrefly]` and `[tool.ruff]` sections
- **What:** settings, added with explicit approval, that hide pyrefly and ruff errors:
  - ~~`project-excludes = ["adapter/comm/excel.py"]`~~: removed with `excel.py` (#16).
  - `ignore-missing-imports = ["adapter.Secret"]`: pyrefly doesn't report the import of the
    git-ignored credentials file in `Db_sqlalchemy.__init__`. Remove if credentials
    loading is restructured (e.g. with #27).
  - ~~`[tool.ruff]` `extend-exclude = ["adapter/comm/excel.py"]`~~: removed with
    `excel.py` (#16).
- **To remove:** delete the line and run `uv run pyrefly check` / `uv run ruff check .` to
  see the errors it was hiding.

## 32. Behavior changes from the pandas 3 upgrade

Branch `upgrade_pandas_3` requires `pandas>=3.0.0` (locked at 3.1.0). What changes for
code that uses `adapterio`:

- **Dependency:** packages that pin `pandas<3` can no longer install this version.
- **Text columns** in the loaded tables have pandas' `str` dtype instead of `object`, and
  their missing values are always `NaN`. Code that checks `dtype == object` must use
  `pd.api.types.is_string_dtype`. The golden fixtures were regenerated for this (39 dtype
  entries `object` -> `str`, no value changes).
- **Copy-on-Write** is always on: chained assignment such as `df["a"][0] = 1` on loaded
  tables no longer modifies them.
- **`IO.load(to_numeric=[...])`** converts column by column (#21), since pandas 3 removed
  `to_numeric(errors="ignore")` (#5).
- **SQL errors** from `pd.read_sql*`/`to_sql` are raised as `pandas.errors.DatabaseError`.
- Code changes needed in `adapter`: the numeric-column check in `Excel.load` no longer
  passes pandas extension dtypes (e.g. `str`) to `np.issubdtype`. No Copy-on-Write
  problems were found.
- Tests: all pass on pandas 3.1.0 with every warning treated as an error.
- **Pandas versions tested** (Python 3.12, with `uv run --with "pandas==X"`, not changing
  the lock file):
  - 3.0.0, 3.0.6, 3.1.0: all 105 tests pass. `pandas>=3.0.0` is the lowest bound that
    passes the full suite.
  - 2.1.4, 2.2.0 (both need `numpy<2`), 2.2.3, 2.3.0, 2.3.3: 99 pass; the 6 golden tests
    fail only because text columns load as `object` instead of `str` (on 2.3.3 with
    `future.infer_string` enabled, all 105 pass, so the data itself is identical).
  - 2.0.3, 2.1.0: can't be installed on Python 3.12 (no wheels; building from source fails).
  - Supporting pandas 2 would mean users get `object` or `str` text columns depending on
    their pandas version, and golden fixtures that depend on the pandas version.

## 33. sqlite database connections left open

- **File:** `adapter/to_python.py` (`Db.load`), `adapter/i_o.py` (`IO.create_db`)
- **Problem:** Python 3.13+ reports a `ResourceWarning: unclosed database` when a sqlite
  connection is garbage-collected without being closed; `uv run pytest -W error` failed
  (`1 failed, 104 passed`, 29 more reports). Tracking `sqlite3.connect` over the suite
  found 30 of 136 connections never closed:
  - 29 from `Db.load` (so every `IO.load()` of a `.db` file): its SQLAlchemy engine is
    never disposed, so its pooled connection stays open (also when it raises `OSError`
    for a db without tables). It also passes `pd.read_sql_table` a connection string,
    which makes pandas create another engine for every table.
  - 1 from `IO.create_db` when writing a table fails: it raised without closing the
    connection. (With `close=False`, the connection returned on success is meant to be
    open.)
  Open connections can exhaust file handles in long-running processes, and on Windows
  keep the db file locked.
- **Reproduce:** `uv run pytest -W error`; or run `Db("adapter/tests/inputs/test.db").load()`
  with `-W always::ResourceWarning` and `gc.collect()`.
- **Status:** Resolved on branch `upgrade_pandas_3`.
  - `IO.create_db` closes the connection whenever writing fails
    (`except BaseException: db_con.close(); raise`) and now lets the original error
    propagate instead of wrapping it in `ValueError` (see #28); test
    `TestHelpers.test_create_db_raises_when_a_table_cannot_be_written` updated.
  - `Db.load` creates one engine, passes it to `read_sql_table` (instead of a connection
    string, which made pandas create an engine per table), and disposes of it in a
    `finally` that covers everything after `create_engine`, including the `OSError` for a
    db without tables and the duplicate-table `ValueError`.
  - Result: 0 of 80 connections are left open over the suite (was 30 of 136), and
    `uv run pytest -W error` passes.

## 34. Behavior changes from simplifying `try`/`except` blocks

Several `try`/`except` blocks only replaced an error with a less informative one. On
branch `upgrade_pandas_3` they are removed or changed to add context to the original
error. Successful calls are unaffected; what changes is the error a caller sees when
something fails.

- **`Sql.__init__`** (`comm/sql.py`): removed the retry with `os.getcwd()` joined to the
  path. It always targeted the same file and failed with the same error. No behavior
  change. Test: `SqlTests.test_raises_for_path_that_cannot_be_opened`.
- **`Db_sqlalchemy.load`** (`to_python.py`): no longer catches every error, prints a
  traceback to stderr and raises an empty `ValueError`. The original error propagates
  (e.g. `pandas.errors.DatabaseError` for a table that can't be read; `ValueError` with
  its message for a table already loaded) and nothing is printed. Tests:
  `TestDbSqlalchemy.test_load_missing_table_raises_original_error`,
  `test_load_raises_for_tables_already_loaded` (both fail on the old code).
- **`Debugger.check_for_duplicates`** (`to_python.py`), string branch: removed the
  `try`/`except` that caught its own `ValueError` and only logged "Unexpected table_name
  format". A CSV input whose table name was already loaded now raises `ValueError`
  instead of silently overwriting that table (fixes #6). Tests: see #6.
- **`IO.load`** (`i_o.py`), creating the run database: no longer replaces the error with
  `ValueError("Not able to create a db of tables that were read in from <input>.")` (and
  no longer logs it). The original error propagates, with a note (`add_note`) naming the
  input file, e.g. `ValueError: Unsupported db flavor 'postgres' ...` followed by
  "Raised while creating the run database for input file <input>". Test:
  `TestLoadOutput.test_raises_when_db_cannot_be_created` updated to expect the original
  error and the note (fails on the old code).
- **`Excel.load`** (`to_python.py`), named ranges and named tables: no longer replace any
  reading error with `ValueError("Failed to read input named range/table <name> from
  input file <file>. If the data ... definition.")`. The original error propagates (e.g.
  `KeyError: 'Worksheet Missing does not exist.'` for a named range on a missing sheet),
  with a note naming the file: "Raised while reading named ranges/tables from <file>".
  The error no longer names the range or table. Tests:
  `ExcelTest.test_load_range_error_names_the_file`,
  `test_load_table_error_names_the_file` (both fail on the old code).
