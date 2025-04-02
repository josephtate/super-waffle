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
echo "🧪 Checking marker file state..."
if sudo test -f "$TOUCHFILE"; then
    echo "📌 Marker file exists, testing early exit logic..."
    sudo rm -f "$REPO_FILE"

    sudo $CLI --format repo > /tmp/cli.out || true
    if grep -q "Marker file exists" /tmp/cli.out; then
        echo "✅ CLI exited early as expected with marker present"
    else
        echo "❌ CLI did not exit early with marker present!"
        exit 1
    fi

    echo "🧹 Removing marker and re-testing full run..."
    sudo rm -f "$TOUCHFILE"
    sudo $CLI --format repo > /tmp/cli.out
    grep -q "Wrote repo" /tmp/cli.out && echo "✅ Repo rewritten after marker removal"
else
    echo "📎 Marker file not present; testing creation flow..."
    
    echo "📥 Creating marker manually..."
    sudo touch "$TOUCHFILE"
    sudo rm -f "$REPO_FILE"

    sudo $CLI --format repo > /tmp/cli.out || true
    grep -q "Marker file exists" /tmp/cli.out && echo "✅ CLI respected manual marker"

    echo "🧹 Removing marker to run clean config..."
    sudo rm -f "$TOUCHFILE"
    sudo $CLI --format repo > /tmp/cli.out
    grep -q "Wrote repo" /tmp/cli.out && echo "✅ CLI created repo on clean run"
fi

echo "🧼 Restoring test state (removing marker + repo file)..."
sudo rm -f "$TOUCHFILE" "$REPO_FILE"

echo "🎉 Remote marker file tests complete!"

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
