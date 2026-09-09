# Repo restructure plan: multi-app monorepo

Status: **decisions made below — nothing implemented yet. Confirm with the
rest of the team before starting.**

## Background

Today this repo is one app (Rule Learning) plus a shared engine, with the two
tangled together under `App/`:

```
App/
  Framework/        shared PySide6 engine (TrainingWindow, SessionConfig, ...)
  Trainings/        7 scripts, one of which (rule_learning.py) is Rule Learning
  Training_Stimuli/ shared image assets
  SoundEffects/     shared audio assets
docs/
  index.html        Rule Learning's web version (GitHub Pages)
  apps-script/       its Google Apps Script sources
```

Going forward:
- More apps are coming, each potentially with a desktop (Qt) version and,
  where it makes sense, a web version, all built on the same shared
  Framework.
- Desktop apps are deployed one-app-per-PC to physically separate sites
  (e.g. a pig facility, a bird facility), each running unsupervised for long
  stretches.
- 4 collaborators, all with full visibility into everything — confirmed,
  no per-app access restriction is needed.
- Development happens remotely ("hundreds of kilometers away"); the person
  on-site should only ever need to run one script, and only when told the
  update is ready.
- The 6 existing trainings other than Rule Learning (Two Images, Go/No-Go,
  Matching to Sample, Random Position, Sequential Learning, Two Images
  Keyboard) are **not real apps** — they're reference implementations used
  as teaching examples for scientists and as starting-point templates when
  building a new app (including with AI-agent assistance). Rule Learning is
  the first real app, itself originally built as a modified/improved Two
  Images.

## Decision: one monorepo, not multiple GitHub repos

Recap of why (see conversation for full reasoning): the Framework is still
actively co-evolving with app needs, the team is small and shared, and no
collaborator needs restricted visibility. Splitting into multiple repos
(or extracting Framework as a separately-versioned package) adds real
coordination overhead — versioning, publishing, pinning — with no current
payoff. It's cheap to split a monorepo apart later; it's expensive to
un-split multiple repos or hand-sync versions across them while things are
still changing.

**Revisit this if:** a future collaborator should not see other apps' code,
Framework's API stabilizes and apps want independently pinned versions, or
an app needs to be shared/open-sourced on its own.

## Proposed structure

```
Framework/                  (moved from App/Framework — shared engine)

Apps/                        real, deployable, versioned research apps
  RuleLearning/
    rule_learning.py          (moved from App/Trainings/rule_learning.py)
    Training_Stimuli/         (own assets — not shared with other apps)
    SoundEffects/
  NextApp/
    next_app.py
    Training_Stimuli/
    ...

Examples/                    reference implementations — NOT real apps,
                              NOT offered in the field-deployment picker;
                              teaching material + starting-point templates
  TwoImages/
    two_images.py
    Training_Stimuli/
    SoundEffects/
  GoNoGo/
  MatchingToSample/
  RandomPosition/
  SequentialLearning/
  TwoImagesKeyboard/

docs/                        (GitHub Pages root — must stay at repo root)
  index.html                 (NEW: landing page linking to each app below)
  RuleLearning/
    index.html                (moved from docs/index.html)
    apps-script/               (moved from docs/apps-script/)
  NextApp/
    index.html                 (only if that app has a web version)

Devices/                     (unchanged — hardware/firmware)
individuals.csv, install.sh, update.sh, touchscreen.sh, touchscreen.service
```

Key points:
- `docs/` must remain at the repo root and is the *only* place web frontends
  can live for GitHub Pages to serve them — there's no way to publish
  `Apps/RuleLearning/web/` directly, so the web version's canonical home is
  `docs/<AppName>/`, not a copy of something under `Apps/`.
- Each app under `Apps/` owns its desktop entry point and its own assets
  (no shared asset pool — an app's `Training_Stimuli`/`SoundEffects` are
  independent, even if they duplicate what an `Examples/` folder has).
  Whether an app also gets a `docs/<AppName>/` web version is decided
  per app, not assumed.
- `Examples/` holds the 6 existing trainings, kept simple and stable as
  reference material. `install.sh`'s app picker only lists `Apps/*` —
  Examples are never offered as something to deploy to a field PC (they can
  still be run manually for a demo, just not through the installer).
- Framework moves up one level (`App/Framework` → `Framework/`), so
  `touchscreen.sh`'s `PYTHONPATH` changes from `$SCRIPT_DIR/App` to
  `$SCRIPT_DIR`.

## Deployment workflow changes

Today, `install.sh` both installs *and* updates, and always re-prompts
"which app should run" even when just pulling an update. Proposed split:

- **`install.sh`** (first-time only): clone repo, show the app picker
  (see below), set up the venv, install the systemd user service.
- **`update.sh`** (repeatable, the on-site "run this when told"
  script): fetch + check out the latest release tag, reinstall
  dependencies only if `requirements.txt` changed, restart the service.
  **No re-prompt** — it keeps running whichever app was originally
  selected.

**Pin field updates to tags, not `main`.** The web version already uses
tagged major versions (`v1.0`–`v7.0`); extend the same idea to desktop
installs. With 4 people pushing to a shared `main` across potentially
several apps at once, "ready for the field" should be an explicit action
(cutting a tag) rather than an assumption that `main` is always safe to
pull. `update.sh` checks out the newest tag instead of `git pull`-ing
`main` directly. **Decided: repo-wide tags** (the existing `vN.0` scheme
continues to cover the whole repo, not a separate series per app) — a
field site's `update.sh` always just checks out the newest tag, regardless
of which app's changes produced it. Revisit only if that ever causes a
site to pick up an unrelated app's unfinished change through a shared
Framework regression.

**Generate the app picker dynamically** from the `Apps/` folder instead of
the current hardcoded numbered `case` statement in `install.sh` — so adding
a new app doesn't require editing the installer.

## Migration steps (once agreed)

1. Move `App/Framework/` → `Framework/`; update all `from Framework...`
   imports (no change needed — package name stays `Framework`) and
   `touchscreen.sh`'s `PYTHONPATH`.
2. Create `Apps/RuleLearning/`, move `App/Trainings/rule_learning.py` into
   it.
3. Move `docs/index.html` → `docs/RuleLearning/index.html` and
   `docs/apps-script/` → `docs/RuleLearning/apps-script/`. **This changes
   the live URL** for the web version — anyone with the old bare link needs
   the new one.
4. Add a small `docs/index.html` landing page listing/linking each app.
5. Create `Examples/`, move each of the 6 existing trainings (and their own
   copies of the assets they use) into `Examples/<Name>/`. Make sure
   `install.sh`'s app picker only enumerates `Apps/*`, never `Examples/*`.
6. Split `install.sh` / add `update.sh`; switch to tag-based updates; make
   the app picker dynamic (enumerate `Apps/` subfolders).
7. Update `README.md` to describe the new layout.

## Decisions (settled with the team)

1. **The other 6 existing trainings are not apps** — they're reference
   implementations (teaching examples + starting-point templates for new
   apps, including AI-agent-assisted builds), not real deployed research
   instruments. They move to a separate top-level `Examples/` folder, not
   `Apps/`, and are excluded from the field-deployment app picker.
2. **Web version is decided per app**, not required for every app. It only
   makes sense where an app is run by human participants unsupervised
   online (like Rule Learning); animal-only lab apps can stay desktop-only.
3. **Assets are per-app, not shared.** Each app (and each example) owns its
   own `Training_Stimuli`/`SoundEffects`, even if that duplicates content —
   no shared asset pool. Simpler, avoids one app's asset change silently
   affecting another.
4. **Confirmed:** all 4 collaborators have and need full visibility into
   every app's code. The monorepo decision stands.
5. **Tagging stays repo-wide** — one `vN.0` series covering the whole repo,
   not a separate series per app. See the tag-pinning note above.

## Explicitly not changing (for now)

- Not splitting into multiple GitHub repos.
- Not extracting Framework into a separately-versioned/published package.
- Not touching `Devices/` (hardware/firmware).
