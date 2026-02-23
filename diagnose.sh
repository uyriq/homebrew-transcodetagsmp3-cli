#!/bin/zsh
# diagnose.sh - Diagnostic script for TranscodeTagsMP3 installation
#
# This script checks all components and helps identify why the workflow isn't working

set -euo pipefail

echo "════════════════════════════════════════════════════════════════"
echo "TranscodeTagsMP3 Installation Diagnostics"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check 1: Python script
echo "1. Checking Python script..."
SCRIPT_PATH="$HOME/Library/Application Scripts/TranscodeTagsMP3/fix_mp3_tags.py"
if [[ -f "$SCRIPT_PATH" ]]; then
    check_pass "Python script exists: $SCRIPT_PATH"
    if [[ -x "$SCRIPT_PATH" ]]; then
        check_pass "Python script is executable"
    else
        check_fail "Python script is NOT executable"
    fi
else
    check_fail "Python script NOT FOUND: $SCRIPT_PATH"
fi
echo ""

# Check 2: Wrapper script
echo "2. Checking wrapper script..."
WRAPPER_PATH="$HOME/Library/Application Scripts/TranscodeTagsMP3/run_fix_mp3_tags.sh"
if [[ -f "$WRAPPER_PATH" ]]; then
    check_pass "Wrapper script exists: $WRAPPER_PATH"
    if [[ -x "$WRAPPER_PATH" ]]; then
        check_pass "Wrapper script is executable"
    else
        check_fail "Wrapper script is NOT executable"
    fi
    echo ""
    echo "Wrapper script content (first 10 lines):"
    head -10 "$WRAPPER_PATH" | sed 's/^/    /'
else
    check_fail "Wrapper script NOT FOUND: $WRAPPER_PATH"
fi
echo ""

# Check 3: Workflow
echo "3. Checking Automator workflow..."
WORKFLOW_PATH="$HOME/Library/Services/TranscodeTagsMP3.workflow"
if [[ -d "$WORKFLOW_PATH" ]]; then
    check_pass "Workflow exists: $WORKFLOW_PATH"
    
    WFLOW_FILE="$WORKFLOW_PATH/Contents/document.wflow"
    if [[ -f "$WFLOW_FILE" ]]; then
        check_pass "Workflow definition file exists"
        
        # Check COMMAND_STRING
        echo ""
        echo "COMMAND_STRING from workflow:"
        COMMAND=$(sed -n '/<key>COMMAND_STRING<\/key>/,/<\/string>/p' "$WFLOW_FILE" | grep '<string>' | sed 's/.*<string>//; s/<\/string>.*//')
        echo "    $COMMAND"
        
        if [[ "$COMMAND" == "cat" ]]; then
            check_fail "COMMAND is corrupted (showing literal 'cat')"
        elif [[ "$COMMAND" == *"run_fix_mp3_tags.sh"* ]]; then
            check_pass "COMMAND contains wrapper script reference - looks correct"
        elif [[ -z "$COMMAND" || "$COMMAND" == "List" ]]; then
            check_fail "COMMAND is empty or showing placeholder text"
        else
            check_warn "COMMAND does not reference expected wrapper script: $COMMAND"
        fi
        
        # Check inputMethod
        INPUT_METHOD=$(sed -n '/<key>inputMethod<\/key>/,/<integer>/p' "$WFLOW_FILE" | grep '<integer>' | sed 's/.*<integer>//; s/<\/integer>.*//')
        echo ""
        echo "inputMethod value: $INPUT_METHOD"
        if [[ "$INPUT_METHOD" == "1" ]]; then
            check_pass "inputMethod is 1 (as arguments) - CORRECT"
        elif [[ "$INPUT_METHOD" == "0" ]]; then
            check_fail "inputMethod is 0 (to stdin) - WRONG"
        else
            check_warn "inputMethod value unclear: $INPUT_METHOD"
        fi
    else
        check_fail "Workflow definition file NOT FOUND"
    fi
else
    check_fail "Workflow NOT FOUND: $WORKFLOW_PATH"
fi
echo ""

# Check 4: Python and mutagen
echo "4. Checking Python and dependencies..."
if command -v python3 &>/dev/null; then
    check_pass "python3 found: $(which python3)"
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo "    Version: $PYTHON_VERSION"
    
    if python3 -c "import mutagen" 2>/dev/null; then
        check_pass "mutagen module is installed"
        MUTAGEN_VERSION=$(python3 -c "import mutagen; print(mutagen.version_string)")
        echo "    Version: $MUTAGEN_VERSION"
    else
        check_fail "mutagen module NOT installed"
    fi
else
    check_fail "python3 NOT FOUND"
fi

# Check Python candidates used by the wrapper script at runtime.
# The wrapper augments PATH and searches these paths in order; at least one
# must have mutagen for the workflow to work.
echo ""
echo "4b. Checking python3 candidates used by the wrapper script..."
WRAPPER_FOUND_PYTHON=""
for _candidate in /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
    if [[ -x "$_candidate" ]]; then
        if "$_candidate" -c "import mutagen" 2>/dev/null; then
            _ver=$("$_candidate" --version 2>&1)
            _mut=$("$_candidate" -c "import mutagen; print(mutagen.version_string)")
            check_pass "$_candidate ($_ver) — mutagen $_mut ✓"
            WRAPPER_FOUND_PYTHON="$_candidate"
        else
            check_warn "$_candidate — mutagen NOT installed here"
        fi
    fi
done
if [[ -z "$WRAPPER_FOUND_PYTHON" ]]; then
    check_fail "No candidate python3 has mutagen — the wrapper will fail at runtime"
    echo "    Fix: run install.sh (installs mutagen for the active python3)"
else
    check_pass "Wrapper will use: $WRAPPER_FOUND_PYTHON"
fi
echo ""

# Check 5: System info
echo "5. System information..."
echo "    macOS version: $(sw_vers -productVersion)"
echo "    Architecture: $(uname -m)"
echo ""

# Check 6: Log directory
echo "6. Checking log directory..."
LOG_DIR="$HOME/Library/Logs"
if [[ -d "$LOG_DIR" ]]; then
    check_pass "Log directory exists: $LOG_DIR"
    LOG_FILE="$LOG_DIR/TranscodeTagsMP3.log"
    if [[ -f "$LOG_FILE" ]]; then
        check_pass "Log file exists (workflow has run at least once)"
        echo ""
        echo "Last 20 lines of log:"
        echo "────────────────────────────────────────"
        tail -20 "$LOG_FILE" | sed 's/^/    /'
        echo "────────────────────────────────────────"
    else
        check_warn "Log file does NOT exist (workflow hasn't run yet, or failed to start)"
    fi
else
    check_fail "Log directory NOT FOUND: $LOG_DIR"
fi
echo ""

# Summary and recommendations
echo "════════════════════════════════════════════════════════════════"
echo "SUMMARY AND RECOMMENDATIONS"
echo "════════════════════════════════════════════════════════════════"
echo ""

if [[ -f "$WORKFLOW_PATH/Contents/document.wflow" ]]; then
    COMMAND=$(sed -n '/<key>COMMAND_STRING<\/key>/,/<\/string>/p' "$WORKFLOW_PATH/Contents/document.wflow" | grep '<string>' | sed 's/.*<string>//; s/<\/string>.*//')
    INPUT_METHOD=$(sed -n '/<key>inputMethod<\/key>/,/<integer>/p' "$WORKFLOW_PATH/Contents/document.wflow" | grep '<integer>' | sed 's/.*<integer>//; s/<\/integer>.*//')
    
    NEEDS_FIX=0
    
    if [[ "$COMMAND" == "cat" ]]; then
        echo "⚠️  WORKFLOW COMMAND IS CORRUPTED (showing 'cat')"
        NEEDS_FIX=1
    elif [[ ! "$COMMAND" == *"run_fix_mp3_tags.sh"* ]]; then
        echo "⚠️  WORKFLOW COMMAND DOESN'T REFERENCE WRAPPER SCRIPT"
        echo "   Current: $COMMAND"
        echo "   Expected: Should contain 'run_fix_mp3_tags.sh'"
        NEEDS_FIX=1
    fi
    
    if [[ "$INPUT_METHOD" == "0" ]]; then
        echo "⚠️  WORKFLOW inputMethod IS WRONG (0=stdin, should be 1=arguments)"
        echo "   This causes 'Files: 0' and prevents MP3 files from being passed"
        NEEDS_FIX=1
    fi
    
    if [[ $NEEDS_FIX -eq 1 ]]; then
        echo ""
        echo "The workflow is corrupted in macOS cache. Follow these steps:"
        echo ""
        echo "1. Run the cleanup script:"
        echo "   bash cleanup.sh"
        echo ""
        echo "2. Reboot your Mac (essential to clear all caches)"
        echo ""
        echo "3. Reinstall:"
        echo "   bash install.sh"
        echo ""
        echo "4. Open Automator to verify the workflow:"
        echo "   open ~/Library/Services/TranscodeTagsMP3.workflow"
        echo "   Check that:"
        echo "   - Command contains: run_fix_mp3_tags.sh"
        echo "   - Pass input is: 'as arguments' (NOT 'to stdin')"
        echo "   - Shell is: /bin/zsh"
    else
        echo "✓ Workflow configuration looks correct"
        echo ""
        if [[ -f "$HOME/Library/Logs/TranscodeTagsMP3.log" ]]; then
            LAST_FILES=$(tail -50 "$HOME/Library/Logs/TranscodeTagsMP3.log" | grep "Files:" | tail -1)
            if [[ "$LAST_FILES" == *"Files: 0"* ]]; then
                echo "⚠️  Log shows 'Files: 0' - workflow may not be receiving file arguments"
                echo "   This can happen if:"
                echo "   - Files weren't selected in Finder before running the service"
                echo "   - The workflow cache hasn't been refreshed"
                echo "   Try:"
                echo "   1. Select actual MP3 files in Finder"
                echo "   2. Right-click → Quick Actions → Fix MP3 Tags Encoding"
                echo "   3. Check log again: cat ~/Library/Logs/TranscodeTagsMP3.log"
            fi
        fi
    fi
fi

echo ""
echo "To test components individually:"
echo ""
echo "  # Test Python script directly:"
echo "  python3 '$SCRIPT_PATH' /path/to/test.mp3"
echo ""
echo "  # Test wrapper script directly:"
echo "  #!/bin/zsh  '$WRAPPER_PATH' /path/to/test.mp3"
echo ""
echo "  # Check log:"
echo "  cat ~/Library/Logs/TranscodeTagsMP3.log"
echo ""
