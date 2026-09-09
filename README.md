# Touch screen learning tool

A touchscreen-based cognitive training framework built with PySide6/Qt. Designed for deployment on a Raspberry Pi (or any Linux PC) with a touchscreen and optionally a second monitor — one app per machine, e.g. one PC running Rule Learning at a pig facility, another running a different app at a bird facility.

The repo is a monorepo with three top-level parts:

- **`Framework/`** — the shared engine (window management, session logging, trial timing, ...) that every app is built on.
- **`Apps/`** — real, deployable, versioned research apps (currently: `RuleLearning`). This is what `install.sh`'s app picker offers.
- **`Examples/`** — reference implementations (Two Images, Go/No-Go, Matching to Sample, Random Position, Sequential Learning, Two Images Keyboard). These are **not** real apps — they're teaching material and starting-point templates for building new apps (including with AI-agent assistance), and are never offered by the installer.

## Quick install (Linux)

Clones the repo, pins it to the latest release tag, sets up the virtual environment, and enables the systemd autostart service:

```bash
bash <(curl -sSL https://raw.githubusercontent.com/VetMedUniViennaMesserli/Touchscreen/main/install.sh)
```

It asks once which app (from `Apps/`) should run on this machine, and whether to **Install** or **Uninstall**.

## Updating

Once installed, run `update.sh` from within the install directory whenever a new release is ready:

```bash
~/Touchscreen/update.sh
```

This only ever moves to the newest release tag (never unreleased commits on `main`), reinstalls dependencies only if `requirements.txt` changed, restarts the service, and — unlike `install.sh` — never re-asks which app to run.

## Running

Navigate to the installation directory and run the launcher script:

```bash
cd ~/Touchscreen
./touchscreen.sh
```

The script reads the active app from `.selected_app` (written by the installer). To change it without reinstalling, edit that file directly:

```bash
echo "Apps/RuleLearning/rule_learning.py" > ~/Touchscreen/.selected_app
```

To run a specific app or example directly without changing the configuration:

```bash
cd ~/Touchscreen
source venv/bin/activate
PYTHONPATH=. python Apps/RuleLearning/rule_learning.py
```

Press `Escape` or `Q` to quit any training.

## Manual installation

Clone the repo into your home directory (the systemd service expects it there), then check out a release tag:

```bash
cd ~
git clone https://github.com/VetMedUniViennaMesserli/Touchscreen.git Touchscreen
cd Touchscreen
git checkout "$(git tag -l 'v*' --sort=-v:refname | head -n1)"
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

Standalone binaries are placed in `dist/`, one per app/example, named after its folder (e.g. `dist/RuleLearning`). Requires the venv to be set up first.

Session logs are written to `dist/SessionLogs/` when running a built binary.

## Examples

The following are reference implementations under `Examples/`, not deployable apps — see the note at the top of this file. Each is self-contained with its own `Training_Stimuli/`/`SoundEffects/`.

### Two images (`Examples/TwoImages/two_images.py`)

Two images are shown side by side — one from the **Paintings** category (correct) and one from the **Underwater** category (wrong). Their left/right position is randomised each trial. The individual must touch the painting. Feedback: success sound + inter-trial interval on correct; error sound + red screen on wrong.

Input: touchscreen.

---

### Two images — keyboard (`Examples/TwoImagesKeyboard/two_images_keyboard_input.py`)

Identical to Two images but responds to key presses instead of touch. Press **A** to select the left image, **D** to select the right image. Compatible with the Raspberry Pi Pico W hardware button box (`Devices/Keyboard/`).

Input: keyboard (A / D).

---

### Go / No-Go (`Examples/GoNoGo/go_nogo.py`)

A single image is shown for up to **2 seconds**. The individual should touch it if it is a Painting (Go trial) and withhold if it is an Underwater image (No-Go trial). Not touching within the timeout counts as a correct No-Go response; touching a No-Go stimulus or not touching a Go stimulus counts as an error.

Input: touchscreen.

---

### Matching to sample (`Examples/MatchingToSample/matching_to_sample.py`)

A sample geometric shape is shown alone for **1 second**, then replaced by two choice shapes. The individual must touch the shape that matches the sample. Stimuli are drawn from `Training_Stimuli/Geometric_Shapes/`.

Input: touchscreen.

---

### Random position (`Examples/RandomPosition/random_position.py`)

A single geometric shape is placed at a random position in a **5 × 4 grid**. The individual must touch it regardless of where it appears. Trains position-independent stimulus recognition.

Input: touchscreen.

---

### Sequential learning (`Examples/SequentialLearning/sequential_learning.py`)

Eight identical red circles are arranged in a U-shape across a **2 × 4 grid**. The individual must touch them in a fixed order (bottom row left-to-right, then top row right-to-left). Each correctly touched circle disappears; touching the wrong one triggers an error.

Input: touchscreen.

---

## Apps

### Rule learning (`Apps/RuleLearning/rule_learning.py`)

The first real app built on this Framework — originally a modified/improved version of the Two Images example above.

Two geometric shapes are shown side by side on the **task screen** (primary monitor). The **background** signals which rule is currently active:

| Background | Rule | Correct stimulus |
|---|---|---|
| Light grey | Rule A | Stimulus with the **target colour** |
| Diagonal grey stripes | Rule B | Stimulus with the **target shape** |

The setup dialog and session-end screen are always shown on the **secondary monitor** (if connected), so the subject cannot interact with control options. If only one monitor is present, everything appears on the same screen. (Both dialogs are explicitly bound to their target screen and shown full-screen, so the window manager can't misplace them or leave desktop panels/bars visible underneath.)

Input: touchscreen or keyboard (**A** = left, **D** = right).

---

#### Phases

The experiment runs through seven phases in order. Each phase repeats sessions until the criterion is met, then advances automatically.

| # | Phase | Stimuli | Criterion to advance |
|---|---|---|---|
| 1 | **Pre-Training** | White cross on black — one side only | ≥ 10 / 12 correct in **2 consecutive sessions** |
| 2 | **Rule A** (or B first, depending on counterbalance) | Training colours & shapes | ≥ 10 / 12 correct for each trial type |
| 3 | **Rule B** (or A) | Training colours & shapes | ≥ 10 / 12 correct for each trial type |
| 4 | **Alternate** | Training colours & shapes — rules blocked (half A, half B) | ≥ 10 / 12 correct for each trial type |
| 5 | **Mixed** | Training colours & shapes — rules interleaved | ≥ 10 / 12 correct for each trial type |
| 6 | **Alternating Transfer** | Novel colours (blue/yellow) and shapes (star/square) — rules blocked | ≥ 10 / 12 correct for each trial type |
| 7 | **Mixed Transfer** | Novel colours and shapes — rules interleaved | ≥ 10 / 12 correct for each trial type |

**Training stimuli** (phases 2–5): the target colour and shape configured per individual (e.g. black triangle / white circle).  
**Transfer stimuli** (phases 6–7): novel blue/yellow colours and star/square shapes. Background rules (which bg = which rule) remain unchanged.

---

#### Trial structure

**Error-reduced (ER) trials — first 4 trials of every non-Pre-Training session**

Only one stimulus is shown (the common S+, i.e. the stimulus that satisfies both rules). The other side is blank. This makes the correct choice obvious and gives the subject a successful start to each session.

- In training phases the ER trials use the **rule background** of the first trial in that session.
- In transfer phases the ER trials use a **black background** so the new stimulus stands out clearly.
- A wrong choice (or timeout) during an ER trial shows a **red screen** and repeats the same ER trial (correction trial).
- ER trials **are recorded** in the session log with `trial_count = 0` and `trial_type = 0`. The hidden side is logged as `none`.

**Regular trials (trials 5 onward)**

Both stimuli are shown. The subject must choose the correct one according to the active rule signalled by the background.

- The first regular trial of every non-Pre-Training session is always a **type-1 trial** (common S+ present). Transfer sessions start with a **type-2 trial** (other S+ present) instead.
- **All sessions**: exactly equal numbers of each of the 4 sub-types — (common S+ left), (common S+ right), (other S+ left), (other S+ right). For a 24-trial session this is 6 of each; for a 12-trial rule block inside Alternate/Mixed it is 3 of each.
- **All sessions**: no two consecutive trials have the same full stimulus layout; the S+ side does not repeat more than 3 times in a row.
- **Alternate** sessions: the two rules are presented in two equal sequential blocks (first rule first, matching the individual's counterbalance setting).
- **Mixed** sessions: no more than 3 consecutive trials of the same rule.
- A wrong choice triggers a **red screen** (800 ms) followed by a correction trial (same trial repeated). Up to 5 correction attempts per trial. Correction trials are recorded in the log with `correction_trial > 0`.
- A correct choice triggers a **success sound** and the next trial appears immediately (no green feedback screen).
- No response within **3 minutes** triggers a **yellow timeout screen** followed by a correction trial.

**Pre-Training trials**

All 12 trials per session show only a white cross on a black background, visible on one side at a time. Positioning is semirandom — no more than 3 consecutive trials on the same side. Criterion: 10 or more correct in 2 consecutive sessions.

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
| `trial_count` | Trial number within the session (starts at 1 for regular trials; `0` for ER trials; correction trials do not increment this) |
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

---

## Web version (GitHub Pages)

A browser-based version of Rule Learning is available at:

[https://vetmeduniviennamesserli.github.io/Touchscreen/RuleLearning/](https://vetmeduniviennamesserli.github.io/Touchscreen/RuleLearning/)

The bare site root (`https://vetmeduniviennamesserli.github.io/Touchscreen/`) is a landing page (`docs/index.html`) linking to each app that has a web version. Each app's web frontend lives at `docs/<AppName>/` — not every app needs one; it's a per-app decision. `docs/` must stay at the repo root for GitHub Pages to serve it.

Deployment is handled by `.github/workflows/deploy-pages.yml` and only runs on a pushed `v*` tag or a published GitHub Release — **not** on ordinary commits to `main`. This requires the repo's **Settings → Pages → Build and deployment → Source** to be **GitHub Actions**, and the `github-pages` environment's deployment rules (**Settings → Environments → github-pages**) to allow tag `v*` (and not `main`, so a manual workflow run against `main` can't bypass the tag-only rule).

The web version is designed for **human participants** and differs from the pigtouch version in several ways:

- **ID code entry** — participants type an alphanumeric identifier code before the task starts. No subject-selection screen or manual counterbalancing controls.
- **Automatic test-group & counterbalancing assignment** — on the first request for a given ID code, the participant is assigned a test group (`group1`/`group2`, alternated to keep the groups balanced) and one of the 64 counterbalance conditions in `TSparadigm_counterbalancing.xlsx` (cycled so every condition is used at least once per test group before repeating). Assignment is idempotent — reusing the same ID code always returns the same assignment. This is handled by a separate Apps Script (`docs/RuleLearning/apps-script/assignment.gs`, deployment URL set in `ASSIGN_URL`); if that URL isn't configured or unreachable, the page falls back to a per-browser `localStorage` record instead (not shared across devices).
- **Test group 2** — instead of learning a real second rule, group 2 gets two sessions where the second rule's background is rewarded semi-randomly (50/50 per stimulus pairing), and in the subsequent Alternate/Mixed sessions only needs to hit criterion on rule 1.
- **No Pre-Training phase** — the experiment begins directly at Rule A (or B, per counterbalance).
- **Session-end screens** — show score and a Continue/Repeat button only. No Exit or Download buttons.
- **Session cap** — if the learning criterion isn't reached within 5 sessions of a phase, the experiment ends early with a link to the follow-up survey. Transfer phases always end after exactly 1 session regardless of criterion.
- **Completion screen** — after all phases are done (or a phase's session cap is hit), participants see a completion message and a button linking to the follow-up survey.
- **Automatic data upload** — the accumulated CSV is uploaded to Google Drive after every session end and again when the experiment completes. This means data is preserved even if a participant quits early. The upload URL is set in the `GDRIVE_URL` constant at the top of `docs/RuleLearning/index.html`, and the Apps Script source behind it lives at `docs/RuleLearning/apps-script/upload.gs`.
- Supports touch and keyboard (**A** = left, **D** = right). All trial logic (counterbalancing, trial ordering, criterion) matches the pigtouch version, except where test group 2 diverges as noted above.
