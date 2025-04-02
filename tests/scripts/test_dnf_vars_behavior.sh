#!/bin/bash
set -euo pipefail

echo "🔬 Starting DNF vars integrity test..."

DNF_VARS_DIR="/etc/dnf/vars"
BACKUP_DIR="/tmp/dnf-vars-backup"
VARS=("baseurl1" "baseurl2" "region" "infra" "rltype" "contentdir" "sigcontentdir")

# Step 0: Prepare backup of any existing vars
echo "🧰 Backing up existing DNF vars (if any)..."
mkdir -p "$BACKUP_DIR"
for var in "${VARS[@]}"; do
    if [[ -f "$DNF_VARS_DIR/$var" ]]; then
        cp "$DNF_VARS_DIR/$var" "$BACKUP_DIR/$var.bak"
    fi
done

# Step 1: Run rlc-cloud-repos to regenerate vars
echo "🚀 Running rlc-cloud-repos to trigger DNF var setup..."
sudo rm -f "$DNF_VARS_DIR"/*  # simulate clean slate
sudo rlc-cloud-repos --format url > /tmp/dnf-vars.out

# Step 2: Verify vars were created
echo "🔍 Verifying that all expected DNF vars were created..."
MISSING_VARS=0
for var in "${VARS[@]}"; do
    if [[ -f "$DNF_VARS_DIR/$var" ]]; then
        echo "✅ $var found: $(cat "$DNF_VARS_DIR/$var")"
    else
        echo "❌ $var missing!"
        ((MISSING_VARS++))
    fi
done

# Step 3: Restore previous state (optional)
echo "🧼 Restoring original DNF vars (if any)..."
for var in "${DNF_VARS[@]}"; do
    backup="${BACKUP_DIR}/${var}"
    target="${DNF_VARS_DIR}/${var}"
    if [[ -f "$backup" ]]; then
        sudo cp "$backup" "$target"
    fi
done

echo "🎉 DNF var test complete. Missing count: $MISSING_VARS"
exit $MISSING_VARS
