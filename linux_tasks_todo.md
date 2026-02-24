# Linux Files Extension Tasks

Track progress for Ubuntu 22.04 / Nautilus 42.6 implementation.

## Session retrospective (completed)

- [x] Implemented Linux CLI (`transcodetagsmp3`) with default file-fix mode and explicit `install-nautilus --user`.
- [x] Implemented Nautilus extension integration (menu entry, async runner, notifications, mixed-selection handling).
- [x] Added Linux CLI and integration tests; full suite passing during implementation.
- [x] Verified end-to-end Nautilus GUI flow on sample garbled MP3 files (batch selection fix).
- [x] Published public packaging repo and aligned Homebrew tap flow to `brew tap uyriq/transcodetagsmp3-cli`.
- [x] Added release automation workflows (`release.yml`, `update-tap.yml`) and fixed workflow execution issues.
- [x] Published `v0.1.0` release and uploaded minimal runtime package asset.
- [x] Updated tap formula (`Formula/transcodetagsmp3.rb`) to release asset URL and concrete SHA256.
- [x] Validated real Homebrew tap/install/reinstall from GitHub-hosted formula.

## Step 1: Homebrew-friendly CLI foundation

- [x] Create `transcodetagsmp3` executable wrapper and CLI module.
- [x] Add `fix` subcommand to run existing MP3 tag fixer on selected files.
- [x] Make `fix` the default command when called with file path arguments.
- [x] Add `install-nautilus --user` subcommand for user-local installation.
- [x] Generate Nautilus extension file into `~/.local/share/nautilus-python/extensions`.
- [x] Generate helper runner script into `~/.local/share/transcodetagsmp3`.
- [x] Wire desktop notifications through `notify-send` in runner script.
- [x] Add overwrite guard and `--force` support.
- [x] Add tests for user install path rendering and overwrite behavior.

## Step 2: Nautilus UX and behavior parity

- [x] Show menu item only for local `.mp3` selections.
- [x] Ensure asynchronous background execution from Nautilus menu action.
- [x] Validate error handling/reporting for mixed selection sets.

## Step 3: Packaging and distribution

- [x] Add release-oriented install docs for Linux/Homebrew usage.
- [x] Add and maintain tap formula in `Formula/transcodetagsmp3.rb`.
- [x] Keep in-repo formula template (`packaging/homebrew/transcodetagsmp3.rb`) aligned with tap formula structure.
- [x] Publish formula to `uyriq/homebrew-transcodetagsmp3-cli` pointing to public release assets.
- [x] Validate fresh-install path on Ubuntu 22.04 + Nautilus 42.6.

## Step 4: Post-release hardening (next)

- [ ] Remove remaining manual step by chaining tap update automatically from successful release workflow.
- [ ] Add CI check that formula contains no placeholder hashes and uses release-asset URL pattern.
- [ ] Add explicit upgrade/uninstall/troubleshooting section for Linux users in README.
- [ ] Add a release checklist section for maintainers (tag, workflow run, verification commands).
