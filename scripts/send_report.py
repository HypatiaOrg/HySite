#!/usr/bin/env python3
"""Email a report of one run of the update job: status, code, image and package changes, test results.

scripts/hysite_update.sh sends it at the end of every run, also when nothing changed (so the report
doubles as proof that the job ran), to HYSITE_REPORT_EMAIL when that is set in /etc/hysite/update.env.
It goes through the same account as the failure alerts (ALERT_SMTP_*, scripts/send_mail.py).
Everything in it comes from the run's folder (.update/runs/<run id>) and the versions from before the
run (.update/backup).

    python3 scripts/send_report.py .update/runs/<run id>            # send it
    python3 scripts/send_report.py .update/runs/<run id> --print    # show the text, send nothing
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

import send_mail

LOCK_FILES = {"backend": "backend/requirements.lock", "frontend-web2py": "frontend-web2py/requirements.lock"}
SERVICES = {"django-api": "backend", "web-to-py": "frontend-web2py"}  # image name -> what people call it
PACKAGE = re.compile(r"^([A-Za-z0-9_.-]+)==(\S+)")


def read_text(path: Path) -> str:
    return path.read_text() if path.exists() else ""


def env_file(path: Path) -> dict[str, str]:
    lines = read_text(path).splitlines()
    return dict(line.split("=", 1) for line in lines if "=" in line and not line.startswith("#"))


def packages(path: Path) -> dict[str, str]:
    found = (PACKAGE.match(line) for line in read_text(path).splitlines())
    return {match[1].lower(): match[2] for match in found if match}


def image_lines(before: dict[str, str], after: dict[str, str]) -> list[str]:
    lines = []
    for variable, image in after.items():
        if not variable.endswith("_IMAGE"):
            continue
        tag, _, digest = image.partition("@")
        old_tag, _, old_digest = before.get(variable, "").partition("@")
        if not old_tag:
            change = "new"
        elif old_tag != tag:
            change = f"was {old_tag}"
        elif old_digest != digest:
            change = "new build of the same tag"
        else:
            change = "unchanged"
        lines.append(f"  {variable:<20} {tag:<20} {change}")
    return lines or ["  (no versions.env)"]


def package_lines(name: str, before: dict[str, str], after: dict[str, str]) -> list[str]:
    if not after:
        return [f"  {name}: (no lock file)"]
    updated = [(p, before[p], v) for p, v in after.items() if p in before and before[p] != v]
    added = [p for p in after if p not in before]
    removed = [p for p in before if p not in after]
    if not before:
        return [f"  {name}: {len(after)} packages, first lock file"]
    if not (updated or added or removed):
        return [f"  {name}: unchanged ({len(after)} packages)"]
    parts = [f"{len(updated)} updated" if updated else "", f"{len(added)} added" if added else "",
             f"{len(removed)} removed" if removed else ""]
    lines = [f"  {name}: " + ", ".join(part for part in parts if part)]
    lines += [f"    {p} {old} -> {new}" for p, old, new in updated]
    lines += [f"    + {p} {after[p]}" for p in added]
    lines += [f"    - {p} {before[p]}" for p in removed]
    return lines


def smoke_line(path: Path) -> str:
    lines = [line for line in read_text(path).splitlines() if line.strip()]
    if not lines:
        return "not run"
    failed = [line for line in lines if line.startswith("FAIL")]
    summary = lines[-1] if "checks passed" in lines[-1] else "no summary line (interrupted?)"
    return summary + "".join(f"\n    {line}" for line in failed[:10])


def duration(started: datetime, finished: datetime) -> str:
    seconds = int((finished - started).total_seconds())
    return f"{seconds // 60} min {seconds % 60} s" if seconds >= 60 else f"{seconds} s"


def report(run_dir: Path, before_dir: Path) -> tuple[str, str]:
    """(subject, body) for the run in run_dir, compared with the versions in before_dir."""
    run = json.loads(read_text(run_dir / "run.json") or "{}")
    run_id = run.get("run_id", run_dir.name)
    host = run.get("host", "?")
    git = run.get("git") or {}
    events = [line.split(" ", 2) for line in read_text(run_dir / "events.txt").splitlines() if line.strip()]
    status, message = (events[-1][1], events[-1][2] if len(events[-1]) > 2 else "") if events else ("?", "no status recorded")
    started = datetime.fromisoformat(run["started"]) if "started" in run else None
    now = datetime.now(timezone.utc)
    pinned = run_dir / "pinned"

    lines = [f"HySite update run {run_id} on {host}",
             f"Status: {status} - {message}"]
    if started:
        lines.append(f"Started {started:%Y-%m-%d %H:%M} UTC, took {duration(started, now)}")
    lines += ["", "Code",
              f"  {git.get('branch', '?')} {git.get('commit', '?')[:8]}  {git.get('subject', '')}".rstrip()]
    lines += ["", "Images (the exact versions in versions.env)"]
    lines += image_lines(env_file(before_dir / "versions.env"), env_file(pinned / "versions.env"))
    lines += ["", "Packages"]
    for name, lock in LOCK_FILES.items():
        lines += package_lines(name, packages(before_dir / lock), packages(pinned / lock))
    lines += ["", "Tests",
              f"  sample database: {smoke_line(run_dir / 'smoke-test.txt')}",
              f"  production:      {smoke_line(run_dir / 'smoke-production.txt')}"]
    if (run_dir / "smoke-rollback.txt").exists():
        lines.append(f"  after rollback:  {smoke_line(run_dir / 'smoke-rollback.txt')}")
    pythons = []
    for image, name in SERVICES.items():
        first = read_text(run_dir / f"installed-{image}.txt").splitlines()[:1]
        if first and first[0].startswith("Python "):
            pythons.append(f"{name} {first[0].split()[1]}")
    if pythons:
        lines.append("  Python: " + ", ".join(pythons))
    lines += ["", "Steps"] + [f"  {' '.join(event)}" for event in events]
    if status not in ("deployed", "unchanged"):
        lines += ["", "The failure alert email has the log. On the server:",
                  "  journalctl --unit hysite-update.service --invocation 0"]
    lines += ["", "Every run: scripts/rollback.sh --list on the server, or the hysite_ops.deployments collection."]
    subject = f"[HySite] {status}: weekly update of {run_id[:10]} on {host}"
    return subject, "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("run_dir", type=Path, help=".update/runs/<run id>")
    parser.add_argument("--before", type=Path, help="the versions from before the run (default: .update/backup)")
    parser.add_argument("--print", action="store_true", help="show the report, send nothing")
    args = parser.parse_args()
    before = args.before or args.run_dir.resolve().parent.parent / "backup"
    subject, body = report(args.run_dir, before)
    if args.print:
        print(f"Subject: {subject}\n\n{body}", end="")
        return
    recipients = os.environ.get("HYSITE_REPORT_EMAIL", "").strip()
    if not recipients:
        sys.exit("HYSITE_REPORT_EMAIL is not set; no report to send")
    message = EmailMessage()
    message["To"] = recipients
    message["From"] = os.environ.get("ALERT_FROM") or f"hysite@{os.uname().nodename}"
    message["Subject"] = subject
    message.set_content(body)
    send_mail.send(message)


if __name__ == "__main__":
    try:
        main()
    except (OSError, send_mail.smtplib.SMTPException) as error:
        sys.exit(f"Could not send the report: {error}")
