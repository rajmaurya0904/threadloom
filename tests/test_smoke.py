"""Smoke test: package imports cleanly. Replace/extend as modules land."""

import threadloom


def test_version_is_set() -> None:
    assert threadloom.__version__
