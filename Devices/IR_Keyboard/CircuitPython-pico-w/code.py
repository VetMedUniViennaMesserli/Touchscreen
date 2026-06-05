import board
import digitalio
import time
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

kbd = Keyboard(usb_hid.devices)

# IR sensor OUT pins (sensor drives LOW when obstacle is detected)
IR_A_PIN = board.GP14   # left sensor  → sends A
IR_D_PIN = board.GP15   # right sensor → sends D

ir_a = digitalio.DigitalInOut(IR_A_PIN)
ir_a.direction = digitalio.Direction.INPUT
ir_a.pull = digitalio.Pull.UP   # ensures HIGH when sensor output is open/floating

ir_d = digitalio.DigitalInOut(IR_D_PIN)
ir_d.direction = digitalio.Direction.INPUT
ir_d.pull = digitalio.Pull.UP

# Minimum time (seconds) before the same sensor can trigger again.
# Prevents double-firing if the obstacle lingers in the beam.
RETRIGGER_DELAY = 0.3

# Initialise from actual sensor state so nothing fires on boot,
# even if an obstacle is already in the beam at startup.
last_a_detected = not ir_a.value
last_d_detected = not ir_d.value
last_a_time = 0.0
last_d_time = 0.0

while True:
    now = time.monotonic()

    a_detected = not ir_a.value   # True when obstacle present (LOW output)
    d_detected = not ir_d.value

    # Send on rising edge only (clear → detected), with retrigger guard
    if a_detected and not last_a_detected and (now - last_a_time) >= RETRIGGER_DELAY:
        kbd.send(Keycode.A)
        print("A sent")
        last_a_time = now

    if d_detected and not last_d_detected and (now - last_d_time) >= RETRIGGER_DELAY:
        kbd.send(Keycode.D)
        print("D sent")
        last_d_time = now

    last_a_detected = a_detected
    last_d_detected = d_detected

    time.sleep(0.01)
