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

## Future / ideas

- [ ] Add support for ID3v1 tags (currently only ID3v2 frames are processed)
- [ ] Add optional verbose/quiet flag to CLI
- [ ] Add `--dry-run` mode that prints what would change without saving
- [ ] Add macOS Notification Center notification on completion
- [ ] Distribute as a standalone macOS `.pkg` installer
- [ ] Support additional Cyrillic encodings (KOI8-R, ISO 8859-5) via auto-detection
