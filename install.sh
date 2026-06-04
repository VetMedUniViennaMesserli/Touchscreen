#!/usr/bin/env bash
# Touchscreen learning tool — one-line installer
# Usage:
#   bash <(curl -sSL https://raw.githubusercontent.com/VetMedUniViennaMesserli/Touchscreen/main/install.sh)
# To update an existing installation, run the same command again.

set -euo pipefail

REPO_URL="https://github.com/VetMedUniViennaMesserli/Touchscreen.git"
INSTALL_DIR="$HOME/Touchscreen"
SERVICE="touchscreen"

# ── helpers ───────────────────────────────────────────────────────────────────

step() { echo ""; echo "[+] $*"; }
ok()   { echo "    ok"; }
fail() { echo ""; echo "[!] $*" >&2; exit 1; }

echo ""
echo "Touchscreen learning tool — installer"
echo "======================================"

# ── checks ────────────────────────────────────────────────────────────────────

[[ "$OSTYPE" == linux* ]] || fail "This installer targets Linux only."

command -v git    >/dev/null 2>&1 || fail "git not found.    Run: sudo apt-get install git"
command -v python3 >/dev/null 2>&1 || fail "python3 not found. Run: sudo apt-get install python3"

# ── clone / update ────────────────────────────────────────────────────────────

step "Repository"
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "    Existing installation found — pulling latest changes"
    git -C "$INSTALL_DIR" pull --ff-only
else
    echo "    Cloning into $INSTALL_DIR"
    git clone "$REPO_URL" "$INSTALL_DIR"
fi
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
echo "  Service      : systemctl --user status $SERVICE"
echo "  Logs         : $INSTALL_DIR/SessionLogs/"
echo ""
echo "  To change which training runs, edit:"
echo "    $INSTALL_DIR/touchscreen.sh"
echo ""
