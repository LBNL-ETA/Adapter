"""Rewrites the golden fixtures in fixtures/golden/ from the current
IO.load() output, for every input listed in GOLDEN_CASES in test_i_o.py.

Only run this when a change to the loaded data is intended and has been
reviewed (see "Golden fixtures" in the root README.md), then check
`git diff adapter/tests/fixtures/golden/` before committing. From the
repository root:

    uv run python -m adapter.tests.regenerate_golden_fixtures
"""

import json
import os

import pandas as pd

from adapter.i_o import IO
from adapter.tests.test_i_o import (
    GOLDEN_CASES,
    GOLDEN_RTOL,
    INPUTS_DIR,
    REPO_ROOT,
    frame_to_golden,
    golden_path,
)


def regenerate_golden_fixtures():
    cwd = os.getcwd()
    try:
        for input_file, needs_repo_root in GOLDEN_CASES.items():
            # nothing is written by load(skip_writeout=True), so the
            # working directory only matters for repo-relative inputs
            os.chdir(REPO_ROOT if needs_repo_root else cwd)
            tables = IO(os.path.join(INPUTS_DIR, input_file)).load(skip_writeout=True)[
                "tables_as_dict_of_dfs"
            ]
            golden = {
                "input_file": input_file,
                "pandas_version": pd.__version__,
                "rtol": GOLDEN_RTOL,
                "tables": {
                    name: frame_to_golden(df) for name, df in sorted(tables.items())
                },
            }
            with open(golden_path(input_file), "w") as f:
                json.dump(golden, f, indent=2)
                f.write("\n")
            print(f"wrote {golden_path(input_file)}")
    finally:
        os.chdir(cwd)


if __name__ == "__main__":
    regenerate_golden_fixtures()
