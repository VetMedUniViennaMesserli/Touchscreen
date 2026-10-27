#!/usr/bin/env bash
# Make the InfraredMultiTouch-61 IR touchscreen (USB 08d3:1000) behave like a
# plain mouse: one touch = move + left click/drag, no multitouch gestures.
#
# How: a small background service (touch-to-mouse) grabs the touchscreen,
# keeps only the first touch point and re-emits it as a virtual absolute mouse.
# The desktop never sees multitouch, so no gestures. The screen's own "Mouse"
# interface can't be used: it goes silent once Linux enables multitouch mode.
#
# Usage:
#   sudo ./touchscreen-single-touch.sh            # install
#   sudo ./touchscreen-single-touch.sh uninstall  # restore normal multitouch
#   ./touchscreen-single-touch.sh status          # show current state

set -euo pipefail

VENDOR="08d3"
PRODUCT="1000"
RULE_FILE="/etc/udev/rules.d/99-touchscreen-single-touch.rules"
DAEMON="/usr/local/bin/touch-to-mouse.py"
SERVICE="touch-to-mouse.service"
SERVICE_FILE="/etc/systemd/system/$SERVICE"

need_root() {
    if [[ $EUID -ne 0 ]]; then
        echo "This needs root. Run: sudo $0 ${1:-}" >&2
        exit 1
    fi
}

reload_udev() {
    udevadm control --reload
    udevadm trigger --subsystem-match=input --action=change
    udevadm settle
}

status() {
    echo "Udev rule: $([[ -f $RULE_FILE ]] && echo installed || echo "not installed")"
    echo "Service:   $(systemctl is-active "$SERVICE" 2>/dev/null || true)"
    local found=0
    for dev in /sys/class/input/event*; do
        local ev; ev=$(basename "$dev")
        local props; props=$(udevadm info --query=property "/dev/input/$ev" 2>/dev/null) || continue
        local name; name=$(cat "$dev/device/name" 2>/dev/null)
        if [[ $name == "Touchscreen single-touch mouse" ]]; then
            printf '  %-8s %-26s %-8s %s\n' "$ev" "virtual mouse" "active" "$name"
            continue
        fi
        grep -q "^ID_VENDOR_ID=$VENDOR$" <<<"$props" || continue
        grep -q "^ID_MODEL_ID=$PRODUCT$" <<<"$props" || continue
        found=1
        local kind="other"
        grep -q '^ID_INPUT_TOUCHSCREEN=1' <<<"$props" && kind="touchscreen (multitouch)"
        grep -q '^ID_INPUT_MOUSE=1' <<<"$props" && kind="mouse interface"
        grep -q '^ID_INPUT_KEYBOARD=1' <<<"$props" && kind="keyboard"
        local state="active"
        grep -q '^LIBINPUT_IGNORE_DEVICE=1' <<<"$props" && state="IGNORED"
        printf '  %-8s %-26s %-8s %s\n' "$ev" "$kind" "$state" "$name"
    done
    [[ $found -eq 1 ]] || echo "  Touchscreen $VENDOR:$PRODUCT not detected (is it plugged in?)"
}

install_all() {
    need_root install

    if ! python3 -c "import evdev" 2>/dev/null; then
        echo "Installing python3-evdev..."
        apt-get install -y python3-evdev
    fi

    cat > "$DAEMON" <<EOF
#!/usr/bin/env python3
# Grab the multitouch screen and re-emit only the first touch as an absolute mouse.
import time
import evdev
from evdev import ecodes as e, AbsInfo, UInput

VENDOR, PRODUCT = 0x$VENDOR, 0x$PRODUCT
NAME = "Touchscreen single-touch mouse"


def find_touchscreen():
    for path in evdev.list_devices():
        dev = evdev.InputDevice(path)
        abs_codes = [code for code, _ in dev.capabilities().get(e.EV_ABS, [])]
        if (dev.info.vendor, dev.info.product) == (VENDOR, PRODUCT) and e.ABS_MT_POSITION_X in abs_codes:
            return dev
        dev.close()
    return None


def run(dev):
    ax, ay = dev.absinfo(e.ABS_X), dev.absinfo(e.ABS_Y)
    caps = {
        e.EV_KEY: [e.BTN_LEFT, e.BTN_RIGHT, e.BTN_MIDDLE],
        e.EV_ABS: [
            (e.ABS_X, AbsInfo(0, ax.min, ax.max, 0, 0, ax.resolution)),
            (e.ABS_Y, AbsInfo(0, ay.min, ay.max, 0, 0, ay.resolution)),
        ],
    }
    with UInput(caps, name=NAME, bustype=e.BUS_USB) as ui:
        dev.grab()
        print(f"Grabbed {dev.path} ({dev.name})", flush=True)
        pos, button = {}, None
        for ev in dev.read_loop():
            if ev.type == e.EV_ABS and ev.code in (e.ABS_X, e.ABS_Y):
                pos[ev.code] = ev.value
            elif ev.type == e.EV_KEY and ev.code == e.BTN_TOUCH:
                button = ev.value
            elif ev.type == e.EV_SYN and ev.code == e.SYN_REPORT:
                # Move first, then press/release, so clicks land where the finger is
                for code, value in pos.items():
                    ui.write(e.EV_ABS, code, value)
                if pos:
                    ui.syn()
                if button is not None:
                    ui.write(e.EV_KEY, e.BTN_LEFT, button)
                    ui.syn()
                pos, button = {}, None


while True:
    dev = find_touchscreen()
    if dev is None:
        time.sleep(2)
        continue
    try:
        run(dev)
    except OSError as err:
        print(f"Touchscreen lost ({err}), waiting for it to come back", flush=True)
    finally:
        dev.close()
    time.sleep(1)
EOF
    chmod 755 "$DAEMON"
    echo "Wrote $DAEMON"

    cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=IR touchscreen as single-touch mouse
After=systemd-udevd.service

[Service]
ExecStart=/usr/bin/python3 $DAEMON
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
EOF
    echo "Wrote $SERVICE_FILE"

    # The desktop must not use the raw touchscreen or the (silent) mouse interface
    cat > "$RULE_FILE" <<EOF
# InfraredMultiTouch-61 ($VENDOR:$PRODUCT): handled by $SERVICE instead
ACTION=="add|change", SUBSYSTEM=="input", KERNEL=="event*", ATTRS{idVendor}=="$VENDOR", ATTRS{idProduct}=="$PRODUCT", ENV{ID_INPUT_TOUCHSCREEN}=="1", ENV{LIBINPUT_IGNORE_DEVICE}="1"
ACTION=="add|change", SUBSYSTEM=="input", KERNEL=="event*", ATTRS{idVendor}=="$VENDOR", ATTRS{idProduct}=="$PRODUCT", ENV{ID_INPUT_MOUSE}=="1", ENV{LIBINPUT_IGNORE_DEVICE}="1"
EOF
    echo "Wrote $RULE_FILE"
    reload_udev

    systemctl daemon-reload
    systemctl enable "$SERVICE"
    systemctl restart "$SERVICE"
    sleep 2
    status
    echo
    echo "Done. Touch the screen: it should now act like a mouse."
    echo "Log: journalctl -u $SERVICE -f"
}

uninstall_all() {
    need_root uninstall
    systemctl disable --now "$SERVICE" 2>/dev/null || true
    rm -f "$SERVICE_FILE" "$DAEMON" "$RULE_FILE"
    systemctl daemon-reload
    reload_udev
    echo "Removed service, daemon and udev rule."
    status
    echo
    echo "Multitouch restored. If touch doesn't respond, unplug and replug the touchscreen."
}

case "${1:-install}" in
    install)   install_all ;;
    uninstall) uninstall_all ;;
    status)    status ;;
    *) echo "Usage: $0 [install|uninstall|status]" >&2; exit 1 ;;
esac
