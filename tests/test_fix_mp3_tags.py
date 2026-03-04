#!/usr/bin/env python3
"""
Tests for fix_mp3_tags.py

Run with:
    pip3 install pytest mutagen
    pytest tests/
"""

import hashlib
import os
import platform
import plistlib
import sys

import pytest

# Allow importing from the repository root without installing the package.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fix_mp3_tags import fix_encoding, fix_mp3_file
from mutagen.id3 import ID3, TIT2, TPE1, TALB, Encoding
from transcodetagsmp3_cli import (
    install_macos_service_user,
    _render_macos_runner_script,
    _render_workflow_info_plist,
    _render_workflow_document,
)


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


# ── pytest fixtures ───────────────────────────────────────────────────────────


@pytest.fixture
def broken_cp1251_mp3(tmp_path):
    """
    Pytest fixture that generates a temporary MP3 file with intentionally
    broken CP1251 tags (Cyrillic text misinterpreted as Latin-1).

    The fixture creates:
    - A minimal valid MP3 file (silent, one frame)
    - ID3 tags with CP1251 Cyrillic text incorrectly stored as Latin-1:
      * TIT2 (title): "Группа крови"
      * TPE1 (artist): "Виктор Цой"
      * TALB (album): "Гений"

    Returns:
        pathlib.Path: Path to the generated MP3 file

    Cleanup:
        The file is automatically removed after the test completes (via tmp_path).

    Example:
        def test_my_fixer(broken_cp1251_mp3):
            # broken_cp1251_mp3 is a Path object with broken tags
            fix_mp3_file(str(broken_cp1251_mp3))
            tags = ID3(str(broken_cp1251_mp3))
            assert str(tags["TIT2"]) == "Группа крови"
    """
    mp3_path = tmp_path / "broken_tags.mp3"
    _make_mp3(str(mp3_path))

    # Write garbled tags (CP1251 bytes declared as Latin-1)
    tags = ID3()
    tags.add(TIT2(encoding=Encoding.LATIN1, text=[_garble("Группа крови")]))
    tags.add(TPE1(encoding=Encoding.LATIN1, text=[_garble("Виктор Цой")]))
    tags.add(TALB(encoding=Encoding.LATIN1, text=[_garble("Гений")]))
    tags.save(str(mp3_path))

    yield mp3_path
    # Cleanup is automatic via tmp_path


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
        text = "Привет"  # real Unicode - encode('latin-1') raises UnicodeEncodeError
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

    def test_fixture_broken_cp1251_mp3(self, broken_cp1251_mp3):
        """
        Demonstration test using the broken_cp1251_mp3 fixture.

        Verifies that:
        1. The fixture creates a valid MP3 file (one second of silence) with ID3 tags
        2. Tags are initially garbled (CP1251 stored as Latin-1)
        3. fix_mp3_file() correctly converts them to UTF-8
        4. All three tags (title, artist, album) are fixed
        """
        # Verify the fixture created a file
        assert broken_cp1251_mp3.exists()
        assert broken_cp1251_mp3.suffix == ".mp3"

        # Read tags before fix — they should be garbled
        tags_before = ID3(str(broken_cp1251_mp3))
        title_before = str(tags_before["TIT2"])
        artist_before = str(tags_before["TPE1"])
        album_before = str(tags_before["TALB"])

        # The garbled versions should NOT match the correct Cyrillic text
        assert title_before != "Группа крови"
        assert artist_before != "Виктор Цой"
        assert album_before != "Гений"

        # Apply the fix
        result = fix_mp3_file(str(broken_cp1251_mp3))
        assert result is True

        # Verify tags are now correct UTF-8 Cyrillic
        tags_after = ID3(str(broken_cp1251_mp3))
        assert str(tags_after["TIT2"]) == "Группа крови"
        assert str(tags_after["TPE1"]) == "Виктор Цой"
        assert str(tags_after["TALB"]) == "Гений"

        # Verify encoding is now proper Unicode (UTF-8 or UTF-16, not Latin-1)
        # mutagen may choose UTF-16 for non-ASCII text, which is also valid
        assert tags_after["TIT2"].encoding in (Encoding.UTF8, Encoding.UTF16)
        assert tags_after["TPE1"].encoding in (Encoding.UTF8, Encoding.UTF16)
        assert tags_after["TALB"].encoding in (Encoding.UTF8, Encoding.UTF16)


# ── macOS Quick Action install tests ─────────────────────────────────────────


class TestMacOSInstall:
    """Tests for install_macos_service_user() and its rendering helpers."""

    def test_render_macos_runner_contains_osascript(self, tmp_path):
        cli = tmp_path / "transcodetagsmp3"
        log = tmp_path / "TranscodeTagsMP3.log"
        script = _render_macos_runner_script(cli, log)
        assert "osascript" in script
        assert str(cli) in script
        assert str(log) in script
        assert 'ARGS=("$@")' in script
        assert 'read -r line' in script

    def test_render_macos_runner_no_notify_send(self, tmp_path):
        cli = tmp_path / "transcodetagsmp3"
        log = tmp_path / "t.log"
        script = _render_macos_runner_script(cli, log)
        assert "notify-send" not in script

    def test_render_workflow_info_plist_valid_xml(self):
        plist = _render_workflow_info_plist()
        # Must parse as a valid plist without error
        plistlib.loads(plist.encode("utf-8"))
        assert "public.mp3" in plist
        assert "Fix MP3 Tags Encoding" in plist

    def test_render_workflow_document_embeds_runner_path(self, tmp_path):
        runner = tmp_path / "run_fix_mp3_tags.sh"
        doc = _render_workflow_document(runner)
        assert str(runner) in doc
        assert "COMMAND_STRING" in doc
        assert "inputMethod" in doc
        assert "<integer>1</integer>" in doc
        assert "/bin/zsh" in doc

    def test_render_workflow_document_spaces_in_path(self, tmp_path):
        runner = tmp_path / "Application Scripts" / "run.sh"
        doc = _render_workflow_document(runner)
        # Path with spaces must be shell-quoted in the COMMAND_STRING
        assert "Application Scripts" in doc

    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS only")
    def test_install_macos_service_writes_files(self, tmp_path):
        fake_cli = tmp_path / "bin" / "transcodetagsmp3"
        fake_cli.parent.mkdir()
        fake_cli.touch()

        result = install_macos_service_user(home=tmp_path, cli_path=fake_cli)

        workflow_contents = result["workflow_dir"] / "Contents"
        assert (workflow_contents / "Info.plist").exists()
        assert (workflow_contents / "document.wflow").exists()
        assert result["runner_path"].exists()
        assert result["runner_path"].stat().st_mode & 0o111  # executable

    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS only")
    def test_install_macos_service_overwrite_guard(self, tmp_path):
        fake_cli = tmp_path / "bin" / "transcodetagsmp3"
        fake_cli.parent.mkdir()
        fake_cli.touch()

        install_macos_service_user(home=tmp_path, cli_path=fake_cli)
        with pytest.raises(FileExistsError):
            install_macos_service_user(home=tmp_path, cli_path=fake_cli)

    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS only")
    def test_install_macos_service_force_overwrites(self, tmp_path):
        fake_cli = tmp_path / "bin" / "transcodetagsmp3"
        fake_cli.parent.mkdir()
        fake_cli.touch()

        install_macos_service_user(home=tmp_path, cli_path=fake_cli)
        # Second call with force must not raise
        install_macos_service_user(home=tmp_path, cli_path=fake_cli, force=True)

    def test_install_macos_service_raises_on_non_macos(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sys.platform", "linux")
        with pytest.raises(RuntimeError, match="macOS"):
            install_macos_service_user(home=tmp_path)

    def test_install_macos_service_permission_error_is_clean(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sys.platform", "darwin")

        def _raise_permission(*args, **kwargs):
            raise PermissionError("denied")

        monkeypatch.setattr("pathlib.Path.write_text", _raise_permission)
        with pytest.raises(RuntimeError, match="Permission denied while installing Finder Quick Action"):
            install_macos_service_user(home=tmp_path, cli_path=tmp_path / "bin" / "transcodetagsmp3")
