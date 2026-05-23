# quotai Documentation

`quotai` is intentionally small: one Python CLI, no runtime dependencies, and output that makes Z.ai reset windows obvious. Public releases include GitHub assets, a Debian package, and a signed APT repository.

Use these docs for the longer-form details that do not need to live in the main README.

## Guides

- [Usage Guide](usage.md) - APT installation, configuration, examples, output formats, and troubleshooting
- [Release Flow](release.md) - GitHub release, Debian package, APT repository, and Pages automation

## Design Goals

- Show the exact rolling five-hour reset time without needing to infer it from a chart.
- Keep normal terminal output readable for humans.
- Keep JSON output stable enough for scripts and monitoring.
- Avoid runtime dependencies so the tool can be dropped onto almost any machine with Python 3.12+.
- Make release validation repeatable through GitHub Actions.
- Keep committed source versions aligned with the stable release tags.
