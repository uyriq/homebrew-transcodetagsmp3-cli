#!/usr/bin/env bash
# install.sh — Install TranscodeTagsMP3 Quick Action for Finder on macOS (Apple Silicon).
#
# What this script does:
#   1. Verifies Python 3 and pip3 are available.
#   2. Installs the `mutagen` Python library.
#   3. Copies fix_mp3_tags.py to ~/Library/Application Scripts/TranscodeTagsMP3/.
#   4. Copies the Automator Quick Action to ~/Library/Services/.
#   5. Prints instructions for enabling the Quick Action in System Settings.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_SCRIPTS_DIR="$HOME/Library/Application Scripts/TranscodeTagsMP3"
SERVICES_DIR="$HOME/Library/Services"
WORKFLOW_NAME="TranscodeTagsMP3.workflow"

# ── Preflight checks ──────────────────────────────────────────────────────────

if [[ "$(uname)" != "Darwin" ]]; then
    echo "Error: This helper is for macOS only." >&2
    exit 1
fi

if ! command -v python3 &>/dev/null; then
    echo "Error: python3 is required.  Install it via Homebrew: brew install python3" >&2
    exit 1
fi

if ! command -v pip3 &>/dev/null; then
    echo "Error: pip3 is required.  It usually ships with python3." >&2
    exit 1
fi

# ── Install Python dependency ─────────────────────────────────────────────────

echo "Installing Python dependency (mutagen)…"
pip3 install --quiet --upgrade mutagen

# ── Install the Python script ─────────────────────────────────────────────────

echo "Installing fix_mp3_tags.py to $APP_SCRIPTS_DIR …"
mkdir -p "$APP_SCRIPTS_DIR"
cp "$SCRIPT_DIR/fix_mp3_tags.py" "$APP_SCRIPTS_DIR/"
chmod +x "$APP_SCRIPTS_DIR/fix_mp3_tags.py"

# ── Install the Automator Quick Action ───────────────────────────────────────

echo "Installing Automator Quick Action to $SERVICES_DIR …"
mkdir -p "$SERVICES_DIR"
DEST="$SERVICES_DIR/$WORKFLOW_NAME"
if [[ -d "$DEST" ]]; then
    rm -rf "$DEST"
fi
cp -r "$SCRIPT_DIR/$WORKFLOW_NAME" "$DEST"

# ── Done ──────────────────────────────────────────────────────────────────────

echo ""
echo "✅  Installation complete!"
echo ""
echo "How to use:"
echo "  1. Select one or more .mp3 files in Finder."
echo "  2. Right-click → Quick Actions → Fix MP3 Tags Encoding."
echo ""
echo "If the Quick Action is not visible, enable it in:"
echo "  System Settings → Privacy & Security → Extensions → Finder Extensions"
echo "  — or —"
echo "  System Settings → Keyboard → Keyboard Shortcuts → Services → Files and Folders"
echo ""
echo "You can also run the script directly from the command line:"
echo "  python3 \"$APP_SCRIPTS_DIR/fix_mp3_tags.py\" file1.mp3 file2.mp3"
