#!/usr/bin/env bash
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
        
        if [[ "$COMMAND" == "cat" ]] || [[ "$COMMAND" == *"cat"* ]]; then
            check_fail "COMMAND is corrupted (showing 'cat')"
        else
            check_pass "COMMAND looks correct"
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
    
    if [[ "$COMMAND" == "cat" ]] || [[ "$INPUT_METHOD" == "0" ]]; then
        echo "⚠️  WORKFLOW IS CORRUPTED IN MACOS CACHE"
        echo ""
        echo "The workflow file on disk may be correct, but macOS is using a cached"
        echo "corrupted version. Try these steps:"
        echo ""
        echo "1. Run the cleanup script:"
        echo "   bash cleanup.sh"
        echo ""
        echo "2. Reboot your Mac"
        echo ""
        echo "3. Reinstall:"
        echo "   bash install.sh"
        echo ""
        echo "4. Open Automator to verify the workflow:"
        echo "   open ~/Library/Services/TranscodeTagsMP3.workflow"
        echo "   Check that it shows the wrapper script command, not 'cat'"
        echo "   Check that 'Pass input' is 'as arguments', not 'to stdin'"
    fi
fi

echo ""
echo "To test components individually:"
echo ""
echo "  # Test Python script directly:"
echo "  python3 '$SCRIPT_PATH' /path/to/test.mp3"
echo ""
echo "  # Test wrapper script directly:"
echo "  bash '$WRAPPER_PATH' /path/to/test.mp3"
echo ""
echo "  # Check log:"
echo "  cat ~/Library/Logs/TranscodeTagsMP3.log"
echo ""
