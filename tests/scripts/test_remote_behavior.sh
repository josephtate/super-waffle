#!/bin/bash

set -euo pipefail

echo "📦 Starting remote integration test..."

TOUCHFILE="/etc/rlc-cloud-repos/.configured"
REPOFILE="/etc/yum.repos.d/rlc-depot.repo"
SYSLOG_TAG="rlc-cloud-repos"

# Clean up from previous runs
echo "🧹 Cleaning up marker + repo file..."
sudo rm -f "$TOUCHFILE" "$REPOFILE"

# Run the tool with correct format
echo "🚀 Running rlc-cloud-repos CLI with --format repo..."
sudo rlc-cloud-repos --format repo --output "$REPOFILE"

echo "✅ CLI completed. Checking outcomes..."

# Check repo file
if [[ -f "$REPOFILE" ]]; then
    echo "✅ Repo file generated: $REPOFILE"
else
    echo "❌ Repo file missing!"
    exit 1
fi

# Check touchfile
if [[ -f "$TOUCHFILE" ]]; then
    echo "✅ Touchfile created: $TOUCHFILE"
else
    echo "❌ Touchfile missing!"
    exit 1
fi

# Check syslog entries (may not be available in container/minimal systems)
echo "🔍 Checking journal for syslog entries..."
if sudo journalctl -t "$SYSLOG_TAG" --since "5 minutes ago" | grep -q "rlc-cloud-repos"; then
    echo "✅ Syslog entry found for tag '$SYSLOG_TAG'"
    echo "🪵 Recent journal entries for rlc-cloud-repos:"
    journalctl -t rlc-cloud-repos -n 20 --no-pager
else
    echo "⚠️  No syslog entry found (may be expected in minimal systems)"
fi

echo "🎉 Remote integration test complete!"
