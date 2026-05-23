# 📊 Quotai

> A small terminal CLI for showing Z.ai quota usage, remaining capacity, and exact reset times.

[![Validate](https://img.shields.io/github/actions/workflow/status/soakes/quotai/build-and-validate.yml?branch=main&style=flat-square&label=validate)](https://github.com/soakes/quotai/actions/workflows/build-and-validate.yml)
[![Release](https://img.shields.io/github/v/release/soakes/quotai?sort=semver&style=flat-square)](https://github.com/soakes/quotai/releases)
[![APT Repository](https://img.shields.io/badge/APT-signed%20repository-00897B?style=flat-square)](https://soakes.github.io/quotai/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-2EA043.svg?style=flat-square)](LICENSE)
[![Stdlib Only](https://img.shields.io/badge/runtime%20deps-zero-10B981.svg?style=flat-square)](quotai.py)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-support-FFDD00?style=flat-square&logo=buymeacoffee&logoColor=000000)](https://buymeacoffee.com/soakes)

`quotai` queries the Z.ai quota endpoint and renders the result in a terminal view that is easy to read at a glance. It was built because the Z.ai usage charts are useful, but they do not make the rolling five-hour reset window and exact reset time clear enough when you are trying to plan work.

The default output is for humans. JSON, JSON Lines, compact, and raw modes are available for scripts, dashboards, cron jobs, and debugging.

This is an unofficial tool and is not affiliated with Z.ai.

**Quick links:** [Website and APT repo](https://soakes.github.io/quotai/) | [Releases](https://github.com/soakes/quotai/releases) | [Usage guide](docs/usage.md) | [Release flow](docs/release.md) | [License](LICENSE)

## 🧭 Contents

- [Overview](#overview)
- [Capabilities](#capabilities)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Output Formats](#output-formats)
- [Exit Codes](#exit-codes)
- [Development](#development)
- [Project Structure](#project-structure)
- [License](#license)

## 📖 Overview

Z.ai exposes quota information through an authenticated API endpoint. `quotai` turns that response into:

- the current Z.ai plan level
- the known quota windows, including the five-hour rolling token quota
- percentage used and percentage remaining
- exposed limit, used, and remaining unit counts
- exact reset time in your chosen timezone
- UTC reset timestamp and epoch milliseconds for machine-readable output

The script has no runtime dependencies outside the Python standard library.

## ✨ Capabilities

- Human-friendly terminal panels with colour-coded usage bars
- Compact one-line output for small terminals and status panes
- JSON output for `jq`, automation, and monitoring integrations
- JSON Lines output for logs and append-only collection
- Raw API response mode for debugging endpoint changes
- Watch mode for a live refreshing quota dashboard
- Threshold mode with a separate exit code for cron and shell scripts
- Timezone control through `--timezone` or `ZAI_TIMEZONE`
- Installable as a signed Debian package, single executable script, or Python package

## 🚀 Installation

### Signed APT Repository

For Debian and Ubuntu hosts, use the signed GitHub Pages APT repository:

```bash
sudo install -d -m 0755 /etc/apt/keyrings
curl -fsSL https://soakes.github.io/quotai/quotai-archive-keyring.gpg \
  | sudo tee /etc/apt/keyrings/quotai-archive-keyring.gpg >/dev/null

sudo tee /etc/apt/sources.list.d/quotai.sources >/dev/null <<'EOF'
Types: deb deb-src
URIs: https://soakes.github.io/quotai/
Suites: stable
Components: main
Signed-By: /etc/apt/keyrings/quotai-archive-keyring.gpg
EOF

sudo apt update
sudo apt install quotai
```

### Download the Script

```bash
mkdir -p ~/.local/bin
curl -fsSL https://raw.githubusercontent.com/soakes/quotai/main/quotai.py -o ~/.local/bin/quotai
chmod +x ~/.local/bin/quotai
```

Make sure `~/.local/bin` is on your `PATH`.

### Install From Git

```bash
python3 -m pip install git+https://github.com/soakes/quotai.git
```

### Build From Source

```bash
git clone https://github.com/soakes/quotai.git
cd quotai
python3 -m pip install .
```

## ⚙️ Configuration

Set your Z.ai API key in the environment:

```bash
export ZAI_API_KEY='your-api-key'
```

Supported environment variables:

| Variable | Required | Description | Default |
|---|---:|---|---|
| `ZAI_API_KEY` | yes | Bearer token used to query the quota endpoint | none |
| `ZAI_API_URL` | no | Alternate quota endpoint, mainly useful for testing | `https://api.z.ai/api/monitor/usage/quota/limit` |
| `ZAI_TIMEZONE` | no | Timezone used for displayed reset times | `Europe/London` |

CLI flags take precedence over environment variables.

## 🧪 Usage

Run the default terminal view:

```bash
quotai
```

Example output:

```text
  Z.ai plan: pro

  │  5-Hour Rolling Token Quota
  │
  │  [████████████░░░░░░░░░░░░] 50% used
  │  Remaining: 50%
  │  Limit:      1.0M
  │  Used:       500.0k
  │  Remaining: 500.0k
  │  Resets in:   30m
  │  Resets at:   2026-05-23 15:00:00 BST
  ──────────────────────────────────
```

Show a compact status view:

```bash
quotai --compact
```

Use a specific timezone:

```bash
quotai --timezone America/New_York
```

Refresh every 30 seconds:

```bash
quotai --watch 30
```

Exit with code `2` if any quota is at or above 80 percent:

```bash
quotai --threshold 80
```

## 📋 Output Formats

| Format | Flag | Use case |
|---|---|---|
| Pretty | default | Human-readable terminal output |
| Compact | `--compact` | One line per quota |
| JSON | `--json` | Scripting, dashboards, and `jq` |
| JSON Lines | `--jsonl` | Logs and append-only collection |
| Raw | `--raw` | Debugging the upstream API response |

JSON output includes both local and UTC reset fields:

```bash
quotai --json | jq '.quotas[] | {quota: .name_compact, local: .resets_at, utc: .resets_at_utc}'
```

```json
{
  "quota": "5h-rolling",
  "local": "2026-05-23 15:00:00 BST",
  "utc": "2026-05-23T14:00:00Z"
}
```

## 🚪 Exit Codes

| Code | Meaning |
|---:|---|
| `0` | Success |
| `1` | Runtime or input error |
| `2` | Threshold exceeded when `--threshold` is set |

The separate threshold exit code makes it safe to distinguish quota pressure from a broken API key, network failure, or invalid response.

## 🛠️ Development

Create a local environment and install the development tools:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e '.[dev]'
```

Run the local checks:

```bash
make fmt-check
make lint
make test
make smoke
make version-check
```

Format code:

```bash
make fmt
```

Build a Python package:

```bash
make build
```

Build the website locally:

```bash
make website-build
```

## 🗂️ Project Structure

```text
quotai/
├── quotai.py                 # CLI application
├── tests/                    # Stdlib unittest coverage
├── debian/                   # Debian package metadata
├── docs/                     # Usage and release documentation
├── scripts/                  # Release helper scripts
├── .github/
│   ├── assets/website/       # GitHub Pages landing site
│   └── workflows/            # GitHub Actions release automation
├── AGENTS.md                 # Repository rules for coding agents
├── pyproject.toml            # Packaging and tool configuration
├── Makefile                  # Local validation shortcuts
├── LICENSE                   # MIT License
└── README.md                 # Project overview
```

## 📄 License

`quotai` is released under the [MIT License](LICENSE).
