#!/bin/bash
set -euo pipefail

echo "🔁 Reboot Validation: rlc-cloud-repos"

echo "📂 Checking marker file..."
if [[ ! -f /etc/rlc-cloud-repos/.configured ]]; then
    echo "❌ Marker file not found"
    exit 2
else
    echo "✅ Marker file exists"
fi

echo "📄 Validating DNF vars..."
missing_vars=0
for var in baseurl1 baseurl2 contentdir infra region rltype sigcontentdir; do
    if [[ ! -f "/etc/dnf/vars/$var" ]]; then
        echo "❌ Missing DNF var: $var"
        ((missing_vars++))
    else
        val=$(cat "/etc/dnf/vars/$var" 2>/dev/null | tr -d '\n')
        echo "✅ Found: /etc/dnf/vars/$var: \t$val"
    fi
done
[[ $missing_vars -eq 0 ]] || exit 3

echo "📑 Checking repo files..."
grep -q baseurl /etc/yum.repos.d/*.repo && echo "✅ Repo files contain baseurl" || {
    echo "❌ Repo file missing baseurl"
    exit 4
}

echo "🧾 Checking logs (journal)..."
if journalctl -b -t rlc-cloud-repos --no-pager | grep -q "rlc-cloud-repos"; then
    echo "✅ Syslog entries found via journal"
else
    echo "⚠️  No journalctl entries — checking /var/log/messages..."

    if sudo grep -q "rlc-cloud-repos" /var/log/messages; then
        echo "✅ Syslog entries found in /var/log/messages"
    else
        echo "❌ No syslog entries tagged rlc-cloud-repos"
        exit 5
    fi
fi

journalctl -b -t rlc-cloud-repos --no-pager 
sudo grep "rlc-cloud-repos" /var/log/messages

echo "🎉 Reboot test passed!"
