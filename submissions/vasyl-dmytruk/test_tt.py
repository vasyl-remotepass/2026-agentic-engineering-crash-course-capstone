"""Тести tt за spec.md. Контракт: tt.main(argv, now) -> код виходу; дані в $TT_FILE."""
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta
from unittest import mock

import tt

T0 = datetime(2026, 10, 2, 10, 0)


class TTTest(unittest.TestCase):
    def setUp(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.path = os.path.join(d.name, "tt.json")
        p = mock.patch.dict(os.environ, {"TT_FILE": self.path})
        p.start()
        self.addCleanup(p.stop)

    def run_tt(self, *argv, now=T0):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = tt.main(list(argv), now=now)
        return code, out.getvalue().strip(), err.getvalue().strip()

    def entries(self):
        with open(self.path) as f:
            return json.load(f)["entries"]

    def write(self, entries):
        with open(self.path, "w") as f:
            json.dump({"entries": entries}, f)

    # --- start ---

    def test_start_joins_args_into_task_name(self):
        code, out, _ = self.run_tt("start", "write", "spec")
        self.assertEqual(code, 0)
        self.assertEqual(out, "▶ started: write spec")
        self.assertEqual(self.entries(), [{"task": "write spec", "start": T0.isoformat(), "end": None}])

    def test_start_while_running_is_error_and_changes_nothing(self):  # правило 1
        self.run_tt("start", "docs")
        before = self.entries()
        code, out, err = self.run_tt("start", "other", now=T0 + timedelta(minutes=5))
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("docs", err)
        self.assertEqual(self.entries(), before)

    def test_start_empty_name_is_error(self):  # правило 3
        for argv in (["start"], ["start", "  "]):
            code, _, err = self.run_tt(*argv)
            self.assertEqual(code, 1, argv)
            self.assertNotEqual(err, "", argv)
        self.assertFalse(os.path.exists(self.path))

    # --- stop ---

    def test_stop_closes_running_entry(self):
        self.run_tt("start", "docs")
        code, out, _ = self.run_tt("stop", now=T0 + timedelta(minutes=25, seconds=40))
        self.assertEqual(code, 0)
        self.assertEqual(out, "■ stopped: docs (25m)")
        self.assertEqual(self.entries()[0]["end"], (T0 + timedelta(minutes=25, seconds=40)).isoformat())

    def test_stop_when_nothing_running_is_error(self):  # правило 2
        code, out, err = self.run_tt("stop")
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertNotEqual(err, "")

    # --- status ---

    def test_status_running(self):
        self.run_tt("start", "docs")
        self.assertEqual(self.run_tt("status", now=T0 + timedelta(minutes=12)), (0, "▶ docs — 12m", ""))

    def test_status_nothing_running(self):
        self.assertEqual(self.run_tt("status"), (0, "nothing running", ""))

    # --- report ---

    def report_lines(self, *args, now):
        code, out, _ = self.run_tt("report", *args, now=now)
        self.assertEqual(code, 0)
        return [line.split(None, 1) for line in out.splitlines()]

    def test_report_sums_per_task_sorted_desc_with_total(self):
        h = lambda hh, mm: datetime(2026, 10, 2, hh, mm).isoformat()
        self.write([
            {"task": "review", "start": h(9, 0), "end": h(9, 20)},
            {"task": "docs", "start": h(10, 0), "end": h(10, 45)},
            {"task": "docs", "start": h(11, 0), "end": h(11, 20)},
            {"task": "old", "start": "2026-10-01T09:00:00", "end": "2026-10-01T10:00:00"},
        ])
        lines = self.report_lines(now=datetime(2026, 10, 2, 18, 0))
        self.assertEqual(lines, [["docs", "1h 05m"], ["review", "20m"], ["total", "1h 25m"]])

    def test_report_counts_running_timer_up_to_now(self):  # правило 4
        self.run_tt("start", "docs")
        lines = self.report_lines(now=T0 + timedelta(minutes=30))
        self.assertEqual(lines, [["docs", "30m"], ["total", "30m"]])

    def test_report_date_option_and_midnight_belongs_to_start_day(self):  # правило 5
        self.write([{"task": "late", "start": "2026-10-01T23:30:00", "end": "2026-10-02T00:40:00"}])
        self.assertEqual(self.report_lines("--date", "2026-10-01", now=T0),
                         [["late", "1h 10m"], ["total", "1h 10m"]])
        self.assertEqual(self.report_lines(now=T0), [["total", "0m"]])

    def test_report_bad_date_is_error(self):
        code, _, err = self.run_tt("report", "--date", "02.10.2026")
        self.assertEqual(code, 1)
        self.assertNotEqual(err, "")

    # --- дані ---

    def test_missing_file_is_empty_log(self):
        self.assertEqual(self.run_tt("status"), (0, "nothing running", ""))

    def test_corrupted_file_is_error_and_not_overwritten(self):  # «Дані»
        with open(self.path, "w") as f:
            f.write("{not json")
        for argv in (["start", "docs"], ["stop"], ["status"], ["report"]):
            code, _, err = self.run_tt(*argv)
            self.assertEqual(code, 1, argv)
            self.assertNotEqual(err, "", argv)
        with open(self.path) as f:
            self.assertEqual(f.read(), "{not json")


class FormatTest(unittest.TestCase):  # правило 6
    def test_format_duration(self):
        cases = {0: "0m", 59: "0m", 60: "1m", 59 * 60: "59m", 3600: "1h 00m", 3900: "1h 05m", 10 * 3600: "10h 00m"}
        for seconds, expected in cases.items():
            self.assertEqual(tt.fmt(timedelta(seconds=seconds)), expected, seconds)


if __name__ == "__main__":
    unittest.main()
