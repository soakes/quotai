from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone
from io import StringIO
from unittest.mock import patch

import quotai


def reset_ms() -> int:
    return int(datetime(2026, 5, 23, 14, 0, tzinfo=timezone.utc).timestamp() * 1000)


def sample_payload() -> dict[str, object]:
    return {
        "success": True,
        "data": {
            "level": "pro",
            "limits": [
                {
                    "type": "TOKENS_LIMIT",
                    "unit": 3,
                    "number": 5,
                    "percentage": 50,
                    "usage": 1_000_000,
                    "currentValue": 500_000,
                    "remaining": 500_000,
                    "nextResetTime": reset_ms(),
                    "usageDetails": [
                        {"modelCode": "glm-4.5", "usage": 1234},
                    ],
                }
            ],
        },
    }


class QuotaFormattingTests(unittest.TestCase):
    def test_format_duration_keeps_three_largest_units(self) -> None:
        self.assertEqual(quotai.format_duration(90061), "1d 1h 1m")
        self.assertEqual(quotai.format_duration(0), "now")

    def test_progress_bar_clamps_out_of_range_percentages(self) -> None:
        negative = quotai.progress_bar(-20, width=4, use_color=False)
        too_large = quotai.progress_bar(140, width=4, use_color=False)

        self.assertEqual(negative, quotai.BAR_EMPTY * 4)
        self.assertEqual(too_large, quotai.BAR_FILLED * 4)

    def test_build_quota_item_includes_exact_reset_times(self) -> None:
        _, limits = quotai.parse_payload(sample_payload())
        now = datetime(2026, 5, 23, 13, 30, tzinfo=timezone.utc)

        item = quotai.build_quota_item(limits[0], quotai.get_timezone("Europe/London"), now)

        self.assertEqual(item["name_compact"], "5h-rolling")
        self.assertEqual(item["resets_in"], "30m")
        self.assertEqual(item["resets_at"], "2026-05-23 15:00:00 BST")
        self.assertEqual(item["resets_at_utc"], "2026-05-23T14:00:00Z")
        self.assertEqual(item["reset_epoch_ms"], reset_ms())
        self.assertEqual(item["timezone"], "Europe/London")

    def test_json_lines_contains_script_friendly_reset_fields(self) -> None:
        _, limits = quotai.parse_payload(sample_payload())
        item = quotai.build_quota_item(
            limits[0],
            quotai.get_timezone("Europe/London"),
            datetime(2026, 5, 23, 13, 30, tzinfo=timezone.utc),
        )

        line = json.loads(quotai.output_json_lines("pro", [item]))

        self.assertEqual(line["quota"], "5h-rolling")
        self.assertEqual(line["resets_at_utc"], "2026-05-23T14:00:00Z")
        self.assertEqual(line["reset_epoch_ms"], reset_ms())


class MainTests(unittest.TestCase):
    def test_raw_output_prints_payload_without_parsing_assertion(self) -> None:
        stdout = StringIO()

        with (
            patch("quotai.fetch_json", return_value=sample_payload()),
            patch("sys.stdout", new=stdout),
        ):
            code = quotai.main(["--raw", "--api-key", "test"])

        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout.getvalue()), sample_payload())

    def test_raw_output_cannot_be_combined_with_threshold(self) -> None:
        stderr = StringIO()

        with patch("sys.stderr", new=stderr):
            code = quotai.main(["--raw", "--threshold", "80", "--api-key", "test"])

        self.assertEqual(code, 1)
        self.assertIn("--threshold cannot be used with --raw", stderr.getvalue())

    def test_threshold_must_be_a_percentage(self) -> None:
        stderr = StringIO()

        with patch("sys.stderr", new=stderr):
            code = quotai.main(["--threshold", "101", "--api-key", "test"])

        self.assertEqual(code, 1)
        self.assertIn("--threshold must be between 0 and 100", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
