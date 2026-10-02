"""tt — тайм-трекер у терміналі. Поведінка: spec.md."""
import json
import os
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta


class TTError(Exception):
    pass


def path():
    return os.environ.get("TT_FILE") or os.path.expanduser("~/.tt.json")


def load():
    try:
        with open(path()) as f:
            return json.load(f)["entries"]
    except FileNotFoundError:
        return []
    except (ValueError, KeyError, TypeError) as e:
        raise TTError(f"corrupted data file {path()}: {e}")


def save(entries):
    with open(path(), "w") as f:
        json.dump({"entries": entries}, f, indent=2)


def fmt(delta):
    h, m = divmod(int(delta.total_seconds()) // 60, 60)
    return f"{h}h {m:02d}m" if h else f"{m}m"


def running(entries):
    return next((e for e in entries if e["end"] is None), None)


def cmd_start(args, now):
    task = " ".join(args).strip()
    if not task:
        raise TTError("task name is required")
    entries = load()
    if cur := running(entries):
        raise TTError(f"already running: {cur['task']}")
    entries.append({"task": task, "start": now.isoformat(), "end": None})
    save(entries)
    print(f"▶ started: {task}")


def cmd_stop(args, now):
    entries = load()
    cur = running(entries)
    if not cur:
        raise TTError("nothing running")
    cur["end"] = now.isoformat()
    save(entries)
    print(f"■ stopped: {cur['task']} ({fmt(now - datetime.fromisoformat(cur['start']))})")


def cmd_status(args, now):
    cur = running(load())
    if cur:
        print(f"▶ {cur['task']} — {fmt(now - datetime.fromisoformat(cur['start']))}")
    else:
        print("nothing running")


def cmd_report(args, now):
    day = now.date()
    if args:
        if len(args) != 2 or args[0] != "--date":
            raise TTError("usage: tt report [--date YYYY-MM-DD]")
        try:
            day = date.fromisoformat(args[1])
            if day.isoformat() != args[1]:  # 3.11+ приймає й 20261002, 2026-W40-5
                raise ValueError
        except ValueError:
            raise TTError(f"invalid date: {args[1]} (expected YYYY-MM-DD)")
    totals = defaultdict(timedelta)
    for e in load():
        start = datetime.fromisoformat(e["start"])
        if start.date() == day:  # правило 5: запис належить дню старту
            end = datetime.fromisoformat(e["end"]) if e["end"] else now
            totals[e["task"]] += end - start
    for task, d in sorted(totals.items(), key=lambda kv: kv[1], reverse=True):
        print(f"{task}  {fmt(d)}")
    print(f"total  {fmt(sum(totals.values(), timedelta()))}")


COMMANDS = {"start": cmd_start, "stop": cmd_stop, "status": cmd_status, "report": cmd_report}


def main(argv, now):
    if not argv or argv[0] not in COMMANDS:
        print("usage: tt start <task> | stop | status | report [--date YYYY-MM-DD]", file=sys.stderr)
        return 1
    try:
        COMMANDS[argv[0]](argv[1:], now)
    except TTError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], datetime.now()))
