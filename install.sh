#!/bin/zsh
# install.sh — Install TranscodeTagsMP3 Quick Action for Finder on macOS (Apple Silicon).
#
# What this script does:
#   1. Verifies Python 3 is available.
#   2. Installs the `mutagen` Python library (pinned version, user install).
#   3. Copies fix_mp3_tags.py to ~/Library/Application Scripts/TranscodeTagsMP3/.
#   4. Copies the Automator Quick Action to ~/Library/Services/.
#   5. Prints instructions for enabling the Quick Action in System Settings.

set -euo pipefail

SCRIPT_DIR="${0:A:h}"
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

# ── Install Python dependency ─────────────────────────────────────────────────

echo "Installing Python dependency (mutagen 1.47.0)…"
# Use --break-system-packages for modern macOS with Homebrew Python (PEP 668)
python3 -m pip install --quiet --user --break-system-packages "mutagen==1.47.0" 2>/dev/null || \
    python3 -m pip install --quiet --user "mutagen==1.47.0"

# Verify mutagen is importable and report which interpreter has it.
# The wrapper script searches the same candidate list at runtime, so we check
# that at least one candidate can import mutagen; if none can, warn loudly.
echo "Verifying mutagen installation…"
FOUND_PYTHON=""
for _candidate in /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
    if [[ -x "$_candidate" ]] && "$_candidate" -c "import mutagen" 2>/dev/null; then
        echo "  ✓ mutagen found via $_candidate"
        FOUND_PYTHON="$_candidate"
    fi
done
if [[ -z "$FOUND_PYTHON" ]]; then
    echo "  ⚠ mutagen was not found for any known python3 interpreter."
    echo "    The wrapper script will not be able to process MP3 files."
    echo "    Try: $(command -v python3) -m pip install --user mutagen"
fi

# ── Install the Python script ─────────────────────────────────────────────────

echo "Installing fix_mp3_tags.py to $APP_SCRIPTS_DIR …"
mkdir -p "$APP_SCRIPTS_DIR"
cp "$SCRIPT_DIR/fix_mp3_tags.py" "$APP_SCRIPTS_DIR/"
chmod +x "$APP_SCRIPTS_DIR/fix_mp3_tags.py"

echo "Installing wrapper script to $APP_SCRIPTS_DIR …"
cp "$SCRIPT_DIR/run_fix_mp3_tags.sh" "$APP_SCRIPTS_DIR/"
chmod +x "$APP_SCRIPTS_DIR/run_fix_mp3_tags.sh"

# ── Install the Automator Quick Action ───────────────────────────────────────

echo "Installing Automator Quick Action to $SERVICES_DIR …"
mkdir -p "$SERVICES_DIR"
DEST="$SERVICES_DIR/$WORKFLOW_NAME"
if [[ -d "$DEST" ]]; then
    rm -rf "$DEST"
fi
mkdir -p "$DEST/Contents"

# Copy Info.plist from repo
cp "$SCRIPT_DIR/$WORKFLOW_NAME/Contents/Info.plist" "$DEST/Contents/Info.plist"

# Write document.wflow directly — never copy from cache or let pbs restore a stale version.
# inputMethod=0 means "pass input to stdin"; the wrapper reads stdin when $# is 0.
cat > "$DEST/Contents/document.wflow" << 'WFLOW_EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>AMApplicationBuild</key>
	<string>523.2</string>
	<key>AMApplicationVersion</key>
	<string>2.10</string>
	<key>AMDocumentVersion</key>
	<string>2</string>
	<key>actions</key>
	<array>
		<dict>
			<key>action</key>
			<dict>
				<key>AMAccepts</key>
				<dict>
					<key>Container</key>
					<string>List</string>
					<key>Optional</key>
					<true/>
					<key>Types</key>
					<array>
						<string>com.apple.cocoa.string</string>
					</array>
				</dict>
				<key>AMActionVersion</key>
				<string>2.0.3</string>
				<key>AMApplication</key>
				<array>
					<string>Automator</string>
				</array>
				<key>AMParameterProperties</key>
				<dict>
					<key>COMMAND_STRING</key>
					<dict/>
					<key>CheckedForUserDefaultShell</key>
					<dict/>
					<key>inputMethod</key>
					<dict/>
					<key>shell</key>
					<dict/>
					<key>source</key>
					<dict/>
				</dict>
				<key>AMProvides</key>
				<dict>
					<key>Container</key>
					<string>List</string>
					<key>Types</key>
					<array>
						<string>com.apple.cocoa.string</string>
					</array>
				</dict>
				<key>ActionBundlePath</key>
				<string>/System/Library/Automator/Run Shell Script.action</string>
				<key>ActionName</key>
				<string>Run Shell Script</string>
				<key>ActionParameters</key>
				<dict>
					<key>COMMAND_STRING</key>
					<string>/bin/zsh ~/Library/Application\ Scripts/TranscodeTagsMP3/run_fix_mp3_tags.sh "$@"</string>
					<key>CheckedForUserDefaultShell</key>
					<true/>
					<key>inputMethod</key>
					<integer>0</integer>
					<key>shell</key>
					<string>/bin/zsh</string>
					<key>source</key>
					<string></string>
				</dict>
				<key>BundleIdentifier</key>
				<string>com.apple.RunShellScript</string>
				<key>CFBundleVersion</key>
				<string>2.0.3</string>
				<key>CanShowSelectedItemsWhenRun</key>
				<false/>
				<key>CanShowWhenRun</key>
				<true/>
				<key>Category</key>
				<array>
					<string>AMCategoryUtilities</string>
				</array>
				<key>Class Name</key>
				<string>RunShellScriptAction</string>
				<key>InputUUID</key>
				<string>A1B2C3D4-E5F6-7890-ABCD-EF1234567890</string>
				<key>Keywords</key>
				<array>
					<string>Shell</string>
					<string>Script</string>
					<string>Command</string>
					<string>Run</string>
					<string>Unix</string>
				</array>
				<key>OutputUUID</key>
				<string>B2C3D4E5-F6A7-8901-BCDE-F12345678901</string>
				<key>UUID</key>
				<string>C3D4E5F6-A7B8-9012-CDEF-123456789012</string>
				<key>UnlocalizedApplications</key>
				<array>
					<string>Automator</string>
				</array>
				<key>arguments</key>
				<dict>
					<key>0</key>
					<dict>
						<key>default value</key>
						<integer>0</integer>
						<key>name</key>
						<string>inputMethod</string>
						<key>required</key>
						<string>0</string>
						<key>type</key>
						<string>0</string>
						<key>uuid</key>
						<string>0</string>
					</dict>
					<key>1</key>
					<dict>
						<key>default value</key>
						<false/>
						<key>name</key>
						<string>CheckedForUserDefaultShell</string>
						<key>required</key>
						<string>0</string>
						<key>type</key>
						<string>0</string>
						<key>uuid</key>
						<string>1</string>
					</dict>
					<key>2</key>
					<dict>
						<key>default value</key>
						<string></string>
						<key>name</key>
						<string>source</string>
						<key>required</key>
						<string>0</string>
						<key>type</key>
						<string>0</string>
						<key>uuid</key>
						<string>2</string>
					</dict>
					<key>3</key>
					<dict>
						<key>default value</key>
						<string></string>
						<key>name</key>
						<string>COMMAND_STRING</string>
						<key>required</key>
						<string>0</string>
						<key>type</key>
						<string>0</string>
						<key>uuid</key>
						<string>3</string>
					</dict>
					<key>4</key>
					<dict>
						<key>default value</key>
						<string>/bin/sh</string>
						<key>name</key>
						<string>shell</string>
						<key>required</key>
						<string>0</string>
						<key>type</key>
						<string>0</string>
						<key>uuid</key>
						<string>4</string>
					</dict>
				</dict>
				<key>isViewVisible</key>
				<integer>1</integer>
				<key>location</key>
				<string>432.750000:305.000000</string>
				<key>nibPath</key>
				<string>/System/Library/Automator/Run Shell Script.action/Contents/Resources/Base.lproj/main.nib</string>
			</dict>
			<key>isViewVisible</key>
			<integer>1</integer>
		</dict>
	</array>
	<key>connectors</key>
	<dict/>
	<key>workflowMetaData</key>
	<dict>
		<key>applicationBundleID</key>
		<string>com.apple.finder</string>
		<key>applicationBundleIDsByPath</key>
		<dict>
			<key>/System/Library/CoreServices/Finder.app</key>
			<string>com.apple.finder</string>
		</dict>
		<key>applicationPath</key>
		<string>/System/Library/CoreServices/Finder.app</string>
		<key>applicationPaths</key>
		<array>
			<string>/System/Library/CoreServices/Finder.app</string>
		</array>
		<key>inputTypeIdentifier</key>
		<string>com.apple.Automator.fileSystemObject</string>
		<key>outputTypeIdentifier</key>
		<string>com.apple.Automator.nothing</string>
		<key>presentationMode</key>
		<integer>15</integer>
		<key>processesInput</key>
		<false/>
		<key>serviceApplicationBundleID</key>
		<string>com.apple.finder</string>
		<key>serviceApplicationPath</key>
		<string>/System/Library/CoreServices/Finder.app</string>
		<key>serviceInputTypeIdentifier</key>
		<string>com.apple.Automator.fileSystemObject</string>
		<key>serviceOutputTypeIdentifier</key>
		<string>com.apple.Automator.nothing</string>
		<key>serviceProcessesInput</key>
		<false/>
		<key>systemImageName</key>
		<string>NSTouchBarTagIcon</string>
		<key>useAutomaticInputType</key>
		<false/>
		<key>workflowTypeIdentifier</key>
		<string>com.apple.Automator.servicesMenu</string>
	</dict>
</dict>
</plist>
WFLOW_EOF

echo "   ✓ Workflow written ($(wc -c < "$DEST/Contents/document.wflow") bytes)"
plutil -lint "$DEST/Contents/document.wflow" && echo "   ✓ Workflow plist valid"

# Enable the Quick Action in the context menu (avoids user needing to visit System Settings)
echo "Enabling Quick Action in context menu…"
defaults write pbs NSServicesStatus -dict-add "Fix MP3 Tags Encoding" \
    '{enabled_context_menu = 1; enabled_services_menu = 1;}' 2>/dev/null || true

# Refresh macOS Services cache
echo "Refreshing macOS Services cache…"
/System/Library/CoreServices/pbs -flush 2>/dev/null || true
# Restart cfprefsd to clear in-memory Service registrations so Finder
# picks up the new workflow immediately without a reboot.
killall -u "$USER" cfprefsd 2>/dev/null || true
# Kill automator.runner so it reloads the fresh workflow on next Quick Action trigger
killall automator.runner 2>/dev/null || true
sleep 1
killall Finder 2>/dev/null || true

# ── Done ──────────────────────────────────────────────────────────────────────

echo ""
echo "✅  Installation complete!"
echo ""
echo "How to use:"
echo "  1. Select one or more .mp3 files in Finder."
echo "  2. Right-click → Quick Actions → Fix MP3 Tags Encoding."
echo ""
echo "Troubleshooting:"
echo "  • If Quick Action shows an error, check the log:"
echo "    ~/Library/Logs/TranscodeTagsMP3.log"
echo ""
echo "  • If Quick Action is not visible, enable it in:"
echo "    System Settings → Privacy & Security → Extensions → Finder"
echo "    (Enable the checkbox next to 'Fix MP3 Tags Encoding')"
echo ""
echo "  • If you see 'not configured correctly', try:"
echo "    - Reboot your Mac to refresh the Services cache"
echo "    - Or run: /System/Library/CoreServices/pbs -flush"
echo ""
echo "You can also run the script directly from the command line:"
echo "  python3 \"$APP_SCRIPTS_DIR/fix_mp3_tags.py\" file1.mp3 file2.mp3"
