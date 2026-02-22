#!/bin/zsh
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
echo "4. Removing Automator and Services caches..."
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

# Remove the NSServices preference file that caches registered Quick Actions.
# macOS regenerates it from ~/Library/Services on next pbs flush.
NSSERVICES="$HOME/Library/Preferences/pbs.plist"
if [[ -f "$NSSERVICES" ]]; then
    rm -f "$NSSERVICES"
    echo "   ✓ Removed $NSSERVICES"
fi

echo ""
echo "5. Flushing Services database and restarting system daemons..."
# Flush the Services (pbs) database
/System/Library/CoreServices/pbs -flush 2>/dev/null && echo "   ✓ pbs -flush" || echo "   - pbs not available"

# Restart cfprefsd (user instance only) — this clears the preferences cache
# that macOS uses to hold compiled Service registrations in memory.
# It auto-restarts immediately via launchd.
killall -u "$USER" cfprefsd 2>/dev/null && echo "   ✓ cfprefsd restarted" || echo "   - cfprefsd not running"

# Kill automator.runner — the background process that executes Quick Actions.
# It will be relaunched by launchd when next needed with fresh workflow state.
killall automator.runner 2>/dev/null && echo "   ✓ automator.runner stopped" || echo "   - automator.runner not running"

# Kill Automator.app if open (it may hold a stale in-memory workflow)
killall Automator 2>/dev/null && echo "   ✓ Automator.app closed" || echo "   - Automator.app not open"

# Give the daemon a moment to restart before Finder queries it
sleep 1

# Restart Finder so it picks up the updated (empty) Services list
killall Finder 2>/dev/null && echo "   ✓ Finder restarted" || echo "   - Finder restart not needed"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✓ Cleanup complete — no reboot required!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "You can reinstall immediately:"
echo "  bash install.sh"
echo ""
echo "If the Quick Action still appears in Finder after reinstall,"
echo "a reboot will clear any remaining in-memory cache."
echo ""
