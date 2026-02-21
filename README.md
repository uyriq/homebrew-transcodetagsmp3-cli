# transcodetagsmp3

A macOS helper (Apple Silicon compatible) that fixes garbled MP3 ID3 tag
encoding — converting Windows-1251 (CP1251) Cyrillic text that was
mis-stored as Latin-1 back to proper UTF-8 so track names, artists and
album titles become readable again.

**Target Platform:** macOS (Quick Action / Finder integration)  
**Testing:** Full Python test suite runs on Linux and other platforms

---

## The problem

MP3 files tagged on Windows with Cyrillic text often store tag strings as
raw **Windows-1251** bytes while declaring the encoding as **ISO-8859-1
(Latin-1)**. Modern software reads those bytes as Latin-1 and shows
garbled characters:

| What you see   | What it should be |
| -------------- | ----------------- |
| `Ãðóïïà êðîâè` | `Группа крови`    |
| `Âèêòîð Öîé`   | `Виктор Цой`      |

The fix is a simple re-encoding:

```python
garbled_latin1_string.encode("latin-1").decode("cp1251")
```

---

## Files

| File                         | Purpose                                                                                            |
| ---------------------------- | -------------------------------------------------------------------------------------------------- |
| `fix_mp3_tags.py`            | Core Python script — reads ID3 tags, detects mis-encoded frames, converts to UTF-8, saves          |
| `run_fix_mp3_tags.sh`        | Wrapper script with logging — called by Automator workflow to handle redirection                   |
| `requirements.txt`           | Python dependency (`mutagen`)                                                                      |
| `install.sh`                 | One-shot installer: installs `mutagen`, copies scripts and wrapper, installs the Automator Quick Action |
| `diagnose.sh`                | Diagnostic script: checks installation, identifies problems                                         |
| `cleanup.sh`                 | Complete cleanup: removes all components and caches before reinstalling                             |
| `TranscodeTagsMP3.workflow/` | Automator Quick Action that wires Finder → wrapper script → Python script                          |
| `tests/`                     | `pytest` unit and integration tests                                                                |

---

## Installation (macOS)

```bash
git clone https://github.com/uyriq/transcodetagsmp3.git
cd transcodetagsmp3
bash install.sh
```

The installer:

1. Checks for Python 3.
2. Installs `mutagen` via `pip3`.
3. Copies `fix_mp3_tags.py` to
   `~/Library/Application Scripts/TranscodeTagsMP3/`.
4. Copies `TranscodeTagsMP3.workflow` to `~/Library/Services/`.

### Enable the Quick Action in Finder

After installation, enable the service in one of these places:

- **System Settings → Privacy & Security → Extensions → Finder Extensions**
- **System Settings → Keyboard → Keyboard Shortcuts → Services → Files and Folders**

---

## Usage

### Finder (Quick Action)

1. Select one or more `.mp3` files in Finder.
2. Right-click → **Quick Actions** → **Fix MP3 Tags Encoding**.

**Logging:** The Quick Action automatically logs all operations to:
```
~/Library/Logs/TranscodeTagsMP3.log
```

**Note:** The log file is only created when the workflow actually runs. If you see "Service cannot be run because it is not configured correctly" error, the log won't exist yet.

To view the log:
```bash
# View the log (if it exists)
cat ~/Library/Logs/TranscodeTagsMP3.log

# Follow the log in real-time
tail -f ~/Library/Logs/TranscodeTagsMP3.log
```

**Troubleshooting "not configured correctly" error:**

**If Automator shows "cat" command or "to stdin":** This means macOS has cached a corrupted version of the workflow. Use the aggressive cleanup procedure:

1. **Run the diagnostic script to confirm the problem:**
   ```bash
   cd transcodetagsmp3
   bash diagnose.sh
   ```
   This will show exactly what's wrong and which components are installed correctly.

2. **Complete cleanup:**
   ```bash
   bash cleanup.sh
   ```
   This removes all traces including caches.

3. **Reboot your Mac** (essential for clearing all caches)

4. **Reinstall:**
   ```bash
   bash install.sh
   ```

5. **Verify in Automator:**
   ```bash
   open ~/Library/Services/TranscodeTagsMP3.workflow
   ```
   Should show:
   - Command: `/bin/zsh "$HOME/Library/Application Scripts/TranscodeTagsMP3/run_fix_mp3_tags.sh" "$@"`
   - Pass input: **as arguments** (NOT "to stdin")
   - Shell: `/bin/zsh`

6. **Test the Quick Action with MP3 files**

**If still failing after cleanup:**

1. **Test components individually:**
   ```bash
   # Test wrapper script directly
   bash ~/Library/Application\ Scripts/TranscodeTagsMP3/run_fix_mp3_tags.sh /path/to/test.mp3
   
   # Check if log was created
   cat ~/Library/Logs/TranscodeTagsMP3.log
   ```

2. **Check Console.app** for system-level errors:
   - Open Console.app
   - Search for "TranscodeTagsMP3" or "Automator"
   - Look for error messages when attempting to run the service

3. **Manual workflow creation:** If automated installation keeps failing, you can create the workflow manually in Automator:
   - Open Automator
   - New Document → Quick Action
   - Workflow receives: **audio files** in **Finder**
   - Add action: "Run Shell Script"
   - Shell: `/bin/zsh`
   - Pass input: **as arguments**
   - Script: `/bin/zsh "$HOME/Library/Application Scripts/TranscodeTagsMP3/run_fix_mp3_tags.sh" "$@"`
   - Save as "Fix MP3 Tags Encoding"

### Command line

```bash
# Fix a single file
python3 fix_mp3_tags.py track.mp3

# Fix multiple files at once
python3 fix_mp3_tags.py *.mp3
```

---

## Requirements

- macOS (Apple Silicon or Intel)
- Python 3.9+
- [`mutagen`](https://mutagen.readthedocs.io/) ≥ 1.46  
  (`pip3 install mutagen`)

---

## Development and Testing

### Setting up the development environment

```bash
# Create a virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install pytest
```

### Running tests

```bash
# Make sure the virtual environment is activated
source .venv/bin/activate

# Run tests
pytest tests/ -v
```

**Note:** While the Finder Quick Action is macOS-specific, the core Python
script and all tests run perfectly on Linux and other platforms. The test
suite includes a reusable `broken_cp1251_mp3` pytest fixture that
generates temporary MP3 files with intentionally broken tags for testing.

---

## How it works

`fix_mp3_tags.py` iterates over every ID3 text frame (`TIT2`, `TPE1`,
`TALB`, …). For each string it tries:

```python
text.encode("latin-1").decode("cp1251")
```

- If the string contains characters outside the Latin-1 range (i.e. it is
  already proper Unicode Cyrillic), `encode("latin-1")` raises
  `UnicodeEncodeError` and the string is left untouched.
- If the round-trip succeeds and the result differs from the input, the
  frame is updated to the corrected string with **UTF-8** encoding and the
  file is re-saved as **ID3 v2.3**.
- Files with no encoding issues are not modified.
