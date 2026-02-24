![Downloads](https://img.shields.io/github/downloads/uyriq/homebrew-transcodetagsmp3-cli/total)

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
| `transcodetagsmp3_cli.py`    | Linux/Homebrew-oriented CLI (`fix`, `install-nautilus --user`)                                     |
| `transcodetagsmp3`           | Executable CLI wrapper                                                                             |
| `linux/nautilus/`            | Nautilus extension template used by CLI installer                                                  |
| `requirements.txt`           | Python dependency (`mutagen`)                                                                      |
| `install.sh`                 | One-shot installer: installs `mutagen`, copies the script, and installs the Automator Quick Action |
| `TranscodeTagsMP3.workflow/` | Automator Quick Action that wires Finder → `fix_mp3_tags.py`                                       |
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

## Installation (Linux / Homebrew)

```bash
brew tap uyriq/transcodetagsmp3-cli
brew install transcodetagsmp3
```

Install Nautilus integration for the current user:

```bash
transcodetagsmp3 install-nautilus --user # install extension
nautilus -q # Quit and relaunch Files
```

Optional system packages for GNOME Files integration:

```bash
sudo apt install -y python3-nautilus libnotify-bin
```

---

## Usage

### Finder (Quick Action)

1. Select one or more `.mp3` files in Finder.
2. Right-click → **Quick Actions** → **Fix MP3 Tags Encoding**.

The script runs silently in the background. By default, output is not saved.
To capture logs, you must manually edit the workflow in Automator:

1. Open `~/Library/Services/TranscodeTagsMP3.workflow`
2. Modify the shell command to redirect output:
   ```bash
   python3 ~/path/to/fix_mp3_tags.py "$@" >> ~/Library/Logs/fix_mp3_tags.log 2>&1
   ```

### Command line

```bash
# Fix a single file
python3 fix_mp3_tags.py track.mp3

# Fix multiple files at once
python3 fix_mp3_tags.py *.mp3
```

### Linux CLI

```bash
# Fix one or many files (default command)
transcodetagsmp3 track.mp3
transcodetagsmp3 *.mp3

# Explicit form is also supported
transcodetagsmp3 fix track.mp3
```

### Linux Nautilus

1. Open a folder with `.mp3` files in GNOME Files.
2. Select one or multiple files.
3. Right-click → **Fix MP3 Tags Encoding**.

Installed integration paths:

- `~/.local/share/nautilus-python/extensions/transcodetagsmp3_extension.py`
- `~/.local/share/transcodetagsmp3/run_fix_mp3_tags.sh`

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
