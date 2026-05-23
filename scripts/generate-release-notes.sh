#!/usr/bin/env bash
set -euo pipefail

previous_tag="${1:-}"
release_sha="${2:-HEAD}"
output="${3:-release-notes.md}"
release_ref="${4:-}"

if [ -z "${release_ref}" ]; then
  release_ref="$(git describe --tags --exact-match "${release_sha}" 2>/dev/null || git rev-parse --short "${release_sha}")"
fi

range="${release_sha}"
if [ -n "${previous_tag}" ]; then
  range="${previous_tag}..${release_sha}"
fi

mkdir -p "$(dirname "${output}")"
asset_version="${release_ref#v}"
debian_version="${asset_version/-rc./~rc.}"

{
  printf "## Included Changes\n\n"

  changes="$(git log --reverse --pretty=format:'- %s (%h)' "${range}" || true)"
  if [ -n "${changes}" ]; then
    printf "%s\n\n" "${changes}"
  else
    printf "No commit summary was available for this release.\n\n"
  fi

  printf "## Published Artifacts\n\n"
  printf -- "- \`quotai-%s.tar.gz\`\n" "${asset_version}"
  printf -- "- Debian package \`quotai_%s-1_all.deb\`\n" "${debian_version}"
  printf -- "- Debian source package files\n"
  printf -- "- Signed APT repository metadata on GitHub Pages for stable releases\n"
  printf -- "- \`sha256sums.txt\`\n"
} > "${output}"
