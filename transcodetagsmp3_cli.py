#!/usr/bin/env python3
"""CLI entrypoint for Linux/Homebrew-friendly TranscodeTagsMP3 workflows."""

from __future__ import annotations

import argparse
import shlex
import shutil
import stat
import sys
from pathlib import Path
from typing import Dict, Iterable, Optional

from fix_mp3_tags import fix_mp3_file

APP_NAME = "transcodetagsmp3"
EXTENSION_FILENAME = "transcodetagsmp3_extension.py"
TEMPLATE_PATH = (
    Path(__file__).resolve().parent
    / "linux"
    / "nautilus"
    / "transcodetagsmp3_extension.py.tmpl"
)


def _resolve_cli_path(explicit: Optional[Path] = None) -> Path:
    if explicit:
        return explicit.expanduser().resolve()

    argv0 = Path(sys.argv[0]).resolve()
    if argv0.name == APP_NAME:
        return argv0

    found = shutil.which(APP_NAME)
    if found:
        return Path(found).resolve()

    return argv0


def _render_runner_script(cli_path: Path, log_path: Path) -> str:
    cli_quoted = shlex.quote(str(cli_path))
    log_quoted = shlex.quote(str(log_path))
    return f"""#!/usr/bin/env bash
set -euo pipefail

LOG_PATH={log_quoted}
mkdir -p "$(dirname "$LOG_PATH")"

set +e
OUTPUT=$({cli_quoted} "$@" 2>&1)
STATUS=$?
set -e
printf "%s\\n" "$OUTPUT" >>"$LOG_PATH"

SUMMARY=$(printf "%s\\n" "$OUTPUT" | awk '/^Done: /{{ line=$0 }} END {{ print line }}')
if [ -z "$SUMMARY" ]; then
  SUMMARY="See log: $LOG_PATH"
fi

if command -v notify-send >/dev/null 2>&1; then
  if [ "$STATUS" -eq 0 ]; then
    notify-send "Fix MP3 Tags Encoding" "$SUMMARY"
  else
    notify-send "Fix MP3 Tags Encoding (errors)" "$SUMMARY"
  fi
fi

exit "$STATUS"
"""


def _render_extension(runner_path: Path) -> str:
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Missing Nautilus template: {TEMPLATE_PATH}")

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    return template.replace("__RUNNER_PATH_REPR__", repr(str(runner_path)))


def install_nautilus_user(
    *,
    force: bool = False,
    home: Optional[Path] = None,
    cli_path: Optional[Path] = None,
) -> Dict[str, Path]:
    """Install Nautilus extension and runner in user-local directories."""
    home_dir = (home or Path.home()).expanduser().resolve()
    resolved_cli = _resolve_cli_path(cli_path)

    extension_dir = home_dir / ".local" / "share" / "nautilus-python" / "extensions"
    extension_path = extension_dir / EXTENSION_FILENAME

    app_dir = home_dir / ".local" / "share" / APP_NAME
    runner_path = app_dir / "run_fix_mp3_tags.sh"

    log_path = home_dir / ".local" / "state" / APP_NAME / "nautilus.log"

    if not force and (extension_path.exists() or runner_path.exists()):
        raise FileExistsError(
            "Nautilus integration already exists. Re-run with --force to overwrite."
        )

    extension_dir.mkdir(parents=True, exist_ok=True)
    app_dir.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    runner_path.write_text(_render_runner_script(resolved_cli, log_path), encoding="utf-8")
    runner_path.chmod(runner_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    extension_path.write_text(_render_extension(runner_path), encoding="utf-8")

    return {
        "extension_path": extension_path,
        "runner_path": runner_path,
        "log_path": log_path,
    }


def run_fix(paths: Iterable[str]) -> int:
    ok = 0
    failed = 0
    for raw in paths:
        path = Path(raw)
        if not path.is_file():
            print(f"Skipping (not a file): {raw}")
            failed += 1
            continue
        if path.suffix.lower() != ".mp3":
            print(f"Skipping (not an MP3): {raw}")
            continue

        if fix_mp3_file(str(path)):
            ok += 1
        else:
            failed += 1

    print(f"\nDone: {ok} processed, {failed} error(s).")
    return 1 if failed else 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=APP_NAME,
        usage=(
            f"{APP_NAME} [fix] <file1.mp3> [file2.mp3 ...]\n"
            f"       {APP_NAME} install-nautilus --user [--force]"
        ),
        description=(
            "Fix MP3 tags by default when file paths are passed. "
            "Use install-nautilus explicitly to install GNOME Files integration."
        ),
    )
    return parser


def _build_install_parser() -> argparse.ArgumentParser:
    install_parser = argparse.ArgumentParser(
        prog=f"{APP_NAME} install-nautilus",
        description="Install GNOME Files (Nautilus) user extension integration",
    )
    install_parser.add_argument(
        "--user",
        action="store_true",
        help="Install to user-local Nautilus extension path (~/.local/...)",
    )
    install_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing Nautilus integration files",
    )
    return install_parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    argv_list = list(argv) if argv is not None else sys.argv[1:]
    parser = _build_parser()

    if not argv_list:
        parser.print_help()
        return 1

    if argv_list[0] in ("-h", "--help"):
        parser.print_help()
        return 0

    if argv_list[0] == "install-nautilus":
        install_args = _build_install_parser().parse_args(argv_list[1:])
        if not install_args.user:
            parser.error("v1 supports only user-local install; pass --user")

        result = install_nautilus_user(force=install_args.force)
        print(f"Installed Nautilus extension: {result['extension_path']}")
        print(f"Installed runner script: {result['runner_path']}")
        print(f"Log file: {result['log_path']}")
        print("Restart GNOME Files: nautilus -q")
        return 0

    if argv_list[0] == "fix":
        if len(argv_list) == 1:
            parser.error("fix requires at least one file path")
        return run_fix(argv_list[1:])

    if argv_list[0].startswith("-"):
        parser.error(f"Unknown option: {argv_list[0]}")

    # Default mode: arguments are file paths for the fixer.
    return run_fix(argv_list)


if __name__ == "__main__":
    raise SystemExit(main())
