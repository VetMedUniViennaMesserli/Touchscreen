#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

source "$SCRIPT_DIR/venv/bin/activate"

cd "$SCRIPT_DIR/App"

for script in two_images matching_to_sample go_nogo random_position sequential_learning two_images_keyboard_input rule_learning; do
    pyinstaller \
        --add-data "$SCRIPT_DIR/App/Training_Stimuli:Training_Stimuli" \
        --add-data "$SCRIPT_DIR/App/SoundEffects:SoundEffects" \
        --paths . \
        --distpath "$SCRIPT_DIR/dist" \
        --workpath "$SCRIPT_DIR/build" \
        --specpath "$SCRIPT_DIR" \
        --windowed \
        --onefile \
        "Trainings/${script}.py"
done
