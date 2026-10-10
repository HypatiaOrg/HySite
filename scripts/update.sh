#!/bin/bash
# Run the HySite update job now (normally weekly, by hysite-update.timer) and follow its log.
# The job tests the newest versions and deploys them only if the tests pass; see scripts/hysite_update.sh.
sudo systemctl start --no-block hysite-update.service || exit
journalctl --unit hysite-update.service --follow --since now --output cat &
journal=$!
while systemctl is-active --quiet hysite-update.service \
        || [ "$(systemctl show --property ActiveState --value hysite-update.service)" = activating ]; do
    sleep 5
done
kill "$journal"
systemctl status hysite-update.service --no-pager --lines 0
