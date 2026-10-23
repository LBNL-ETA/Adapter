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

## 9. Blank "Table Name" for a `.db` row in `inputs_from_files` crashes

- **File:** `adapter/i_o.py:235-252`, `adapter/to_python.py:290-292` (`Db.load`)
- **Problem:** a blank cell is read as `NaN` (a float) and passed as `table_names`.
  `Excel.load` treats `NaN` as "load all", but `Db.load` does `set(table_names)`.
- **Reproduce:** `inputs_from_files.csv` with one row `adapter/tests/inputs/test.db,,` →
  `IO(<that csv>).load(skip_writeout=True)` → `TypeError: 'numpy.float64' object is not iterable`.
- **Expected:** blank means "load all tables", as for Excel and CSV rows.

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

## 17. `IO.first_col_to_index(..., table_names=False)` raises `TypeError`

- **File:** `adapter/i_o.py:837-847`
- **Problem:** the `False` branch is accepted (`pass`), but the loop then runs
  `x in table_names` with `table_names=False`.
- **Reproduce:** `IO(None).first_col_to_index({"a": pd.DataFrame({"x": [1]})}, table_names=False)`
  → `TypeError: argument of type 'bool' is not iterable`.
  (`IO.load` never calls it with `False`, so `load()` is unaffected.)
- **Expected:** returns copies of all tables unchanged.

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

## 24. Leftover debugger import in `comm/sql.py`

- **File:** `adapter/comm/sql.py:10`
- **Problem:** `from pdb import set_trace as bp` is imported but never used. It is dead
  code, and the `debug-statements` pre-commit hook rejects any commit that includes
  this file until it is removed.
- **Reproduce:** `uv run ruff check adapter/comm/sql.py --select F401` → `F401 'pdb.set_trace' imported but unused`;
  `uv run pre-commit run debug-statements --files adapter/comm/sql.py` (after hooks are set up) fails.
- **Expected:** the import is removed.

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
