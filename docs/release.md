# Release Flow

`quotai` uses the same public-release shape as the other maintained repos: validation first, an automated release candidate, manual promotion to stable, GitHub release assets, and a signed APT repository on GitHub Pages.

## Validation

The `Build and Validate` workflow runs on pull requests, pushes to `main`, and manual dispatches. It checks:

- Python formatting with Black
- Ruff linting
- Pylint
- Unit tests
- CLI smoke tests
- Version consistency between `quotai.py`, `pyproject.toml`, and `debian/changelog`
- Python package build
- GitHub Pages website validation and build
- Debian package and signed APT repository layout smoke tests

## Automation Pull Requests

The `Automation Auto Merge` workflow can approve and merge trusted automation
pull requests after `Build and Validate` has passed for the exact current head
commit.

The trusted author list is intentionally narrow: Dependabot and GitHub
automation bot accounts only. Human contributor pull requests are never
auto-approved by this workflow.

## Draft Releases

The `Release Drafter` workflow updates labels, labels pull requests, and maintains a draft release when releasable commits are present.

The release version is based on conventional commit subjects:

| Commit subject | Version bump |
|---|---|
| `feat: ...` | minor |
| `fix: ...`, `perf: ...`, `build: ...`, `deps: ...`, `packaging: ...`, `release: ...` | patch |
| `type!: ...` or `BREAKING CHANGE:` | major |
| docs, CI, tests, and refactors only | no release by default |

## Release Candidates

The `Automated Release Candidate` workflow can create `vX.Y.Z-rc.N` tags after validation succeeds on `main`.

Before tagging, it ensures the committed source versions match the stable target, for example `v1.0.0`. If a future release needs a version metadata update, the workflow commits that update first and waits for the next validation pass before tagging.

Release candidate tags publish prerelease assets through the `Release Assets` workflow. RC tags share the same source version as their stable target because the promotion workflow points the stable tag at the same commit.

## Stable Releases

Use the `Promote Release Candidate` workflow to promote a release candidate tag such as `v1.0.0-rc.1` to a stable tag such as `v1.0.0`.

Stable tags publish a GitHub release marked as latest and publish the signed APT repository and landing site to GitHub Pages.

## Assets

The `Release Assets` workflow attaches:

- `quotai-VERSION.tar.gz`, a source archive for the tagged commit
- `quotai_VERSION-1_all.deb`, the Debian package
- Debian source package files
- `sha256sums.txt`

The stable-only `Publish Signed Debian Repository` workflow publishes:

- a `stable main` APT repository
- `quotai-archive-keyring.asc`
- `quotai-archive-keyring.gpg`
- `quotai-archive-keyring.fingerprint.txt`
- the GitHub Pages landing site

The Python package build is validated in CI, but the runtime remains a simple stdlib-only script.
