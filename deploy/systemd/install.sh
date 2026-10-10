#!/bin/bash
# Install or update the HySite update job's systemd units. Run on the server with sudo:
#   sudo deploy/systemd/install.sh
set -euo pipefail
cd "$(dirname "$0")"
[ -f /etc/hysite/update.env ] || {
    echo "First create /etc/hysite/update.env from deploy/systemd/update.env.example"; exit 1; }
install --mode 644 hysite-update.service hysite-update.timer hysite-alert@.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now hysite-update.timer
systemctl list-timers hysite-update.timer
