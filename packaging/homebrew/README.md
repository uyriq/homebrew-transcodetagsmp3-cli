# Homebrew Packaging Notes

This folder contains a starter formula for the public source repo:

- Public source repo: `git@github.com:uyriq/homebrew-transcodetagsmp3-cli.git`
- Homebrew tap source: same repo (`uyriq/homebrew-transcodetagsmp3-cli`)

## Release Flow

1. Push a release tag to the public source repo.
2. Download release tarball URL:
   `https://github.com/uyriq/homebrew-transcodetagsmp3-cli/archive/refs/tags/<tag>.tar.gz`
3. Compute SHA-256:
   `sha256sum transcodetagsmp3-cli-<tag>.tar.gz`
4. Update formula fields:
   - `url`
   - `sha256`
   - `resource "mutagen"` sha256
5. Commit formula to `Formula/transcodetagsmp3.rb` in this repo.

## Install (user side)

```bash
brew tap uyriq/transcodetagsmp3-cli
brew install transcodetagsmp3
transcodetagsmp3 install-nautilus --user
nautilus -q
```

## Notes

- `install-nautilus --user` is intentionally explicit.
- Running `transcodetagsmp3 <file1.mp3> ...` defaults to fix mode.
