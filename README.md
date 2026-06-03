# Touch screen learning tool

A touchscreen-based cognitive training system built with PySide6/Qt. Designed for deployment on a Raspberry Pi.

## Installation

Clone the repo into your home directory (the systemd service expects it there):

```bash
cd ~
git clone <repo_url> Touchscreen
cd Touchscreen
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running

```bash
./touchscreen.sh
```

To run a specific training directly:

```bash
source venv/bin/activate
PYTHONPATH=App python App/Trainings/two_images.py
```

Edit `touchscreen.sh` to select which training to run. Available trainings:

| File | Task |
|---|---|
| `two_images.py` | Two-alternative forced choice (touchscreen) |
| `two_images_keyboard_input.py` | Two-alternative forced choice (keyboard: A / D) |
| `go_nogo.py` | Go / No-Go |
| `matching_to_sample.py` | Matching to sample |
| `random_position.py` | Random position |
| `sequential_learning.py` | Sequential learning |

Press `Escape` or `Q` to quit.

## Building executables (optional)

```bash
bash build.sh
```

Standalone binaries are placed in `dist/`. Requires the venv to be set up first.

Session logs are written to `dist/SessionLogs/` when running a built binary.

## Deploy on Linux (systemd user service)

The service expects the repo to be cloned at `~/Touchscreen`.

```bash
cp touchscreen.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable touchscreen.service
systemctl --user start touchscreen.service
```

> [!TIP]
> On Raspberry Pi, enable the "overlay filesystem" option to prevent SD card corruption.
> Session logs are written to `~/Touchscreen/SessionLogs/`. Collect them via network or USB stick.
