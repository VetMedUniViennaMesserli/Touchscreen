#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

source "$SCRIPT_DIR/venv/bin/activate"

# Builds a standalone executable for every app under Apps/ and every
# reference implementation under Examples/. Each one owns its own
# Training_Stimuli/ and SoundEffects/ (not shared), so --add-data is
# generated per app instead of pointing at one common assets folder.
for group in Apps Examples; do
    for dir in "$SCRIPT_DIR/$group"/*/; do
        [ -d "$dir" ] || continue
        name="$(basename "$dir")"
        entry="$(find "$dir" -maxdepth 1 -name '*.py' | sort | head -n1)"
        [ -n "$entry" ] || continue

        add_data=()
        [ -d "$dir/Training_Stimuli" ] && add_data+=(--add-data "$dir/Training_Stimuli:Training_Stimuli")
        [ -d "$dir/SoundEffects" ]     && add_data+=(--add-data "$dir/SoundEffects:SoundEffects")

        pyinstaller \
            "${add_data[@]}" \
            --paths "$SCRIPT_DIR" \
            --distpath "$SCRIPT_DIR/dist" \
            --workpath "$SCRIPT_DIR/build" \
            --specpath "$SCRIPT_DIR" \
            --name "$name" \
            --windowed \
            --onefile \
            "$entry"
    done
done
