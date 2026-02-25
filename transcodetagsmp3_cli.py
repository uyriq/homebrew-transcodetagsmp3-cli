#!/usr/bin/env python3
"""CLI entrypoint for Linux/Homebrew-friendly TranscodeTagsMP3 workflows."""

from __future__ import annotations

import argparse
import getpass
import html
import os
import shlex
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, Optional

from fix_mp3_tags import fix_mp3_file

APP_NAME = "transcodetagsmp3"
_FALLBACK_VERSION = "v0.2.0"


def _get_version() -> str:
    """Return version string.

    Priority:
    1. Homebrew INSTALL_RECEIPT.json  →  'vX.Y.Z (tap@abcd1234)'
    2. git describe                   →  'vX.Y.Z-N-gHASH'
    3. _FALLBACK_VERSION
    """
    import json

    # 1. Homebrew Cellar detection: .../Cellar/<name>/<version>/...
    script_path = Path(__file__).resolve()
    for parent in script_path.parents:
        if parent.parent.name == "Cellar" and parent.parent.parent.name in (
            "homebrew",
            "Cellar",
        ):
            break
        receipt = parent / "INSTALL_RECEIPT.json"
        if receipt.exists():
            try:
                data = json.loads(receipt.read_text())
                version = data.get("source", {}).get("versions", {}).get("stable") or parent.name
                tap_head = data.get("source", {}).get("tap_git_head") or ""
                hash_suffix = f" (tap@{tap_head[:8]})" if tap_head else ""
                return f"v{version}{hash_suffix}"
            except Exception:
                break

    # 2. git describe
    try:
        out = subprocess.check_output(
            ["git", "describe", "--tags", "--long", "--always"],
            stderr=subprocess.DEVNULL,
            cwd=script_path.parent,
        )
        return out.decode().strip()
    except Exception:
        pass

    return _FALLBACK_VERSION


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


def _render_macos_runner_script(cli_path: Path, log_path: Path) -> str:
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

if [ "$STATUS" -eq 0 ]; then
  osascript -e "display notification \\"$SUMMARY\\" with title \\"Fix MP3 Tags Encoding\\""
else
  osascript -e "display notification \\"$SUMMARY\\" with title \\"Fix MP3 Tags Encoding (errors)\\""
fi

exit "$STATUS"
"""


def _render_workflow_info_plist() -> str:
    return """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
\t<key>NSServices</key>
\t<array>
\t\t<dict>
\t\t\t<key>NSMenuItem</key>
\t\t\t<dict>
\t\t\t\t<key>default</key>
\t\t\t\t<string>Fix MP3 Tags Encoding</string>
\t\t\t</dict>
\t\t\t<key>NSMessage</key>
\t\t\t<string>runWorkflowAsService</string>
\t\t\t<key>NSSendFileTypes</key>
\t\t\t<array>
\t\t\t\t<string>public.mp3</string>
\t\t\t</array>
\t\t</dict>
\t</array>
</dict>
</plist>
"""


def _render_workflow_document(runner_path: Path) -> str:
    runner_sh_quoted = shlex.quote(str(runner_path))
    command_xml = html.escape(f'/bin/zsh {runner_sh_quoted} "$@"', quote=False)
    return f"""\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
\t<key>AMApplicationBuild</key>
\t<string>523.2</string>
\t<key>AMApplicationVersion</key>
\t<string>2.10</string>
\t<key>AMDocumentVersion</key>
\t<string>2</string>
\t<key>actions</key>
\t<array>
\t\t<dict>
\t\t\t<key>action</key>
\t\t\t<dict>
\t\t\t\t<key>AMAccepts</key>
\t\t\t\t<dict>
\t\t\t\t\t<key>Container</key>
\t\t\t\t\t<string>List</string>
\t\t\t\t\t<key>Optional</key>
\t\t\t\t\t<true/>
\t\t\t\t\t<key>Types</key>
\t\t\t\t\t<array>
\t\t\t\t\t\t<string>com.apple.cocoa.string</string>
\t\t\t\t\t</array>
\t\t\t\t</dict>
\t\t\t\t<key>AMActionVersion</key>
\t\t\t\t<string>2.0.3</string>
\t\t\t\t<key>AMApplication</key>
\t\t\t\t<array>
\t\t\t\t\t<string>Automator</string>
\t\t\t\t</array>
\t\t\t\t<key>AMParameterProperties</key>
\t\t\t\t<dict>
\t\t\t\t\t<key>COMMAND_STRING</key>
\t\t\t\t\t<dict/>
\t\t\t\t\t<key>CheckedForUserDefaultShell</key>
\t\t\t\t\t<dict/>
\t\t\t\t\t<key>inputMethod</key>
\t\t\t\t\t<dict/>
\t\t\t\t\t<key>shell</key>
\t\t\t\t\t<dict/>
\t\t\t\t\t<key>source</key>
\t\t\t\t\t<dict/>
\t\t\t\t</dict>
\t\t\t\t<key>AMProvides</key>
\t\t\t\t<dict>
\t\t\t\t\t<key>Container</key>
\t\t\t\t\t<string>List</string>
\t\t\t\t\t<key>Types</key>
\t\t\t\t\t<array>
\t\t\t\t\t\t<string>com.apple.cocoa.string</string>
\t\t\t\t\t</array>
\t\t\t\t</dict>
\t\t\t\t<key>ActionBundlePath</key>
\t\t\t\t<string>/System/Library/Automator/Run Shell Script.action</string>
\t\t\t\t<key>ActionName</key>
\t\t\t\t<string>Run Shell Script</string>
\t\t\t\t<key>ActionParameters</key>
\t\t\t\t<dict>
\t\t\t\t\t<key>COMMAND_STRING</key>
\t\t\t\t\t<string>{command_xml}</string>
\t\t\t\t\t<key>CheckedForUserDefaultShell</key>
\t\t\t\t\t<true/>
\t\t\t\t\t<key>inputMethod</key>
\t\t\t\t\t<integer>0</integer>
\t\t\t\t\t<key>shell</key>
\t\t\t\t\t<string>/bin/zsh</string>
\t\t\t\t\t<key>source</key>
\t\t\t\t\t<string></string>
\t\t\t\t</dict>
\t\t\t\t<key>BundleIdentifier</key>
\t\t\t\t<string>com.apple.RunShellScript</string>
\t\t\t\t<key>CFBundleVersion</key>
\t\t\t\t<string>2.0.3</string>
\t\t\t\t<key>CanShowSelectedItemsWhenRun</key>
\t\t\t\t<false/>
\t\t\t\t<key>CanShowWhenRun</key>
\t\t\t\t<true/>
\t\t\t\t<key>Category</key>
\t\t\t\t<array>
\t\t\t\t\t<string>AMCategoryUtilities</string>
\t\t\t\t</array>
\t\t\t\t<key>Class Name</key>
\t\t\t\t<string>RunShellScriptAction</string>
\t\t\t\t<key>InputUUID</key>
\t\t\t\t<string>A1B2C3D4-E5F6-7890-ABCD-EF1234567890</string>
\t\t\t\t<key>Keywords</key>
\t\t\t\t<array>
\t\t\t\t\t<string>Shell</string>
\t\t\t\t\t<string>Script</string>
\t\t\t\t\t<string>Command</string>
\t\t\t\t\t<string>Run</string>
\t\t\t\t\t<string>Unix</string>
\t\t\t\t</array>
\t\t\t\t<key>OutputUUID</key>
\t\t\t\t<string>B2C3D4E5-F6A7-8901-BCDE-F12345678901</string>
\t\t\t\t<key>UUID</key>
\t\t\t\t<string>C3D4E5F6-A7B8-9012-CDEF-123456789012</string>
\t\t\t\t<key>UnlocalizedApplications</key>
\t\t\t\t<array>
\t\t\t\t\t<string>Automator</string>
\t\t\t\t</array>
\t\t\t\t<key>arguments</key>
\t\t\t\t<dict>
\t\t\t\t\t<key>0</key>
\t\t\t\t\t<dict>
\t\t\t\t\t\t<key>default value</key>
\t\t\t\t\t\t<integer>0</integer>
\t\t\t\t\t\t<key>name</key>
\t\t\t\t\t\t<string>inputMethod</string>
\t\t\t\t\t\t<key>required</key>
\t\t\t\t\t\t<string>0</string>
\t\t\t\t\t\t<key>type</key>
\t\t\t\t\t\t<string>0</string>
\t\t\t\t\t\t<key>uuid</key>
\t\t\t\t\t\t<string>0</string>
\t\t\t\t\t</dict>
\t\t\t\t\t<key>1</key>
\t\t\t\t\t<dict>
\t\t\t\t\t\t<key>default value</key>
\t\t\t\t\t\t<false/>
\t\t\t\t\t\t<key>name</key>
\t\t\t\t\t\t<string>CheckedForUserDefaultShell</string>
\t\t\t\t\t\t<key>required</key>
\t\t\t\t\t\t<string>0</string>
\t\t\t\t\t\t<key>type</key>
\t\t\t\t\t\t<string>0</string>
\t\t\t\t\t\t<key>uuid</key>
\t\t\t\t\t\t<string>1</string>
\t\t\t\t\t</dict>
\t\t\t\t\t<key>2</key>
\t\t\t\t\t<dict>
\t\t\t\t\t\t<key>default value</key>
\t\t\t\t\t\t<string></string>
\t\t\t\t\t\t<key>name</key>
\t\t\t\t\t\t<string>source</string>
\t\t\t\t\t\t<key>required</key>
\t\t\t\t\t\t<string>0</string>
\t\t\t\t\t\t<key>type</key>
\t\t\t\t\t\t<string>0</string>
\t\t\t\t\t\t<key>uuid</key>
\t\t\t\t\t\t<string>2</string>
\t\t\t\t\t</dict>
\t\t\t\t\t<key>3</key>
\t\t\t\t\t<dict>
\t\t\t\t\t\t<key>default value</key>
\t\t\t\t\t\t<string></string>
\t\t\t\t\t\t<key>name</key>
\t\t\t\t\t\t<string>COMMAND_STRING</string>
\t\t\t\t\t\t<key>required</key>
\t\t\t\t\t\t<string>0</string>
\t\t\t\t\t\t<key>type</key>
\t\t\t\t\t\t<string>0</string>
\t\t\t\t\t\t<key>uuid</key>
\t\t\t\t\t\t<string>3</string>
\t\t\t\t\t</dict>
\t\t\t\t\t<key>4</key>
\t\t\t\t\t<dict>
\t\t\t\t\t\t<key>default value</key>
\t\t\t\t\t\t<string>/bin/sh</string>
\t\t\t\t\t\t<key>name</key>
\t\t\t\t\t\t<string>shell</string>
\t\t\t\t\t\t<key>required</key>
\t\t\t\t\t\t<string>0</string>
\t\t\t\t\t\t<key>type</key>
\t\t\t\t\t\t<string>0</string>
\t\t\t\t\t\t<key>uuid</key>
\t\t\t\t\t\t<string>4</string>
\t\t\t\t\t</dict>
\t\t\t\t</dict>
\t\t\t\t<key>isViewVisible</key>
\t\t\t\t<integer>1</integer>
\t\t\t\t<key>location</key>
\t\t\t\t<string>432.750000:305.000000</string>
\t\t\t\t<key>nibPath</key>
\t\t\t\t<string>/System/Library/Automator/Run Shell Script.action/Contents/Resources/Base.lproj/main.nib</string>
\t\t\t</dict>
\t\t\t<key>isViewVisible</key>
\t\t\t<integer>1</integer>
\t\t</dict>
\t</array>
\t<key>connectors</key>
\t<dict/>
\t<key>workflowMetaData</key>
\t<dict>
\t\t<key>applicationBundleID</key>
\t\t<string>com.apple.finder</string>
\t\t<key>applicationBundleIDsByPath</key>
\t\t<dict>
\t\t\t<key>/System/Library/CoreServices/Finder.app</key>
\t\t\t<string>com.apple.finder</string>
\t\t</dict>
\t\t<key>applicationPath</key>
\t\t<string>/System/Library/CoreServices/Finder.app</string>
\t\t<key>applicationPaths</key>
\t\t<array>
\t\t\t<string>/System/Library/CoreServices/Finder.app</string>
\t\t</array>
\t\t<key>inputTypeIdentifier</key>
\t\t<string>com.apple.Automator.fileSystemObject</string>
\t\t<key>outputTypeIdentifier</key>
\t\t<string>com.apple.Automator.nothing</string>
\t\t<key>presentationMode</key>
\t\t<integer>15</integer>
\t\t<key>processesInput</key>
\t\t<false/>
\t\t<key>serviceApplicationBundleID</key>
\t\t<string>com.apple.finder</string>
\t\t<key>serviceApplicationPath</key>
\t\t<string>/System/Library/CoreServices/Finder.app</string>
\t\t<key>serviceInputTypeIdentifier</key>
\t\t<string>com.apple.Automator.fileSystemObject</string>
\t\t<key>serviceOutputTypeIdentifier</key>
\t\t<string>com.apple.Automator.nothing</string>
\t\t<key>serviceProcessesInput</key>
\t\t<false/>
\t\t<key>systemImageName</key>
\t\t<string>NSTouchBarTagIcon</string>
\t\t<key>useAutomaticInputType</key>
\t\t<false/>
\t\t<key>workflowTypeIdentifier</key>
\t\t<string>com.apple.Automator.servicesMenu</string>
\t</dict>
</dict>
</plist>
"""


def install_macos_service_user(
    *,
    force: bool = False,
    home: Optional[Path] = None,
    cli_path: Optional[Path] = None,
) -> Dict[str, Path]:
    """Install Automator Quick Action and runner script in user-local directories (macOS only)."""
    if sys.platform != "darwin":
        raise RuntimeError("install-macos-service is only supported on macOS.")

    home_dir = (home or Path.home()).expanduser().resolve()
    resolved_cli = _resolve_cli_path(cli_path)

    workflow_dir = home_dir / "Library" / "Services" / "TranscodeTagsMP3.workflow" / "Contents"
    app_scripts_dir = home_dir / "Library" / "Application Scripts" / "TranscodeTagsMP3"
    runner_path = app_scripts_dir / "run_fix_mp3_tags.sh"
    log_path = home_dir / "Library" / "Logs" / "TranscodeTagsMP3.log"

    if not force and (workflow_dir.exists() or runner_path.exists()):
        raise FileExistsError(
            "macOS Quick Action already installed. Re-run with --force to overwrite."
        )

    workflow_dir.mkdir(parents=True, exist_ok=True)
    app_scripts_dir.mkdir(parents=True, exist_ok=True)

    (workflow_dir / "Info.plist").write_text(_render_workflow_info_plist(), encoding="utf-8")
    (workflow_dir / "document.wflow").write_text(
        _render_workflow_document(runner_path), encoding="utf-8"
    )

    runner_path.write_text(_render_macos_runner_script(resolved_cli, log_path), encoding="utf-8")
    runner_path.chmod(runner_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    subprocess.run(
        [
            "defaults", "write", "pbs", "NSServicesStatus",
            "-dict-add", "Fix MP3 Tags Encoding",
            "{enabled_context_menu = 1; enabled_services_menu = 1;}",
        ],
        check=False, capture_output=True,
    )
    subprocess.run(
        ["/System/Library/CoreServices/pbs", "-flush"], check=False, capture_output=True
    )
    subprocess.run(
        ["killall", "-u", os.environ.get("USER", getpass.getuser()), "cfprefsd"],
        check=False, capture_output=True,
    )
    subprocess.run(["killall", "automator.runner"], check=False, capture_output=True)
    subprocess.run(["killall", "Finder"], check=False, capture_output=True)

    return {
        "workflow_dir": workflow_dir.parent,
        "runner_path": runner_path,
        "log_path": log_path,
    }


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
            f"       {APP_NAME} install-nautilus --user [--force]\n"
            f"       {APP_NAME} install-macos-service --user [--force]\n"
            f"       {APP_NAME} --version"
        ),
        description=(
            "Fix MP3 tags by default when file paths are passed. "
            "Use install-nautilus explicitly to install GNOME Files integration. "
            "Use install-macos-service to install the Finder Quick Action (macOS only)."
        ),
    )
    return parser


def _build_install_macos_parser() -> argparse.ArgumentParser:
    install_parser = argparse.ArgumentParser(
        prog=f"{APP_NAME} install-macos-service",
        description="Install Finder Quick Action (Automator workflow) for macOS",
    )
    install_parser.add_argument(
        "--user",
        action="store_true",
        help="Install to user-local Services path (~/Library/Services/...)",
    )
    install_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing Quick Action files",
    )
    return install_parser


def _build_install_nautilus_parser() -> argparse.ArgumentParser:
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

    if argv_list[0] in ("-V", "--version"):
        print(f"{APP_NAME} {_get_version()}")
        return 0

    if argv_list[0] == "install-nautilus":
        install_args = _build_install_nautilus_parser().parse_args(argv_list[1:])
        if not install_args.user:
            parser.error("v1 supports only user-local install; pass --user")

        result = install_nautilus_user(force=install_args.force)
        print(f"Installed Nautilus extension: {result['extension_path']}")
        print(f"Installed runner script: {result['runner_path']}")
        print(f"Log file: {result['log_path']}")
        print("Restart GNOME Files: nautilus -q")
        return 0

    if argv_list[0] == "install-macos-service":
        install_args = _build_install_macos_parser().parse_args(argv_list[1:])
        if not install_args.user:
            parser.error("v1 supports only user-local install; pass --user")

        try:
            result = install_macos_service_user(force=install_args.force)
        except (RuntimeError, FileExistsError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

        print(f"Installed Quick Action: {result['workflow_dir']}")
        print(f"Installed runner script: {result['runner_path']}")
        print(f"Log file: {result['log_path']}")
        print("If Quick Action is not visible: System Settings → Privacy & Security → Extensions → Finder")
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
