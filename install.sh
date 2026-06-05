#!/usr/bin/env bash
# Touchscreen learning tool — installer / uninstaller
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

echo ""
echo "Touchscreen learning tool"
echo "========================="

# ── action ────────────────────────────────────────────────────────────────────

echo ""
echo "  1) Install / Update"
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

# ── checks (install / update only) ───────────────────────────────────────────

[[ "$OSTYPE" == linux* ]] || fail "This installer targets Linux only."

command -v git     >/dev/null 2>&1 || fail "git not found.    Run: sudo apt-get install git"
command -v python3 >/dev/null 2>&1 || fail "python3 not found. Run: sudo apt-get install python3"

# ── clone / update ────────────────────────────────────────────────────────────

IS_UPDATE=false
step "Repository"
if [ -d "$INSTALL_DIR/.git" ]; then
    IS_UPDATE=true
    echo "    Existing installation found — pulling latest changes"
    git -C "$INSTALL_DIR" pull --ff-only
else
    echo "    Cloning into $INSTALL_DIR"
    git clone "$REPO_URL" "$INSTALL_DIR"
fi
ok

# ── app selection ─────────────────────────────────────────────────────────────

CONFIG_FILE="$INSTALL_DIR/.selected_app"

if $IS_UPDATE && [ -f "$CONFIG_FILE" ]; then
    echo ""
    echo "[i] Update — keeping existing app selection: $(cat "$CONFIG_FILE")"
else
    step "Select training app"
    echo "    Which training should run at startup?"
    echo ""
    echo "    1) Two images            (touchscreen)"
    echo "    2) Two images            (keyboard)"
    echo "    3) Go / No-Go"
    echo "    4) Matching to sample"
    echo "    5) Random position"
    echo "    6) Sequential learning"
    echo "    7) Rule learning"
    echo ""
    read -rp "    Enter number [7]: " choice
    choice="${choice:-7}"
    case "$choice" in
        1) SELECTED="App/Trainings/two_images.py" ;;
        2) SELECTED="App/Trainings/two_images_keyboard_input.py" ;;
        3) SELECTED="App/Trainings/go_nogo.py" ;;
        4) SELECTED="App/Trainings/matching_to_sample.py" ;;
        5) SELECTED="App/Trainings/random_position.py" ;;
        6) SELECTED="App/Trainings/sequential_learning.py" ;;
        *) SELECTED="App/Trainings/rule_learning.py" ;;
    esac
    echo "$SELECTED" > "$CONFIG_FILE"
    echo "    Selected: $SELECTED"
    ok
fi

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
echo "    $INSTALL_DIR/.selected_app"
echo ""
