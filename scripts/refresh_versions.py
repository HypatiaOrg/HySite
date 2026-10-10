#!/usr/bin/env python3
"""Resolve HySite's software to the newest exact versions, for testing and deploying.

Git holds only what to follow:
  - the image tags in compose.yaml, e.g. ${BACKEND_BASE_IMAGE:-python:3.14-alpine}
  - the unpinned package lists, backend/requirements.txt and frontend-web2py/requirements.txt

This script resolves those to exact versions, in files that git ignores:
  - versions.env: each image tag with the @sha256 digest it points to today, and
    REQUIREMENTS=requirements.lock so builds use the lock files
  - backend/requirements.lock, frontend-web2py/requirements.lock: every package at an exact version

The weekly update job on the server (scripts/hysite_update.sh) runs this, tests the result and
deploys it, and records the versions in the hysite_ops.deployments database collection.
Compose reads versions.env when it is listed in COMPOSE_ENV_FILES (e.g. COMPOSE_ENV_FILES=.env,versions.env).

Each lock file is compiled inside the service's own pinned base image, so it matches the Python
version and platform (Alpine, musl) it will be installed on. Needs Docker with buildx.

    python3 scripts/refresh_versions.py
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
COMPOSE_FILE = REPO / "compose.yaml"
VERSIONS_FILE = REPO / "versions.env"
# service directory -> the compose variable holding its Python base image
LOCKED_SERVICES = {"backend": "BACKEND_BASE_IMAGE", "frontend-web2py": "FRONTEND_BASE_IMAGE"}

# image variables with their default tag in compose.yaml, e.g. ${NGINX_IMAGE:-nginx:latest}
IMAGE_VARIABLE = re.compile(r"\$\{(\w+_IMAGE):-([^}]+)\}")
COMPILE_COMMAND = "python3 scripts/refresh_versions.py"


def run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"Command failed: {' '.join(cmd)}\n{result.stderr}")
    return result.stdout


def image_tags() -> dict[str, str]:
    """The image tag to follow for each image variable in compose.yaml."""
    return dict(IMAGE_VARIABLE.findall(COMPOSE_FILE.read_text()))


def resolve_digest(tag: str) -> str:
    """The digest the tag points to now (the multi-platform index, so it works on any CPU)."""
    manifest = json.loads(run(["docker", "buildx", "imagetools", "inspect", tag,
                               "--format", "{{json .Manifest}}"]))
    return manifest["digest"]


def compile_lock(service_dir: Path, image: str) -> None:
    """Compile requirements.txt into requirements.lock inside the service's base image."""
    print(f"  {service_dir.name}/requirements.lock in {image.split('@')[0]}")
    script = (
        "python -m pip install --quiet --disable-pip-version-check --target /tmp/uv uv"
        " && /tmp/uv/bin/uv pip compile requirements.txt --upgrade --quiet"
        f" --output-file requirements.lock --custom-compile-command '{COMPILE_COMMAND}'"
    )
    run(["docker", "run", "--rm",
         # write the lock file as the current user, not root
         "--user", f"{os.getuid()}:{os.getgid()}",
         "--env", "HOME=/tmp", "--env", "UV_CACHE_DIR=/tmp/uv-cache",
         "--volume", f"{service_dir}:/work", "--workdir", "/work",
         image, "sh", "-c", script])


def main() -> None:
    argparse.ArgumentParser(description=__doc__.split("\n")[0]).parse_args()

    print("Resolving image tags in compose.yaml")
    pinned = {}
    for variable, tag in image_tags().items():
        pinned[variable] = f"{tag}@{resolve_digest(tag)}"
        print(f"  {variable} = {pinned[variable]}")

    print("Compiling lock files")
    for service_dir, variable in LOCKED_SERVICES.items():
        compile_lock(REPO / service_dir, pinned[variable])

    lines = [
        "# Exact versions for HySite, made by scripts/refresh_versions.py. Do not edit by hand.",
        f"# Resolved {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC",
        *(f"{variable}={image}" for variable, image in pinned.items()),
        "REQUIREMENTS=requirements.lock",
    ]
    VERSIONS_FILE.write_text("\n".join(lines) + "\n")
    print(f"Wrote {VERSIONS_FILE.name}")


if __name__ == "__main__":
    main()
