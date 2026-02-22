#!/bin/zsh
# TranscodeTagsMP3 - Wrapper script with logging
# This script is called by the Automator workflow

LOG="$HOME/Library/Logs/TranscodeTagsMP3.log"
SCRIPT="$HOME/Library/Application Scripts/TranscodeTagsMP3/fix_mp3_tags.py"

# Create log directory
mkdir -p "$HOME/Library/Logs"

# Redirect all output to log file
exec >> "$LOG" 2>&1

# Augment PATH — Automator runs with a minimal environment (/usr/bin:/bin only).
# Add Homebrew prefixes (Apple Silicon and Intel) so python3 resolves correctly.
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/local/sbin:/usr/bin:/bin:$PATH"

# Locate a python3 interpreter that has mutagen installed.
# We try Homebrew paths first (where `pip install --user` most likely deposited
# mutagen), then fall back to the system stub.
PYTHON3=""
for candidate in /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
    if [[ -x "$candidate" ]] && "$candidate" -c "import mutagen" 2>/dev/null; then
        PYTHON3="$candidate"
        break
    fi
done

# Log session start
echo "=========================================="
echo "TranscodeTagsMP3 - $(date)"
echo "Files: $#"
echo "Python: ${PYTHON3:-NOT FOUND}"
echo "PATH: $PATH"
echo "=========================================="

if [[ -z "$PYTHON3" ]]; then
    echo "ERROR: No python3 with mutagen found."
    echo "       Run install.sh to install the mutagen library."
    exit 1
fi

# Process each file passed as argument
for f in "$@"; do
    echo ""
    echo "Processing: $f"
    "$PYTHON3" "$SCRIPT" "$f"
    echo "Exit code: $?"
done

echo "Completed: $(date)"
echo ""
