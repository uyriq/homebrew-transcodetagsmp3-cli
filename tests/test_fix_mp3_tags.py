#!/usr/bin/env python3
"""
Tests for fix_mp3_tags.py

Run with:
    pip3 install pytest mutagen
    pytest tests/
"""

import hashlib
import os
import sys

import pytest

# Allow importing from the repository root without installing the package.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fix_mp3_tags import fix_encoding, fix_mp3_file  # noqa: E402
from mutagen.id3 import ID3, TIT2, TPE1, TALB, Encoding  # noqa: E402


# ── Minimal valid MPEG1/Layer3 frame (for creating test MP3 files) ────────────
# Sync word 0xFFFA = MPEG1 Layer3 CBR; pad to 417 bytes (one full 128 kbps frame)
_MINIMAL_MP3_FRAME = b"\xff\xfb\x90\x00" + b"\x00" * 413


def _make_mp3(path: str) -> None:
    """Write a bare-bones MP3 file (one silent frame, no ID3 tags)."""
    with open(path, "wb") as fh:
        fh.write(_MINIMAL_MP3_FRAME)


def _file_sha256(path: str) -> str:
    """Return hex SHA-256 digest of a file's contents."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def _garble(text: str) -> str:
    """
    Simulate the CP1251 → Latin-1 misread: encode to CP1251 bytes, then
    incorrectly decode those bytes as Latin-1.  This is what software
    produces when it reads a Windows-1251-tagged file as ISO-8859-1.
    """
    return text.encode("cp1251").decode("latin-1")


# ── fix_encoding unit tests ───────────────────────────────────────────────────


class TestFixEncoding:
    def test_cyrillic_hello(self):
        """CP1251 bytes read as Latin-1 should round-trip back to Cyrillic."""
        garbled = _garble("Привет")
        assert fix_encoding(garbled) == "Привет"

    def test_cyrillic_long_phrase(self):
        phrase = "Группа крови на рукаве"
        assert fix_encoding(_garble(phrase)) == phrase

    def test_ascii_unchanged(self):
        text = "Hello World 123"
        assert fix_encoding(text) == text

    def test_empty_string(self):
        assert fix_encoding("") == ""

    def test_already_unicode_cyrillic_unchanged(self):
        """Text that is already proper Unicode Cyrillic cannot encode to Latin-1,
        so fix_encoding must return it unchanged."""
        text = "Привет"  # real Unicode – encode('latin-1') raises UnicodeEncodeError
        assert fix_encoding(text) == text

    def test_latin_text_unchanged(self):
        """Pure Latin-1 text must not be corrupted into Cyrillic."""
        text = "café"
        result = fix_encoding(text)
        assert result == text


# ── fix_mp3_file integration tests ───────────────────────────────────────────


class TestFixMp3File:
    def test_fixes_cp1251_tags(self, tmp_path):
        """Tags stored as CP1251-in-Latin-1 must be corrected and saved."""
        mp3 = str(tmp_path / "test.mp3")
        _make_mp3(mp3)

        # Write garbled tags (CP1251 bytes declared as Latin-1)
        tags = ID3()
        tags.add(TIT2(encoding=Encoding.LATIN1, text=[_garble("Привет")]))
        tags.add(TPE1(encoding=Encoding.LATIN1, text=[_garble("Тест")]))
        tags.add(TALB(encoding=Encoding.LATIN1, text=[_garble("Альбом")]))
        tags.save(mp3)

        result = fix_mp3_file(mp3)

        assert result is True
        fixed_tags = ID3(mp3)
        assert str(fixed_tags["TIT2"]) == "Привет"
        assert str(fixed_tags["TPE1"]) == "Тест"
        assert str(fixed_tags["TALB"]) == "Альбом"

    def test_already_correct_tags_unchanged(self, tmp_path):
        """An MP3 whose tags are already correct UTF-8 should not be modified."""
        mp3 = str(tmp_path / "correct.mp3")
        _make_mp3(mp3)

        tags = ID3()
        tags.add(TIT2(encoding=Encoding.UTF8, text=["Hello World"]))
        tags.save(mp3)

        sha_before = _file_sha256(mp3)
        result = fix_mp3_file(mp3)
        sha_after = _file_sha256(mp3)

        assert result is True
        assert sha_before == sha_after  # file must NOT have been rewritten
        assert str(ID3(mp3)["TIT2"]) == "Hello World"

    def test_no_id3_header_skipped(self, tmp_path):
        """A file with no ID3 tags should be skipped without error."""
        mp3 = str(tmp_path / "notags.mp3")
        _make_mp3(mp3)
        # Do NOT add any ID3 tags.
        result = fix_mp3_file(mp3)
        assert result is True

    def test_non_mp3_skipped_by_main(self, capsys, tmp_path):
        """main() must skip files whose names do not end in .mp3."""
        txt = str(tmp_path / "note.txt")
        with open(txt, "w") as fh:
            fh.write("not an mp3")

        from fix_mp3_tags import main

        sys.argv = ["fix_mp3_tags.py", txt]
        # main() exits with code 0 when there are no failures; .txt files are
        # simply skipped, not counted as errors.
        main()
        captured = capsys.readouterr()
        assert "Skipping" in captured.out

    def test_missing_file_counted_as_error(self, tmp_path):
        """A path that does not exist must be counted as an error."""
        from fix_mp3_tags import main

        missing = str(tmp_path / "ghost.mp3")
        sys.argv = ["fix_mp3_tags.py", missing]
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
