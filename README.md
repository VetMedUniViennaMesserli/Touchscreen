# Touch screen learning tool

A touchscreen-based cognitive training system built with PySide6/Qt. Designed for deployment on a Raspberry Pi with a touchscreen and optionally a second monitor.

## Quick install / uninstall (Linux)

Clones the repo, sets up the virtual environment, and enables the systemd autostart service in one command:

```bash
bash <(curl -sSL https://raw.githubusercontent.com/VetMedUniViennaMesserli/Touchscreen/main/install.sh)
```

The script asks whether to **Install / Update** or **Uninstall** each time it runs. Run the same command again to update or to remove the installation completely.

## Running

Navigate to the installation directory and run the launcher script:

```bash
cd ~/Touchscreen
./touchscreen.sh
```

The script reads the active training from `.selected_app` (written by the installer). To change it without re-running the installer, edit that file directly:

```bash
echo "App/Trainings/rule_learning.py" > ~/Touchscreen/.selected_app
```

To run a specific training directly without changing the configuration:

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

## Building executables (optional)

```bash
bash build.sh
```

Standalone binaries are placed in `dist/`. Requires the venv to be set up first.

Session logs are written to `dist/SessionLogs/` when running a built binary.

## Trainings

### Two images (`two_images.py`)

Two images are shown side by side — one from the **Paintings** category (correct) and one from the **Underwater** category (wrong). Their left/right position is randomised each trial. The individual must touch the painting. Feedback: success sound + inter-trial interval on correct; error sound + red screen on wrong.

Input: touchscreen.

---

### Two images — keyboard (`two_images_keyboard_input.py`)

Identical to Two images but responds to key presses instead of touch. Press **A** to select the left image, **D** to select the right image. Compatible with the Raspberry Pi Pico W hardware button box (`Devices/Keyboard/`).

Input: keyboard (A / D).

---

### Go / No-Go (`go_nogo.py`)

A single image is shown for up to **2 seconds**. The individual should touch it if it is a Painting (Go trial) and withhold if it is an Underwater image (No-Go trial). Not touching within the timeout counts as a correct No-Go response; touching a No-Go stimulus or not touching a Go stimulus counts as an error.

Input: touchscreen.

---

### Matching to sample (`matching_to_sample.py`)

A sample geometric shape is shown alone for **1 second**, then replaced by two choice shapes. The individual must touch the shape that matches the sample. Stimuli are drawn from `Training_Stimuli/Geometric_Shapes/`.

Input: touchscreen.

---

### Random position (`random_position.py`)

A single geometric shape is placed at a random position in a **5 × 4 grid**. The individual must touch it regardless of where it appears. Trains position-independent stimulus recognition.

Input: touchscreen.

---

### Sequential learning (`sequential_learning.py`)

Eight identical red circles are arranged in a U-shape across a **2 × 4 grid**. The individual must touch them in a fixed order (bottom row left-to-right, then top row right-to-left). Each correctly touched circle disappears; touching the wrong one triggers an error.

Input: touchscreen.

---

### Rule learning (`rule_learning.py`)

Two geometric shapes are shown side by side on the **task screen** (primary monitor). The **background** signals which rule is currently active:

| Background | Rule | Correct stimulus |
|---|---|---|
| Light grey | Rule A | Stimulus with the **target colour** |
| Diagonal grey stripes | Rule B | Stimulus with the **target shape** |

The setup dialog and session-end screen are always shown on the **secondary monitor** (if connected), so the subject cannot interact with control options. If only one monitor is present, everything appears on the same screen.

Input: touchscreen or keyboard (**A** = left, **D** = right).

---

#### Phases

The experiment runs through seven phases in order. Each phase repeats sessions until the criterion is met, then advances automatically.

| # | Phase | Stimuli | Criterion to advance |
|---|---|---|---|
| 1 | **Pre-Training** | White cross on black — one side only | ≥ 10 / 12 correct in **2 consecutive sessions** |
| 2 | **Rule A** (or B first, depending on counterbalance) | Training colours & shapes | ≥ N/2 − 1 correct for each trial type |
| 3 | **Rule B** (or A) | Training colours & shapes | ≥ N/2 − 1 correct for each trial type |
| 4 | **Alternate** | Training colours & shapes — rules blocked (half A, half B) | ≥ N/2 − 1 correct for each trial type |
| 5 | **Mixed** | Training colours & shapes — rules interleaved | ≥ N/2 − 1 correct for each trial type |
| 6 | **Alternating Transfer** | Novel colours (blue/yellow) and shapes (star/square) — rules blocked | ≥ N/2 − 1 correct for each trial type |
| 7 | **Mixed Transfer** | Novel colours and shapes — rules interleaved | ≥ N/2 − 1 correct for each trial type |

**Training stimuli** (phases 2–5): the target colour and shape configured per individual (e.g. black triangle / white circle).  
**Transfer stimuli** (phases 6–7): novel blue/yellow colours and star/square shapes. Background rules (which bg = which rule) remain unchanged.

---

#### Trial structure

**Error-reduced (ER) trials — first 4 trials of every non-Pre-Training session**

Only one stimulus is shown (the common S+, i.e. the stimulus that satisfies both rules). The other side is blank. This makes the correct choice obvious and gives the subject a successful start to each session.

- In training phases the ER trials use the **rule background** of the first trial in that session.
- In transfer phases the ER trials use a **black background** so the new stimulus stands out clearly.
- A wrong choice (or timeout) during an ER trial shows a **red screen** and repeats the same ER trial (correction trial). These correction attempts are **not recorded** in the session log.

**Regular trials (trials 5 onward)**

Both stimuli are shown. The subject must choose the correct one according to the active rule signalled by the background.

- The first regular trial of every Alternate or Mixed session is always a **type-1 trial** — the common S+ is present, making the required rule unambiguous.
- **Alternate** sessions: no two consecutive trials have the same stimulus layout; the S+ side changes at least every 3rd trial; the two rules are presented in two equal blocks (first rule first, matching the individual's counterbalance setting).
- **Mixed** sessions: no more than 3 consecutive trials of the same rule.
- A wrong choice triggers a **red screen** (800 ms) followed by a correction trial (same trial repeated). Up to 5 correction attempts per trial. Correction trials are recorded in the log with `correction_trial > 0`.
- A correct choice triggers a **success sound** and the next trial appears immediately (no green feedback screen).
- No response within **3 minutes** triggers a **yellow timeout screen** followed by a correction trial.

**Pre-Training trials**

All 12 trials per session show only a white cross on a black background, visible on one side at a time. Positioning is semirandom — no more than 2 consecutive trials on the same side. Criterion: 10 or more correct in 2 consecutive sessions.

---

#### Session-end screen

After every session a results screen is shown on the secondary monitor displaying the score, whether the criterion was met, and what happens next. Two buttons are available:

- **Continue / Repeat** — proceeds to the next session or phase.
- **Exit** — ends the experiment and returns to the start menu.

---

#### Setup dialog

Rule learning opens a full-screen setup dialog on the secondary monitor before each run. Scientists select an individual from the grid and can review or adjust parameters:

- **Individual** — select from the individual list
- **First rule** — which rule is trained first (RuleA or RuleB)
- **Background (Rule A)** — lightgrey or striped (determines which background maps to which rule)
- **Target stimulus (S+)** — the training target (e.g. `black triangle`)
- **Transfer target (S+)** — the transfer test target (e.g. `blue star`)
- **Start at phase** — resume from a specific phase (e.g. after criterion was already reached in a previous session)
- **Trials / session** — 8 / 16 / 24 / 32

---

#### individuals.csv

On first launch, `individuals.csv` is created automatically next to the binary (or at the repo root when running via `touchscreen.sh`) with 10 pre-configured individuals and balanced counterbalancing. Scientists can open this file in any spreadsheet application to rename individuals, adjust counterbalancing, or add rows.

```
individual_id, first_rule, bg_rule_a, target_stim, transfer_stim, notes
S01, RuleA, lightgrey, black triangle, blue star,
S02, RuleB, striped,   white circle,   yellow square,
...
```

Column reference:

| Column | Values | Meaning |
|---|---|---|
| `individual_id` | any string | Shown in setup dialog and used in log file names |
| `first_rule` | `RuleA` / `RuleB` | Which rule is trained first |
| `bg_rule_a` | `lightgrey` / `striped` | Background colour assigned to Rule A |
| `target_stim` | e.g. `black triangle` | Colour + shape of the training S+ |
| `transfer_stim` | e.g. `blue star` | Colour + shape of the transfer S+ |
| `notes` | any string | Free text, not used by the software |

---

#### Session logs

Each run creates a new CSV file:

```
SessionLogs/Rule_Learning_<individual_id>/Rule_Learning_<individual_id>_<date>_<time>.csv
```

One row per regular trial (ER correction trials are not logged). Columns:

| Column | Description |
|---|---|
| `subjectID` | Individual identifier |
| `date` | `yyyy-mm-dd` |
| `time` | `hh:mm:ss` |
| `phase` | Phase name (`PreTraining`, `RuleA`, `RuleB`, `Alternate`, `Mixed`, `AlternatingTransfer`, `MixedTransfer`) |
| `phase_count` | Index of this phase in the full sequence (1-based; not always the same number for RuleA/B due to counterbalancing) |
| `session_count` | Session number within the current phase |
| `trial_count` | Trial number within the session (starts at 1; correction trials do not increment this) |
| `target_color` | Target colour according to Rule A |
| `target_shape` | Target shape according to Rule B |
| `bg_shown` | Background on this trial: `grey` or `striped` |
| `rule` | Which rule was active: `RuleA` or `RuleB` |
| `left_shape` | Shape shown on the left |
| `left_color` | Colour of the left stimulus |
| `right_shape` | Shape shown on the right |
| `right_color` | Colour of the right stimulus |
| `commonSp` | The common S+ for this phase, e.g. `black triangle` |
| `left_stim` | `<color> <shape>` of left stimulus |
| `right_stim` | `<color> <shape>` of right stimulus |
| `trial_type` | `0` = errorless/pre-training, `1` = common S+ present, `2` = common S+ absent |
| `target_side` | `left` or `right` — where the correct stimulus was |
| `choice_side` | `left`, `right`, or `NA` (timeout) |
| `reward_score` | `1` if correct, `0` otherwise |
| `choice_shape` | Shape of the chosen stimulus (`NA` on timeout) |
| `choice_color` | Colour of the chosen stimulus (`NA` on timeout) |
| `choice_latency` | Seconds from trial onset to response |
| `correction_trial` | `0` on a first attempt; counts upward for each correction attempt |
