import os
import shutil

import pytest


@pytest.fixture
def clean_output():
    """Removes whatever a test adds under ``<cwd>/output``.

    For tests that must run from the repository root (their inputs
    use repo-relative paths) and therefore write their results to
    ``<repo>/output``. Entries that existed before the test are kept.
    """
    output_dir = os.path.join(os.getcwd(), "output")
    existed = os.path.isdir(output_dir)
    before = set(os.listdir(output_dir)) if existed else set()

    yield

    if os.path.isdir(output_dir):
        for entry in set(os.listdir(output_dir)) - before:
            entry_path = os.path.join(output_dir, entry)
            if os.path.isdir(entry_path):
                shutil.rmtree(entry_path)
            else:
                os.remove(entry_path)
        if not existed and not os.listdir(output_dir):
            os.rmdir(output_dir)


@pytest.fixture
def in_tmp_path(tmp_path, monkeypatch):
    """Runs the test with a fresh temporary folder as the working directory."""
    monkeypatch.chdir(tmp_path)
    return tmp_path
