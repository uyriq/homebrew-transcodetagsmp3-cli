# TranscodeTagsMP3 — Task Tracker

Agents and contributors should mark tasks `[x]` when completed and add new tasks as needed.

---

## Core functionality

- [x] Implement `fix_encoding()` — CP1251-as-Latin-1 → UTF-8 conversion with Cyrillic heuristic
- [x] Implement `fix_mp3_file()` — iterate ID3 frames, apply fix, re-save as ID3 v2.3 only when changed
- [x] Implement `main()` — CLI entry-point with per-file error handling and exit codes

## macOS integration

- [x] Create `TranscodeTagsMP3.workflow` — Automator Quick Action scoped to `public.mp3`
- [x] Create `install.sh` — one-shot installer (mutagen, script, workflow)
- [x] Fix install.sh mutagen installation — add `--break-system-packages` flag for PEP 668 (hack, to improve later)
- [x] Fix Automator workflow configuration — use inputMethod=1 (as arguments) and /usr/bin/python3 full path
- [x] Add comprehensive logging to workflow — captures stdout/stderr/args/env to ~/Library/Logs/TranscodeTagsMP3.log
- [x] Create separate wrapper script to avoid XML entity parsing issues in Automator workflow
- [x] Fix wrapper script Python discovery — augment PATH for Homebrew and search candidate python3 paths for mutagen
- [x] Fix install.sh — verify mutagen is importable from at least one candidate python3 after installation
- [x] Fix Automator COMMAND_STRING — replace `~/` tilde with `${HOME}` for reliable expansion in restricted environment
- [x] Update diagnose.sh — check all candidate python3 paths for mutagen to surface path-mismatch issues

## Testing

- [x] Unit tests for `fix_encoding` (Cyrillic round-trip, ASCII, empty, already-Unicode, Latin-1 unchanged)
- [x] Integration tests for `fix_mp3_file` (fixes tags, unchanged when correct, skips no-header files)
- [x] Integration tests for `main()` (non-MP3 skipped, missing file counted as error)
- [x] Create pytest fixture `broken_cp1251_mp3` for generating test MP3 files with broken tags
- [x] Add demonstration test using fixture to verify end-to-end tag fixing

## Code quality / review feedback

- [x] Fix `changed` flag bug — use per-frame `frame_changed` + overall `any_changed`
- [x] Add Cyrillic-majority heuristic to `fix_encoding` to protect Latin-1 text
- [x] Pin mutagen to vetted version in `install.sh`; use `python3 -m pip --user`
- [x] Remove unused test imports (`tempfile`, `ID3NoHeaderError`)
- [x] Strengthen `test_latin_text_unchanged` assertion (`result == text`)
- [x] Use file content hash (SHA-256) instead of mtime to detect unchanged files in tests

## Documentation

- [x] `README.md` — encoding problem explanation, installation, usage, file table
- [x] `tasks_todo.md` — this file

## macOS Homebrew integration

- [x] Add `_render_macos_runner_script(cli_path, log_path)` — bash runner using `osascript` for notifications
- [x] Add `_render_workflow_info_plist()` and `_render_workflow_document(runner_path)` — generate Automator `.workflow` XML dynamically from Python (no binary blob in tarball)
- [x] Add `install_macos_service_user(*, force, home, cli_path)` — writes `~/Library/Services/TranscodeTagsMP3.workflow/` and runner script; runs `pbs -flush` + restarts Finder; guards on `sys.platform == "darwin"`
- [x] Wire `install-macos-service --user [--force]` subcommand into `main()` and `_build_parser()`
- [x] Update `Formula/transcodetagsmp3.rb` — add `on_macos { depends_on :macos => :monterey }` and `def post_install` hook
- [x] Update `packaging/homebrew/transcodetagsmp3.rb` template with same changes
- [x] Add tests for `install_macos_service_user()` (plist content, runner script, overwrite guard, platform guard)
- [x] Update `README.md` with brew-based macOS install path
- [x] Bump version, publish new release tarball, update sha256 in both formula files
  - v0.2.0 released (macOS brew support); v0.2.1 released (--version / -V flag)
  - `--version` / `-V` shows `vX.Y.Z (tap@HASH)` when installed via Homebrew, or `vX.Y.Z-N-gHASH` from git

## Version info

- [x] Add `--version` / `-V` flag to CLI (`transcodetagsmp3 --version`)
  - Priority chain: Homebrew `INSTALL_RECEIPT.json` → `git describe` → fallback constant
  - Homebrew output: `transcodetagsmp3 v0.2.1 (tap@<tap_git_head[:8]>)`
  - Dev output: `transcodetagsmp3 v0.2.1-N-g<hash>`
  - Released as v0.2.1 in public tap

## Future / ideas

- [ ] Improve mutagen installation method — explore alternatives to `--break-system-packages` (venv, pipx, etc.)
- [ ] Add support for ID3v1 tags (currently only ID3v2 frames are processed)
- [ ] Add optional verbose/quiet flag to CLI
- [ ] Add `--dry-run` mode that prints what would change without saving
- [ ] Support additional Cyrillic encodings (KOI8-R, ISO 8859-5) via auto-detection
