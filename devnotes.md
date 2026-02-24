# Dev Notes

## Repository Setup

- Private development repo (`origin`): `git@github.com:uyriq/transcodetagsmp3.git`
- Public distribution repo (`public`): `git@github.com:uyriq/homebrew-transcodetagsmp3-cli.git`

Current local remotes:

```bash
git remote -v
```

Expected:

```text
origin  git@github.com:uyriq/transcodetagsmp3.git (fetch)
origin  git@github.com:uyriq/transcodetagsmp3.git (push)
public  git@github.com:uyriq/homebrew-transcodetagsmp3-cli.git (fetch)
public  git@github.com:uyriq/homebrew-transcodetagsmp3-cli.git (push)
```

## Sync Workflow

Use `origin` for normal dev collaboration and PRs. Push selected branches/tags to `public` for Homebrew users.

Push current feature branch to both repos:

```bash
git push origin feature/linux-files-ext
git push public feature/linux-files-ext
```

Publish a release tag to both repos:

```bash
git tag v0.1.0
git push origin v0.1.0
git push public v0.1.0
```

## Homebrew/Tap Relationship

- `public` repo provides release package assets (`https://github.com/uyriq/homebrew-transcodetagsmp3-cli/releases/download/<tag>/transcodetagsmp3-<tag>.tar.gz`).
- Homebrew tap uses the same public repo (`brew tap uyriq/transcodetagsmp3-cli`).
- Tap formula path: `Formula/transcodetagsmp3.rb`.
- Keep private-only files/secrets out of branches/tags pushed to `public`.
