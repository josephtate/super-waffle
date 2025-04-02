#!/bin/bash
# One-time wrapper for setting up CIQ cloud mirrors

MARKER="/etc/rlc-cloud-repos/.configured"
REPO_FILE="/etc/yum.repos.d/rlc-depot.repo"

if [ -f "$MARKER" ]; then
    echo "rlc-cloud-repos already configured, skipping."
    exit 0
fi

echo "Running rlc-cloud-repos setup..."
/usr/bin/rlc-cloud-repos --format repo --output "$REPO_FILE" && touch "$MARKER"