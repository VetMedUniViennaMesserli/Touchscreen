#!/usr/bin/env bash
# Touchscreen learning tool — updater
#
# Run this on an already-installed machine when told a new release is
# ready. It never asks which app to run — it keeps whatever install.sh
# originally selected — and it only ever moves to the newest release tag,
# never to unreleased commits on main.

set -euo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
SERVICE="touchscreen"

step() { echo ""; echo "[+] $*"; }
ok()   { echo "    ok"; }
fail() { echo ""; echo "[!] $*" >&2; exit 1; }

[ -d "$SCRIPT_DIR/.git" ] || fail "$SCRIPT_DIR is not an installed Touchscreen checkout. Run install.sh first."
[ -f "$SCRIPT_DIR/.selected_app" ] || fail "No .selected_app found — run install.sh first."

echo ""
echo "Touchscreen learning tool — update"
echo "==================================="

step "Checking for a newer release"
CURRENT="$(git -C "$SCRIPT_DIR" describe --tags --exact-match 2>/dev/null || git -C "$SCRIPT_DIR" rev-parse --short HEAD)"
git -C "$SCRIPT_DIR" fetch --quiet --tags
LATEST="$(git -C "$SCRIPT_DIR" tag -l 'v*' --sort=-v:refname | head -n1)"
[ -n "$LATEST" ] || fail "No release tags (v*) found in the repository."

if [ "$CURRENT" = "$LATEST" ]; then
    echo "    Already on the latest release: $LATEST"
    echo ""
    exit 0
fi

echo "    Current: $CURRENT"
echo "    Latest:  $LATEST"
ok

step "Checking out $LATEST"
REQS_CHANGED=1
if git -C "$SCRIPT_DIR" diff --quiet "$CURRENT" "$LATEST" -- requirements.txt 2>/dev/null; then
    REQS_CHANGED=0
fi
git -C "$SCRIPT_DIR" checkout --quiet "$LATEST"
ok

if [ "$REQS_CHANGED" = "1" ]; then
    step "requirements.txt changed — reinstalling dependencies"
    "$SCRIPT_DIR/venv/bin/pip" install --upgrade pip -q
    "$SCRIPT_DIR/venv/bin/pip" install -r "$SCRIPT_DIR/requirements.txt" -q
    ok
fi

step "Restarting service"
systemctl --user restart "$SERVICE.service"
ok

echo ""
echo "Done. Now running: $LATEST"
echo "  Selected app (unchanged): $(cat "$SCRIPT_DIR/.selected_app")"
echo ""
