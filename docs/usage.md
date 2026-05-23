# Usage Guide

This guide covers day-to-day use of `quotai`.

## Authentication

`quotai` expects a Z.ai API key. The safest normal setup is to keep it in your shell environment:

```bash
export ZAI_API_KEY='your-api-key'
```

You can also pass it directly:

```bash
quotai --api-key 'your-api-key'
```

Passing secrets on the command line can leave them in shell history and process listings, so the environment variable is preferred.

## Timezones

Reset times are displayed in `Europe/London` by default. Override that with:

```bash
quotai --timezone America/New_York
```

or:

```bash
export ZAI_TIMEZONE=America/New_York
quotai
```

Use an IANA timezone name such as `Europe/London`, `UTC`, `America/New_York`, or `Asia/Tokyo`.

## Common Commands

Pretty terminal output:

```bash
quotai
```

Compact terminal output:

```bash
quotai --compact
```

Machine-readable JSON:

```bash
quotai --json
```

JSON Lines:

```bash
quotai --jsonl
```

Raw upstream response:

```bash
quotai --raw
```

Live dashboard:

```bash
quotai --watch 30
```

Threshold alert:

```bash
quotai --threshold 80
```

## JSON Fields

Each quota item contains display-friendly and script-friendly reset fields:

| Field | Description |
|---|---|
| `resets_in` | Compact duration until reset, such as `30m` or `6d 2h 1m` |
| `resets_at` | Local reset time using the selected timezone |
| `resets_at_utc` | UTC reset time in ISO-8601 form |
| `reset_epoch_ms` | Upstream reset time as epoch milliseconds |
| `timezone` | Timezone used for the local display field |

Example:

```bash
quotai --json | jq '.quotas[] | select(.name_compact == "5h-rolling")'
```

## Cron Example

This exits with code `2` when any quota reaches 80 percent. A runtime error still exits with code `1`.

```cron
*/10 * * * * ZAI_API_KEY=your-api-key /usr/local/bin/quotai --threshold 80 >/tmp/quotai.log 2>&1
```

## Troubleshooting

### Missing API key

```text
ERROR: ZAI_API_KEY is not set
```

Set `ZAI_API_KEY` or pass `--api-key`.

### Unknown timezone

If an invalid timezone is supplied, `quotai` prints a warning and falls back to `Europe/London`.

### HTTP errors

`quotai` prints the HTTP status, reason, and response body when the server provides one. Check that the API key is valid and that the quota endpoint has not changed.

### Invalid JSON or response shape

Use `--raw` to inspect the upstream response:

```bash
quotai --raw
```
