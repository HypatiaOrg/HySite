"""Record, list and restore HySite update runs in the hysite_ops.deployments MongoDB collection.

Each run of the weekly update job (scripts/hysite_update.sh) is one document, holding everything
needed to see what production ran and to rebuild it:

    _id           run id, the UTC start time, e.g. "2026-10-12T06-17-00Z"
    status        latest status: running, unchanged, test_failed, deployed, rolled_back, ...
    events        [{time, status, message}], every status change in order
    host, git     server name; branch, commit and commit subject deployed
    versions_env  the exact image versions, {variable: "tag@sha256:..."}
    lock_files    {path: file contents}, the exact package versions
    installed     {service: {python, packages: {name: version}}}, what the built images contain
    smoke_test    {stage: output}, the smoke test results

Uses a database user with readWrite on hysite_ops only (not the website's read-only user), set by
these environment variables. They all start with OPS_ so that Docker Compose, which gives
environment variables priority over .env files, never mistakes them for the website's settings.
    OPS_CONNECTION_STRING                        or the parts below
    OPS_MONGO_HOST, OPS_MONGO_PORT, OPS_USERNAME, OPS_PASSWORD, OPS_AUTH_SOURCE (default admin)
    OPS_CLIENT_TLS                               true (default) or false

Runs inside the backend image, which has pymongo; scripts/hysite_update.sh shows how.

    python scripts/deployments.py record <run dir> --status deployed --message "..."
    python scripts/deployments.py list [--limit 10]
    python scripts/deployments.py restore <run id>      # write that run's versions.env and lock files
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus

import pymongo

REPO = Path(__file__).resolve().parent.parent
# files that pin the versions, relative to the repository
PINNED_FILES = ["versions.env", "backend/requirements.lock", "frontend-web2py/requirements.lock"]


def collection() -> pymongo.collection.Collection:
    uri = os.environ.get("OPS_CONNECTION_STRING")
    if not uri:
        uri = (f"mongodb://{quote_plus(os.environ['OPS_USERNAME'])}:{quote_plus(os.environ['OPS_PASSWORD'])}"
               f"@{os.environ.get('OPS_MONGO_HOST', 'hypatiacatalog.com')}:{os.environ.get('OPS_MONGO_PORT', '27017')}"
               f"/?authSource={os.environ.get('OPS_AUTH_SOURCE', 'admin')}")
    tls = os.environ.get("OPS_CLIENT_TLS", "true").lower() == "true"
    client = pymongo.MongoClient(uri, tls=tls, serverSelectionTimeoutMS=20_000)
    return client.hysite_ops.deployments


def read_env_file(path: Path) -> dict[str, str]:
    lines = path.read_text().splitlines() if path.exists() else []
    return dict(line.split("=", 1) for line in lines if "=" in line and not line.startswith("#"))


def read_installed(path: Path) -> dict:
    """Parse the output of 'python --version; pip freeze'."""
    lines = path.read_text().splitlines()
    python = next((line.split()[1] for line in lines if line.startswith("Python ")), None)
    packages = dict(line.split("==", 1) for line in lines if "==" in line)
    # MongoDB field names cannot contain "."
    return {"python": python, "packages": {name.replace(".", "_"): version for name, version in packages.items()}}


def record(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir)
    run = json.loads((run_dir / "run.json").read_text())
    now = datetime.now(timezone.utc)
    fields = {
        "status": args.status,
        "updated": now,
        "host": run.get("host"),
        "git": run.get("git"),
        "started": datetime.fromisoformat(run["started"]),
    }
    if (run_dir / "pinned").exists():
        fields["versions_env"] = read_env_file(run_dir / "pinned" / "versions.env")
        fields["lock_files"] = {name.replace(".", "_"): (run_dir / "pinned" / name).read_text()
                                for name in PINNED_FILES[1:] if (run_dir / "pinned" / name).exists()}
    installed = {path.stem.removeprefix("installed-"): read_installed(path)
                 for path in run_dir.glob("installed-*.txt")}
    if installed:
        fields["installed"] = installed
    smoke = {path.stem.removeprefix("smoke-"): path.read_text() for path in run_dir.glob("smoke-*.txt")}
    if smoke:
        fields["smoke_test"] = smoke
    collection().update_one(
        {"_id": run["run_id"]},
        {"$set": fields, "$push": {"events": {"time": now, "status": args.status, "message": args.message}}},
        upsert=True,
    )
    print(f"Recorded {run['run_id']}: {args.status}")


def list_runs(args: argparse.Namespace) -> None:
    for doc in collection().find({}, {"status": 1, "git": 1, "versions_env": 1}).sort("_id", -1).limit(args.limit):
        commit = (doc.get("git") or {}).get("commit", "")[:8]
        pythons = ", ".join(re.sub(r"@.*", "", value) for key, value in (doc.get("versions_env") or {}).items()
                            if key.endswith("BASE_IMAGE"))
        print(f"{doc['_id']}  {doc.get('status', ''):<14} {commit:<9} {pythons}")


def restore(args: argparse.Namespace) -> None:
    doc = collection().find_one({"_id": args.run_id})
    if doc is None or not doc.get("versions_env"):
        sys.exit(f"No versions recorded for run {args.run_id}")
    lines = [f"# Restored from hysite_ops.deployments run {args.run_id}"]
    lines += [f"{key}={value}" for key, value in doc["versions_env"].items()]
    (REPO / "versions.env").write_text("\n".join(lines) + "\n")
    for name in PINNED_FILES[1:]:
        (REPO / name).write_text(doc["lock_files"][name.replace(".", "_")])
    print(f"Restored versions.env and lock files from run {args.run_id} (git commit "
          f"{(doc.get('git') or {}).get('commit', 'unknown')[:8]})")


def main() -> None:
    parser = argparse.ArgumentParser(description="HySite update runs in hysite_ops.deployments")
    commands = parser.add_subparsers(required=True)
    record_parser = commands.add_parser("record", help="add or update the record for a run")
    record_parser.add_argument("run_dir")
    record_parser.add_argument("--status", required=True)
    record_parser.add_argument("--message", default="")
    record_parser.set_defaults(func=record)
    list_parser = commands.add_parser("list", help="show recent runs")
    list_parser.add_argument("--limit", type=int, default=10)
    list_parser.set_defaults(func=list_runs)
    restore_parser = commands.add_parser("restore", help="write a run's versions.env and lock files")
    restore_parser.add_argument("run_id")
    restore_parser.set_defaults(func=restore)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
