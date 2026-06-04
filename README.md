# Touch screen learning tool

A touchscreen-based cognitive training system built with PySide6/Qt. Designed for deployment on a Raspberry Pi.

## Quick install (Linux)

Clones the repo, sets up the virtual environment, and enables the systemd autostart service in one command:

```bash
bash <(curl -sSL https://raw.githubusercontent.com/VetMedUniViennaMesserli/Touchscreen/main/install.sh)
```

Run the same command again to update an existing installation.

## Running

Navigate to the installation directory and run the launcher script:

```bash
cd ~/Touchscreen
./touchscreen.sh
```

The script activates the virtual environment and starts whichever training is configured inside it. To change the active training, open `touchscreen.sh` and update the `APP=` line to point to a different training file, for example:

```bash
APP="App/Trainings/rule_learning.py"
```

To run a specific training directly without editing the script:

```bash
cd ~/Touchscreen
source venv/bin/activate
PYTHONPATH=App python App/Trainings/two_images.py
```

Press `Escape` or `Q` to quit any training.

## Manual installation

Clone the repo into your home directory (the systemd service expects it there):

```bash
cd ~
git clone https://github.com/VetMedUniViennaMesserli/Touchscreen.git Touchscreen
cd Touchscreen
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Building executables (optional)

```bash
bash build.sh
```

Standalone binaries are placed in `dist/`. Requires the venv to be set up first.

Session logs are written to `dist/SessionLogs/` when running a built binary.

## Deploy on Linux (systemd user service)

The quick install above handles this automatically. To set it up manually, the service expects the repo to be cloned at `~/Touchscreen`.

```bash
cp touchscreen.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable touchscreen.service
systemctl --user start touchscreen.service
```

> [!TIP]
> On Raspberry Pi, enable the "overlay filesystem" option to prevent SD card corruption.
> Session logs are written to `~/Touchscreen/SessionLogs/`. Collect them via network or USB stick.

To stop the service from starting automatically:

```bash
systemctl --user disable touchscreen.service
```

## Trainings

### Two images (`two_images.py`)

Two images are shown side by side — one from the **Paintings** category (correct) and one from the **Underwater** category (wrong). Their left/right position is randomised each trial. The subject must touch the painting. Feedback: success sound + inter-trial interval on correct; error sound + red screen on wrong.

Input: touchscreen.

---

### Two images — keyboard (`two_images_keyboard_input.py`)

Identical to Two images but responds to key presses instead of touch. Press **A** to select the left image, **D** to select the right image. Compatible with the Raspberry Pi Pico W hardware button box (`Devices/Keyboard/`).

Input: keyboard (A / D).

---

### Go / No-Go (`go_nogo.py`)

A single image is shown for up to **2 seconds**. The subject should touch it if it is a Painting (Go trial) and withhold if it is an Underwater image (No-Go trial). Not touching within the timeout counts as a correct No-Go response; touching a No-Go stimulus or not touching a Go stimulus counts as an error.

Input: touchscreen.

---

### Matching to sample (`matching_to_sample.py`)

A sample geometric shape is shown alone for **1 second**, then replaced by two choice shapes. The subject must touch the shape that matches the sample. Stimuli are drawn from `Training_Stimuli/Geometric_Shapes/`.

Input: touchscreen.

---

### Random position (`random_position.py`)

A single geometric shape is placed at a random position in a **5 × 4 grid**. The subject must touch it regardless of where it appears. Trains position-independent stimulus recognition.

Input: touchscreen.

---

### Sequential learning (`sequential_learning.py`)

Eight identical red circles are arranged in a U-shape across a **2 × 4 grid**. The subject must touch them in a fixed order (bottom row left-to-right, then top row right-to-left). Each correctly touched circle disappears; touching the wrong one triggers an error.

Input: touchscreen.

---

### Rule learning (`rule_learning.py`)

Two geometric shapes are shown side by side. The **background colour** signals which rule is currently active:

| Background | Rule | Correct stimulus |
|---|---|---|
| Light grey | Rule A | Stimulus with the **target colour** |
| Purple | Rule B | Stimulus with the **target shape** |

The experiment progresses through four phases — Rule A, Rule B, Alternating (blocked), Mixed (interleaved) — and only advances to the next phase when the session criterion is reached (≥ N/2 − 1 correct per trial type). Each session starts with 4 error-reduced trials (one stimulus hidden). Wrong choices trigger a correction trial (up to 5 attempts per trial).

Input: touchscreen or keyboard (A = left, D = right).

#### Setup dialog

Rule learning opens a full-screen setup dialog before each run. Scientists select a subject from a list and can adjust session parameters via large touch-friendly controls:

- **Subject** — select from the subject list
- **First rule** / **Background (Rule A)** / **Target stimulus (S+)** — counterbalancing settings pre-filled from `subjects.csv`, editable per run
- **Start at phase** — resume a subject from a specific phase (e.g. after criterion was reached in a previous session)
- **Trials / session** — 8 / 16 / 24 / 32

#### subjects.csv

On first launch, `subjects.csv` is created automatically next to the binary (or at the repo root when running via `touchscreen.sh`) with 10 pre-configured subjects and balanced counterbalancing. Scientists can open this file in any spreadsheet application to rename subjects, adjust counterbalancing, or add rows.

```
subject_id, first_rule, bg_rule_a, target_stim, notes
S01, RuleA, lightgrey, black triangle,
S02, RuleB, purple, white circle,
...
```

Session logs are stored in `SessionLogs/Rule_Learning_<subject_id>/` so each subject's data is automatically separated.
