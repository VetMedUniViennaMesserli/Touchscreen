# Contributing

This is a small lab repo (VetMedUni Vienna, Messerli Institute) — this guide
is deliberately short. See `README.md` for full setup/usage details.

## Setup

```bash
git clone https://github.com/VetMedUniViennaMesserli/Touchscreen.git
cd Touchscreen
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Repo layout

- `Framework/` — shared engine, used by every app.
- `Apps/` — real, deployable apps (what field PCs run).
- `Examples/` — reference trainings, not real apps. Copy `Examples/<Name>/`
  to `Apps/<NewName>/` as the starting point for a new app.
- `docs/` — web versions (GitHub Pages), one folder per app that has one.

See `README.md` for the full picture, and `RESTRUCTURE_PLAN.md` for the
reasoning behind this layout.

## Making changes

- Commit directly to `main`, or open a PR — whichever fits the change.
  There's no required review process for the 4 of us.
- Test manually before committing: run the affected app/website and check
  a few trials go through correctly. There's no automated test suite.
- **Nothing ships until a version tag is pushed.** Field PCs (`update.sh`)
  and the website only ever pick up the latest `vN.0` tag, never raw
  commits on `main`. If your change should go live, cut a tag:
  ```bash
  git tag -a vN.0 -m "short summary"
  git push origin vN.0
  ```
  This alone triggers both the GitHub Pages deploy and the binary release
  build — no extra steps needed.

## Adding a new app

Copy an `Examples/<Name>/` folder to `Apps/<NewName>/` and edit the logic.
That's it — being under `Apps/` is what makes the installer, `build.sh`,
and the release workflow pick it up automatically.
