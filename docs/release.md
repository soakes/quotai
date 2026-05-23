# Release Flow

The GitHub release setup is intentionally lighter than larger service repositories. `quotai` ships as a Python source package and a single script archive.

## Validation

The `Build and Validate` workflow runs on pull requests, pushes to `main`, and manual dispatches. It checks:

- Python formatting with Black
- Ruff linting
- Pylint
- Unit tests
- CLI smoke tests
- Python package build

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
| `fix: ...`, `perf: ...`, `build: ...`, `deps: ...` | patch |
| `type!: ...` or `BREAKING CHANGE:` | major |
| docs, CI, tests, and refactors only | no release by default |

## Release Candidates

The `Automated Release Candidate` workflow can create `vX.Y.Z-rc.N` tags after validation succeeds on `main`.

Release candidate tags publish prerelease assets through the `Release Assets` workflow.

## Stable Releases

Use the `Promote Release Candidate` workflow to promote a release candidate tag such as `v2.1.0-rc.1` to a stable tag such as `v2.1.0`.

Stable tags publish a GitHub release marked as latest.

## Assets

The `Release Assets` workflow attaches:

- `quotai-VERSION.tar.gz`, a curated archive containing the script, docs, license, and packaging metadata
- `sha256sums.txt`

The Python package build is validated in CI, but the runtime remains a simple stdlib-only script.
