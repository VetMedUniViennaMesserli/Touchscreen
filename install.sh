#!/usr/bin/env bash
# Touchscreen learning tool — first-time installer / uninstaller
#
# For updating an existing installation, use update.sh instead — this
# script always re-prompts for which app to run, which update.sh does not.
#
# Usage:
#   bash <(curl -sSL https://raw.githubusercontent.com/VetMedUniViennaMesserli/Touchscreen/main/install.sh)

set -euo pipefail

REPO_URL="https://github.com/VetMedUniViennaMesserli/Touchscreen.git"
INSTALL_DIR="$HOME/Touchscreen"
SERVICE="touchscreen"

# ── helpers ───────────────────────────────────────────────────────────────────

step() { echo ""; echo "[+] $*"; }
ok()   { echo "    ok"; }
fail() { echo ""; echo "[!] $*" >&2; exit 1; }

latest_tag() {
    git -C "$INSTALL_DIR" tag -l 'v*' --sort=-v:refname | head -n1
}

echo ""
echo "Touchscreen learning tool"
echo "========================="

# ── action ────────────────────────────────────────────────────────────────────

echo ""
echo "  1) Install"
echo "  2) Uninstall"
echo ""
read -rp "  Choose [1]: " action
action="${action:-1}"

# ── uninstall ─────────────────────────────────────────────────────────────────

if [ "$action" = "2" ]; then
    step "Stopping and disabling service"
    systemctl --user stop    "$SERVICE.service" 2>/dev/null || true
    systemctl --user disable "$SERVICE.service" 2>/dev/null || true
    rm -f "$HOME/.config/systemd/user/$SERVICE.service"
    systemctl --user daemon-reload 2>/dev/null || true
    ok

    step "Removing files"
    if [ -d "$INSTALL_DIR" ]; then
        rm -rf "$INSTALL_DIR"
        echo "    Removed $INSTALL_DIR"
    else
        echo "    $INSTALL_DIR not found — nothing to remove"
    fi
    ok

    echo ""
    echo "Done. Touchscreen has been uninstalled."
    echo ""
    exit 0
fi

# ── checks ────────────────────────────────────────────────────────────────────

[[ "$OSTYPE" == linux* ]] || fail "This installer targets Linux only."

command -v git     >/dev/null 2>&1 || fail "git not found.    Run: sudo apt-get install git"
command -v python3 >/dev/null 2>&1 || fail "python3 not found. Run: sudo apt-get install python3"

# ── clone + pin to latest release tag ────────────────────────────────────────

step "Repository"
if [ -d "$INSTALL_DIR/.git" ]; then
    fail "An installation already exists at $INSTALL_DIR — use update.sh to update it, or choose 'Uninstall' first."
fi
echo "    Cloning into $INSTALL_DIR"
git clone --quiet "$REPO_URL" "$INSTALL_DIR"

TAG="$(latest_tag)"
[ -n "$TAG" ] || fail "No release tags (v*) found in the repository."
git -C "$INSTALL_DIR" checkout --quiet "$TAG"
echo "    Checked out release: $TAG"
ok

# ── app selection ─────────────────────────────────────────────────────────────

CONFIG_FILE="$INSTALL_DIR/.selected_app"

step "Select app to run"
echo "    Which app should run on this machine?"
echo ""

mapfile -t APP_DIRS < <(find "$INSTALL_DIR/Apps" -mindepth 1 -maxdepth 1 -type d | sort)
[ "${#APP_DIRS[@]}" -gt 0 ] || fail "No apps found under Apps/."

for i in "${!APP_DIRS[@]}"; do
    printf "    %d) %s\n" "$((i+1))" "$(basename "${APP_DIRS[$i]}")"
done
echo ""
read -rp "    Enter number [1]: " choice
choice="${choice:-1}"

idx=$((choice-1))
[ "$idx" -ge 0 ] && [ "$idx" -lt "${#APP_DIRS[@]}" ] || fail "Invalid choice: $choice"
APP_DIR="${APP_DIRS[$idx]}"

ENTRY="$(find "$APP_DIR" -maxdepth 1 -name '*.py' | sort | head -n1)"
[ -n "$ENTRY" ] || fail "No .py entry point found in $APP_DIR"
SELECTED="${ENTRY#"$INSTALL_DIR"/}"

echo "$SELECTED" > "$CONFIG_FILE"
echo "    Selected: $SELECTED"
ok

# ── python venv ───────────────────────────────────────────────────────────────

step "Python virtual environment"
if ! python3 -c "import venv" 2>/dev/null; then
    echo "    python3-venv not found — installing"
    sudo apt-get install -y python3-venv
fi
if [ ! -d "$INSTALL_DIR/venv" ]; then
    python3 -m venv "$INSTALL_DIR/venv"
fi
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip -q
"$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt" -q
ok

# ── systemd user service ──────────────────────────────────────────────────────

step "Systemd user service"
mkdir -p "$HOME/.config/systemd/user"
cp "$INSTALL_DIR/touchscreen.service" "$HOME/.config/systemd/user/"
systemctl --user daemon-reload
systemctl --user enable "$SERVICE.service"
systemctl --user start  "$SERVICE.service"
# Allow the service to start at boot without an active login session
loginctl enable-linger "$USER" 2>/dev/null || true
ok

# ── done ──────────────────────────────────────────────────────────────────────

echo ""
echo "Done."
echo ""
echo "  Installed at : $INSTALL_DIR"
echo "  Release      : $TAG"
echo "  Service      : systemctl --user status $SERVICE"
echo "  Logs         : $INSTALL_DIR/SessionLogs/"
echo ""
echo "  To update later, run update.sh from within $INSTALL_DIR (or re-fetch"
echo "  it from GitHub) — it pulls the newest release tag without re-asking"
echo "  which app to run."
echo ""
