# Repository Guidelines

## Project Structure & Module Organization

`quotai` is a small Python CLI for displaying Z.ai quota usage and exact reset
windows.

- Keep the runtime CLI in `quotai.py`.
- Keep unit tests in `tests/` and prefer stdlib `unittest` unless the project
  deliberately adopts another test runner.
- Keep user-facing docs in `README.md` and `docs/`.
- Keep Debian packaging metadata in `debian/`.
- Keep Homebrew formula in `homebrew/`.
- Keep release helper scripts in `scripts/`.
- Keep GitHub Actions, labels, Dependabot, and release-drafter metadata under
  `.github/`.
- Keep the GitHub Pages landing site under `.github/assets/website/`.
- Keep root-level files for build, packaging, license, editor, and repository
  metadata only.
- Do not add GitLab-specific CI, release, or repository metadata to this GitHub
  repository.
- Retired files should be removed rather than kept as dead alternatives.

## Build, Test, and Development Commands

- Format Python code:
  ```bash
  make fmt
  ```
- Check formatting without rewriting files:
  ```bash
  make fmt-check
  ```
- Run static validation:
  ```bash
  make lint
  ```
- Run unit tests and bytecode compilation:
  ```bash
  make test
  ```
- Smoke test the CLI:
  ```bash
  make smoke
  ```
- Build package artifacts when the local environment has `build` installed:
  ```bash
  make build
  ```
- Check version metadata alignment:
  ```bash
  make version-check
  ```
- Build the GitHub Pages site when touching website assets:
  ```bash
  make website-build
  ```
- Build the Debian package when a Debian build environment is available:
  ```bash
  make package
  ```
- Syntax-check release helper scripts after editing them:
  ```bash
  bash -n scripts/*.sh
  ```

## Coding Style & Naming Conventions

- Python 3.12+ is the minimum supported runtime.
- Runtime code must remain stdlib-only. Development dependencies belong in the
  `dev` optional dependency group in `pyproject.toml`.
- Keep `quotai.py` readable as a single-file CLI: helpers, API parsing, output
  formatters, argument parsing, and entrypoint logic should stay clearly
  separated.
- Keep `main()` thin. Put validation, fetch, render, and loop behavior in
  focused helpers.
- Use type annotations on function signatures.
- Keep production functions documented with docstrings.
- Prefer structured JSON handling over ad hoc string parsing.
- Keep output fields stable unless the change is intentional and documented.
- Avoid broad refactors when a targeted fix is enough.
- Follow `.editorconfig`: Python uses 4 spaces, Markdown/YAML/JSON use 2
  spaces, and Makefiles use tabs.

## CLI Behavior Rules

- The default output is the human-readable quota view.
- Format flags are mutually exclusive: default, `--compact`, `--json`,
  `--jsonl`, and `--raw`.
- Keep exact reset visibility central to the tool. JSON-style outputs should
  preserve script-friendly reset fields such as `resets_at_utc` and
  `reset_epoch_ms`.
- Keep threshold behavior distinct: runtime errors exit `1`, and threshold
  breaches exit `2`.
- Do not make live API calls in tests. Mock `fetch_json()` or test parsing and
  formatting helpers directly.

## Versioning, Release, and Packaging Rules

- The default branch is `main`.
- Stable release tags use `v<major>.<minor>.<patch>`.
- Release candidate tags use `v<major>.<minor>.<patch>-rc.<n>`.
- Keep `VERSION` in `quotai.py` and `project.version` in `pyproject.toml`
  aligned with the stable target version in `debian/changelog`.
- Stable release tags must match the committed source version. RC tags are
  allowed to share the same committed source version as their stable target
  because promotion points the stable tag at the same commit.
- Release-note categories and version bump behavior are shared between
  `.github/release-drafter.yml` and `scripts/next-release.sh`; update them
  together.
- The release automation publishes a source archive, Debian package, Debian
  source package files, `sha256sums.txt`, a signed stable APT repository on
  GitHub Pages, and an updated Homebrew formula to the `homebrew-quotai` tap.
- Keep APT keyring filenames under the `quotai-archive-keyring.*` pattern.
- Keep `homebrew/quotai.rb` as the formula template. The publish workflow updates
  the URL and SHA256 and pushes to `soakes/homebrew-quotai`.
- Keep `Makefile` as the contributor-facing source of truth for common local
  validation commands.

## Documentation Sync

- Update `README.md` and `docs/usage.md` when CLI flags, output formats, exit
  codes, environment variables, or installation behavior change.
- Update `docs/release.md` when release workflows, tag rules, or published
  artifacts change.
- Update the GitHub Pages website when installation, artifact, or APT repository
  behavior changes.
- Update the project structure section in `README.md` when top-level files or
  directories change.
- Keep examples realistic, copyable, and free of real secrets.
- Public docs should not reference private machine paths or internal-only
  repository locations.

## GitHub Actions & Public Repo Security

- Treat this as a public repository. Workflow changes are security-sensitive.
- Keep workflow permissions least-privilege.
- Pull request workflows should validate code, not publish artifacts.
- Publishing should stay limited to trusted `v*` and `v*-rc.*` tags or explicit
  recovery dispatches.
- Automation auto-merge may approve and merge only trusted automation authors:
  Dependabot and GitHub automation bot accounts explicitly listed in
  `.github/workflows/automation-auto-merge.yml`.
- Never broaden auto-approval to general contributor pull requests.
- Release and publish tags must point to commits already contained in `main`;
  keep that verification in place.
- Stable APT publishing must remain limited to stable `v<major>.<minor>.<patch>`
  tags. Do not publish prerelease tags to the stable APT repository.
- Do not broaden token permissions, expose secrets to pull requests, or add
  publish jobs without documenting the operational need.

## Commit & Pull Request Guidelines

- Do not create commits unless the user explicitly asks for one.
- Keep changes focused by concern: runtime behavior, tests, docs, and release
  automation should be easy to review.
- Use conventional commit subjects for release-bearing work:
  `feat:`, `fix:`, `perf:`, `build:`, `deps:`, or `release:`.
- Documentation, CI, test, and maintenance-only changes should not cause a
  release bump unless paired with an intentional shipped behavior change.
- Do not mention prompts, AI assistance, or internal instruction sources in PR
  content.

## Agent Checklist

Before making non-trivial changes:

1. Read `AGENTS.md`, `README.md`, and the files directly related to the task.
2. Check the current worktree and do not overwrite unrelated user changes.
3. Prefer existing helpers, Make targets, and workflow patterns.
4. Update tests and docs alongside behavior changes.
5. Run the relevant validation commands before handing work back.

When the change touches normal runtime code, the expected minimum validation is:

```bash
make fmt-check
make lint
make test
make smoke
```

If packaging, release metadata, or website assets change, also run script syntax
checks, `make version-check`, and `make build` when the local Python environment
has the build tooling installed. Run `make package` and `make website-build`
when the required Debian and Node.js tooling is available.
