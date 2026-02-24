#!/usr/bin/env python3
"""Tests for Linux CLI integration helpers."""

import os
import stat
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from transcodetagsmp3_cli import (
    EXTENSION_FILENAME,
    install_nautilus_user,
    main,
    run_fix,
)


_MINIMAL_MP3_FRAME = b"\xff\xfb\x90\x00" + b"\x00" * 413


def _make_mp3(path: Path) -> None:
    with open(path, "wb") as fh:
        fh.write(_MINIMAL_MP3_FRAME)


def test_install_nautilus_user_writes_extension_and_runner(tmp_path):
    cli_path = tmp_path / "bin" / "transcodetagsmp3"
    cli_path.parent.mkdir(parents=True)
    cli_path.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    cli_path.chmod(0o755)

    result = install_nautilus_user(home=tmp_path, cli_path=cli_path)

    extension_path = result["extension_path"]
    runner_path = result["runner_path"]

    assert extension_path.name == EXTENSION_FILENAME
    assert extension_path.exists()
    assert runner_path.exists()

    extension_content = extension_path.read_text(encoding="utf-8")
    runner_content = runner_path.read_text(encoding="utf-8")
    assert str(runner_path) in extension_content
    assert str(cli_path.resolve()) in runner_content
    assert 'parsed.scheme != "file"' in extension_content
    assert 'path.lower().endswith(".mp3")' in extension_content
    assert "start_new_session=True" in extension_content
    assert f'{str(cli_path.resolve())} "$@"' in runner_content
    assert 'notify-send "Fix MP3 Tags Encoding"' in runner_content
    assert "Done: " in runner_content

    mode = runner_path.stat().st_mode
    assert mode & stat.S_IXUSR


def test_install_nautilus_user_requires_force_when_files_exist(tmp_path):
    cli_path = tmp_path / "bin" / "transcodetagsmp3"
    cli_path.parent.mkdir(parents=True)
    cli_path.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    cli_path.chmod(0o755)

    install_nautilus_user(home=tmp_path, cli_path=cli_path)

    with pytest.raises(FileExistsError):
        install_nautilus_user(home=tmp_path, cli_path=cli_path, force=False)

    install_nautilus_user(home=tmp_path, cli_path=cli_path, force=True)


def test_main_defaults_to_fix_when_paths_are_passed(capsys, tmp_path):
    txt = tmp_path / "note.txt"
    txt.write_text("not an mp3", encoding="utf-8")

    rc = main([str(txt)])

    out = capsys.readouterr().out
    assert rc == 0
    assert "Skipping (not an MP3)" in out


def test_main_explicit_fix_still_supported(capsys, tmp_path):
    txt = tmp_path / "note2.txt"
    txt.write_text("not an mp3", encoding="utf-8")

    rc = main(["fix", str(txt)])

    out = capsys.readouterr().out
    assert rc == 0
    assert "Skipping (not an MP3)" in out


def test_run_fix_mixed_selection_reports_counts(capsys, tmp_path):
    mp3 = tmp_path / "ok.mp3"
    txt = tmp_path / "note.txt"
    missing = tmp_path / "missing.mp3"

    _make_mp3(mp3)
    txt.write_text("not an mp3", encoding="utf-8")

    rc = run_fix([str(mp3), str(txt), str(missing)])

    out = capsys.readouterr().out
    assert rc == 1
    assert "Skipping (not an MP3)" in out
    assert "Skipping (not a file)" in out
    assert "Done: 1 processed, 1 error(s)." in out
