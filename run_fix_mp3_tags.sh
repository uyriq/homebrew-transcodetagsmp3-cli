#!/bin/zsh
# TranscodeTagsMP3 - Wrapper script with logging
# This script is called by the Automator workflow

LOG="$HOME/Library/Logs/TranscodeTagsMP3.log"
SCRIPT="$HOME/Library/Application Scripts/TranscodeTagsMP3/fix_mp3_tags.py"

# Create log directory
mkdir -p "$HOME/Library/Logs"

# Redirect all output to log file
exec >> "$LOG" 2>&1

# Log session start
echo "=========================================="
echo "TranscodeTagsMP3 - $(date)"
echo "Files: $#"
echo "PATH: $PATH"
echo "=========================================="

# Process each file passed as argument
for f in "$@"; do
    echo ""
    echo "Processing: $f"
    /usr/bin/python3 "$SCRIPT" "$f"
    echo "Exit code: $?"
done

echo "Completed: $(date)"
echo ""
