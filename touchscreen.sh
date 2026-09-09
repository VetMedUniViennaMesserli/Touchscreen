#!/usr/bin/env bash

# Source - https://stackoverflow.com/questions/59895/how-do-i-get-the-directory-where-a-bash-script-is-located-from-within-the-script
# Posted by dogbane
# Retrieved 2025-11-06, License - CC BY-SA 4.0

## finds where script is located
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

## read app selection written by install.sh; fall back to Rule Learning
CONFIG_FILE="$SCRIPT_DIR/.selected_app"
if [ -f "$CONFIG_FILE" ]; then
    APP="$(cat "$CONFIG_FILE")"
else
    APP="Apps/RuleLearning/rule_learning.py"
fi

## execute python from virtual environment directly
## PYTHONPATH is the repo root so `from Framework...` resolves; the app
## itself locates its own assets relative to its own script path (see
## Framework/paths.py: get_app_root()).
PYTHONPATH="$SCRIPT_DIR" "$SCRIPT_DIR"/venv/bin/python3 "$SCRIPT_DIR"/"$APP"
