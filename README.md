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

Reference implementations under `Examples/`, not deployable apps — see the note at the top of this file. Each is self-contained with its own `Training_Stimuli/`/`SoundEffects/` and its own README with full details:

- [Two images](Examples/TwoImages/README.md) — touchscreen
- [Two images — keyboard](Examples/TwoImagesKeyboard/README.md) — keyboard (A/D)
- [Go / No-Go](Examples/GoNoGo/README.md) — touchscreen
- [Matching to sample](Examples/MatchingToSample/README.md) — touchscreen
- [Random position](Examples/RandomPosition/README.md) — touchscreen
- [Sequential learning](Examples/SequentialLearning/README.md) — touchscreen

**Turning an example into an app:** copy `Examples/<Name>/` to `Apps/<NewName>/` and edit the logic. That's it — being under `Apps/` is what makes `install.sh`, `build.sh`, and the release-build workflow treat it as a real app; assets and session-log naming already work relative to the folder, no config to update.

## Apps

Real, deployable, versioned apps under `Apps/`:

- [Rule learning](Apps/RuleLearning/README.md) — the first real app built on this Framework, originally a modified/improved version of the Two Images example above. Touchscreen or keyboard (A/D). Full details (phases, trial structure, setup dialog, session logs, web version) in its README.
