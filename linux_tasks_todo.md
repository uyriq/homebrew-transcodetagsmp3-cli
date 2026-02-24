# Linux Files Extension Tasks

Track progress for Ubuntu 22.04 / Nautilus 42.6 implementation.

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
- [x] Add starter Homebrew formula template in-repo (`packaging/homebrew/transcodetagsmp3.rb`).
- [ ] Publish final formula to `uyriq/homebrew-transcodetagsmp3-cli` pointing to public tag tarballs.
- [ ] Validate fresh-install path on Ubuntu 22.04 + Nautilus 42.6.
