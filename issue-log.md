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

## 2. `SqlTests` modifies a tracked file on every run

- **File:** `adapter/comm/tests/test_sql.py:61-71`
- **Problem:** `teardown_class` (previously `tearDownClass`) renames the working
  `test.db` to `adapter/comm/tests/test_done.db`, overwriting it. That file is
  committed, so every test run leaves it modified in `git status`.
- **Reproduce:** start from a clean checkout, run `uv run pytest adapter/comm/tests/test_sql.py`,
  then `git status` → `modified: adapter/comm/tests/test_done.db`.

## 3. Test order dependency in `SqlTests`

- **File:** `adapter/comm/tests/test_sql.py`
- **Problem:** `test_c_table2pd` and `test_e_tables2dict` read the `pd2table`
  table that `test_a_pd2table` writes. They pass only because the tests run in
  alphabetical/definition order against a shared class-level database.
- **Reproduce:** `uv run pytest adapter/comm/tests/test_sql.py -k table2pd`
  (runs `test_c` without `test_a`) → fails because `pd2table` doesn't exist.

## 4. Tests write scratch files to the current working directory

- **File:** `adapter/tests/test_i_o.py` (`TestPickle`), `adapter/tests/test_i_o.py`
  (`IOTests` writes to `./output/`)
- **Problem:** pickle tests create `data.pickle.gz`, `test.pkl.gz`, and `empty.pkl.gz`
  in the CWD. Some `IOTests` load calls (e.g. `test_load_from_csv_inputs_from_files`,
  `test_load_from_db`) create `output/<version>_<timestamp>/` without removing it.
  If an assertion fails before the manual `os.remove`/`shutil.rmtree`, files are left behind.
- **Reproduce:** run `uv run pytest` from the repo root, then `ls output/`.

## 5. Deprecated `pd.to_numeric(errors="ignore")`

- **File:** `adapter/i_o.py:387-389`
- **Problem:** `errors="ignore"` emits a pandas `FutureWarning` and will raise in
  pandas 3.x. This blocks the planned pandas upgrade.
- **Reproduce:** `uv run pytest adapter/tests/test_i_o.py -k csv_inputs_from_files`
  → `FutureWarning: errors='ignore' is deprecated ...`.
