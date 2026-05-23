# quotai Documentation

`quotai` is intentionally small: one Python CLI, no runtime dependencies, and output that makes Z.ai reset windows obvious.

Use these docs for the longer-form details that do not need to live in the main README.

## Guides

- [Usage Guide](usage.md) - installation, configuration, examples, output formats, and troubleshooting
- [Release Flow](release.md) - how the GitHub release automation is expected to work

## Design Goals

- Show the exact rolling five-hour reset time without needing to infer it from a chart.
- Keep normal terminal output readable for humans.
- Keep JSON output stable enough for scripts and monitoring.
- Avoid runtime dependencies so the tool can be dropped onto almost any machine with Python 3.10+.
- Make release validation repeatable through GitHub Actions.
