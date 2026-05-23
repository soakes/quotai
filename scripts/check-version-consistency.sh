#!/usr/bin/env bash
set -euo pipefail

release_ref="${1:-}"

extract_single() {
  local pattern="$1"
  local path="$2"
  local label="$3"
  local value=""

  value="$(sed -n "${pattern}" "${path}" | head -n1)"
  if [ -z "${value}" ]; then
    echo "could not parse ${label} from ${path}" >&2
    exit 1
  fi

  printf '%s\n' "${value}"
}

pyproject_version="$(extract_single 's/^version = "\([^"]*\)"/\1/p' pyproject.toml 'project.version')"
cli_version="$(extract_single 's/^VERSION = "\([^"]*\)"/\1/p' quotai.py 'VERSION')"
debian_full_version="$(extract_single '1s/^[^(]*(\([^)]*\)).*/\1/p' debian/changelog 'Debian changelog version')"
debian_upstream_version="${debian_full_version%-*}"
debian_stable_version="${debian_upstream_version%%~rc.*}"

if [ "${pyproject_version}" != "${cli_version}" ]; then
  echo "version mismatch: pyproject.toml has ${pyproject_version}, quotai.py has ${cli_version}" >&2
  exit 1
fi

if [ "${pyproject_version}" != "${debian_stable_version}" ]; then
  echo "version mismatch: project version is ${pyproject_version}, debian/changelog targets ${debian_stable_version}" >&2
  exit 1
fi

if [ -z "${release_ref}" ]; then
  release_ref="$(
    git tag --points-at HEAD --list 'v*' \
      | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+(-rc\.[0-9]+)?$' \
      | head -n1 || true
  )"
fi

if [ -n "${release_ref}" ]; then
  if [[ ! "${release_ref}" =~ ^v([0-9]+\.[0-9]+\.[0-9]+)(-rc\.[0-9]+)?$ ]]; then
    echo "unsupported release tag format: ${release_ref}" >&2
    exit 1
  fi

  expected_version="${BASH_REMATCH[1]}"
  if [ "${pyproject_version}" != "${expected_version}" ]; then
    echo "version mismatch: ${release_ref} expects ${expected_version}, project has ${pyproject_version}" >&2
    exit 1
  fi
fi

printf 'version consistency OK: %s\n' "${pyproject_version}"
