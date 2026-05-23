#!/usr/bin/env bash
set -euo pipefail

tag="${1:?tag is required}"
sha="${2:?release sha is required}"
shift 2

if [ "$#" -eq 0 ]; then
  echo "At least one workflow filename is required" >&2
  exit 1
fi

deadline="$((SECONDS + 1800))"

wait_for_workflow() {
  local workflow="$1"
  local run_fields=""
  local status=""
  local conclusion=""
  local database_id=""

  while [ "${SECONDS}" -lt "${deadline}" ]; do
    run_fields="$(
      gh run list \
        --workflow "${workflow}" \
        --json databaseId,headSha,status,conclusion,event,headBranch \
        --limit 50 \
        --jq "(map(select(.headSha == \"${sha}\" and .event == \"push\" and .headBranch == \"${tag}\")) | first // empty) | [.databaseId, .status, (.conclusion // \"\")] | @tsv"
    )"

    if [ -z "${run_fields}" ] || [ "${run_fields}" = "null" ]; then
      sleep 10
      continue
    fi

    IFS=$'\t' read -r database_id status conclusion <<< "${run_fields}"

    case "${status}" in
      completed)
        if [ "${conclusion}" = "success" ]; then
          echo "${workflow} completed successfully for ${tag}."
          return 0
        fi
        echo "${workflow} failed for ${tag} with conclusion: ${conclusion}" >&2
        gh run view "${database_id}" --log-failed >&2 || true
        return 1
        ;;
      *)
        echo "Waiting for ${workflow} run ${database_id} for ${tag}; current status: ${status}."
        sleep 15
        ;;
    esac
  done

  echo "Timed out waiting for ${workflow} for ${tag}." >&2
  return 1
}

for workflow in "$@"; do
  wait_for_workflow "${workflow}"
done
