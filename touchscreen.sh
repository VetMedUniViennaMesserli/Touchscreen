#!/usr/bin/env bash

# Source - https://stackoverflow.com/questions/59895/how-do-i-get-the-directory-where-a-bash-script-is-located-from-within-the-script
# Posted by dogbane
# Retrieved 2025-11-06, License - CC BY-SA 4.0

## finds where script is located
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

## define which app to run
#APP="random_position.py"
APP="App/Trainings/two_images.py"

## execute python from virtual environment directly
PYTHONPATH="$SCRIPT_DIR/App" "$SCRIPT_DIR"/venv/bin/python3 "$SCRIPT_DIR"/"$APP"