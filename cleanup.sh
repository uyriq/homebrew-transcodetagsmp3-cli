#!/usr/bin/env bash
# cleanup.sh - Aggressively remove all traces of TranscodeTagsMP3 workflow
#
# Use this to completely clean the installation before reinstalling

set -euo pipefail

echo "════════════════════════════════════════════════════════════════"
echo "TranscodeTagsMP3 - Complete Cleanup"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "This will remove all installed components of TranscodeTagsMP3."
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

WORKFLOW_PATH="$HOME/Library/Services/TranscodeTagsMP3.workflow"
SCRIPTS_DIR="$HOME/Library/Application Scripts/TranscodeTagsMP3"
LOG_FILE="$HOME/Library/Logs/TranscodeTagsMP3.log"

echo ""
echo "1. Removing workflow..."
if [[ -d "$WORKFLOW_PATH" ]]; then
    rm -rf "$WORKFLOW_PATH"
    echo "   ✓ Removed $WORKFLOW_PATH"
else
    echo "   - Workflow not found (already clean)"
fi

echo ""
echo "2. Removing scripts..."
if [[ -d "$SCRIPTS_DIR" ]]; then
    rm -rf "$SCRIPTS_DIR"
    echo "   ✓ Removed $SCRIPTS_DIR"
else
    echo "   - Scripts directory not found (already clean)"
fi

echo ""
echo "3. Removing log file..."
if [[ -f "$LOG_FILE" ]]; then
    rm -f "$LOG_FILE"
    echo "   ✓ Removed $LOG_FILE"
else
    echo "   - Log file not found (already clean)"
fi

echo ""
echo "4. Flushing Services cache..."
/System/Library/CoreServices/pbs -flush 2>/dev/null || echo "   - pbs command not available"
killall Finder 2>/dev/null || echo "   - Finder restart not needed"

echo ""
echo "5. Removing Automator caches..."
# Remove Automator-related caches
CACHE_DIRS=(
    "$HOME/Library/Caches/com.apple.Automator"
    "$HOME/Library/Caches/com.apple.automator.runner"
    "$HOME/Library/Saved Application State/com.apple.Automator.savedState"
)

for dir in "${CACHE_DIRS[@]}"; do
    if [[ -d "$dir" ]]; then
        rm -rf "$dir"
        echo "   ✓ Removed $dir"
    fi
done

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✓ Cleanup complete!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "IMPORTANT: Reboot your Mac before reinstalling"
echo ""
echo "After reboot, run:"
echo "  bash install.sh"
echo ""
