"""Catalog hygiene: every .po file must be complete, consistent and compiled."""

import re
from pathlib import Path

import polib
import pytest

ROOT = Path(__file__).resolve().parent.parent
PO_FILES = sorted(p for p in ROOT.glob("**/locale/*/LC_MESSAGES/django.po") if ".git" not in p.parts)
PLACEHOLDER = re.compile(r"%\([^)]+\)[sd]|%[sd]|\{[^}]*\}")


def test_catalogs_are_found():
    assert len(PO_FILES) >= 15


@pytest.mark.parametrize("path", PO_FILES, ids=lambda p: str(p.relative_to(ROOT)))
def test_catalog_is_complete_and_consistent(path):
    catalog = polib.pofile(str(path))
    assert not catalog.obsolete_entries(), "remove obsolete (#~) entries"
    for entry in catalog:
        assert "fuzzy" not in entry.flags, f"fuzzy entry: {entry.msgid[:60]!r}"
        translations = entry.msgstr_plural.values() if entry.msgid_plural else [entry.msgstr]
        assert all(t.strip() for t in translations), f"empty translation: {entry.msgid[:60]!r}"
        assert sorted(PLACEHOLDER.findall(entry.msgid)) == sorted(PLACEHOLDER.findall(entry.msgstr)), (
            f"placeholders differ: {entry.msgid[:60]!r}"
        )
        assert not re.search("[´`]", entry.msgstr), f"use a plain apostrophe: {entry.msgid[:60]!r}"


@pytest.mark.parametrize("path", PO_FILES, ids=lambda p: str(p.relative_to(ROOT)))
def test_compiled_catalog_matches_source(path):
    compiled = polib.mofile(str(path.with_suffix(".mo")))
    source = {e.msgid: e.msgstr for e in polib.pofile(str(path))}
    assert {e.msgid: e.msgstr for e in compiled} == source, "run `python manage.py compilemessages`"
