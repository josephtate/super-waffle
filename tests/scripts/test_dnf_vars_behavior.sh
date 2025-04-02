#!/bin/bash

set -euo pipefail
echo "🔬 Starting DNF vars integrity test..."

DNF_VAR_DIR="/etc/dnf/vars"
CLI="rlc-cloud-repos"
MISSING=0

echo "🧰 Backing up existing DNF vars (if any)..."
declare -A ORIGINAL_VARS
mkdir -p /tmp/dnf-backup

for var in baseurl1 baseurl2 region infra rltype contentdir sigcontentdir; do
    path="$DNF_VAR_DIR/$var"
    if [[ -f "$path" ]]; then
        sudo cp "$path" "/tmp/dnf-backup/$var"
        ORIGINAL_VARS["$var"]="yes"
    else
        ORIGINAL_VARS["$var"]="no"
    fi
done

echo "🧹 Removing DNF vars to simulate fresh run..."
sudo rm -f "$DNF_VAR_DIR"/* || true

echo "🚀 Running $CLI with --force to trigger DNF var setup..."
sudo $CLI --force --format url > /dev/null

echo "🔍 Verifying that all expected DNF vars were created..."
for var in baseurl1 baseurl2 region infra rltype contentdir sigcontentdir; do
    val=$(sudo cat "$DNF_VAR_DIR/$var" 2>/dev/null | tr -d '\n')
    if [[ -n "$val" ]]; then
        echo "✅ $var found: $val"
    else
        echo "❌ $var missing or empty!"
        ((MISSING+=1))
    fi
done

echo "🧼 Restoring original DNF vars (if any)..."
for var in baseurl1 baseurl2 region infra rltype contentdir sigcontentdir; do
    if [[ "${ORIGINAL_VARS[$var]}" == "yes" ]]; then
        sudo cp "/tmp/dnf-backup/$var" "$DNF_VAR_DIR/$var"
    else
        sudo rm -f "$DNF_VAR_DIR/$var"
    fi
done

echo "🎉 DNF var test complete. Missing count: $MISSING"
exit $MISSING