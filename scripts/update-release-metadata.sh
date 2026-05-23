#!/usr/bin/env bash
set -euo pipefail

release_tag="${1:?stable release tag is required}"
previous_tag="${2:-}"
to_ref="${3:-HEAD}"
suite="${4:-stable}"

if [[ ! "${release_tag}" =~ ^v([0-9]+\.[0-9]+\.[0-9]+)$ ]]; then
  echo "expected a stable release tag like v1.2.3, got: ${release_tag}" >&2
  exit 1
fi

target_version="${BASH_REMATCH[1]}"

bash scripts/update-debian-changelog.sh "${release_tag}" "${previous_tag}" "${to_ref}" "${suite}"

python3 - "${target_version}" <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path

version = sys.argv[1]
updates = (
    (
        Path("quotai.py"),
        r'(?m)^VERSION = "[^"]+"$',
        f'VERSION = "{version}"',
        "quotai.py VERSION",
    ),
    (
        Path("pyproject.toml"),
        r'(?m)^version = "[^"]+"$',
        f'version = "{version}"',
        "pyproject.toml project.version",
    ),
)

for path, pattern, replacement, label in updates:
    text = path.read_text(encoding="utf-8")
    new_text, count = re.subn(pattern, replacement, text, count=1)
    if count != 1:
        raise SystemExit(f"could not update {label}")
    path.write_text(new_text, encoding="utf-8")
PY

bash scripts/check-version-consistency.sh "${release_tag}"
