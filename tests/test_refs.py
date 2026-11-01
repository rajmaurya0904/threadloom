"""Tests for threadloom.refs."""

import pytest

from threadloom.models import PRRef
from threadloom.refs import RefError, parse_ref, parse_refs


def test_parse_short_form() -> None:
    assert parse_ref("psf/requests#6000") == PRRef("psf", "requests", 6000)


def test_parse_url() -> None:
    assert parse_ref("https://github.com/psf/requests/pull/6000") == PRRef("psf", "requests", 6000)


def test_parse_url_with_suffix() -> None:
    ref = parse_ref("https://github.com/a/b/pull/12/files#diff")
    assert ref == PRRef("a", "b", 12)


def test_parse_bare_number_uses_default_repo() -> None:
    assert parse_ref("#7", "o/r") == PRRef("o", "r", 7)
    assert parse_ref("7", "o/r") == PRRef("o", "r", 7)


def test_bare_number_without_repo_fails() -> None:
    with pytest.raises(RefError):
        parse_ref("7")


def test_garbage_fails() -> None:
    with pytest.raises(RefError):
        parse_ref("hello world")


def test_parse_refs_dedupes_in_order() -> None:
    refs = parse_refs(["a/b#1", "https://github.com/a/b/pull/1", "a/b#2"])
    assert [r.number for r in refs] == [1, 2]


def test_ref_slug_and_url() -> None:
    ref = PRRef("a", "b", 3)
    assert ref.slug == "a/b#3"
    assert ref.url == "https://github.com/a/b/pull/3"
