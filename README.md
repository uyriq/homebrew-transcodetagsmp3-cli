# transcodetagsmp3

A macOS helper (Apple Silicon compatible) that fixes garbled MP3 ID3 tag
encoding — converting Windows-1251 (CP1251) Cyrillic text that was
mis-stored as Latin-1 back to proper UTF-8 so track names, artists and
album titles become readable again.

---

## The problem

MP3 files tagged on Windows with Cyrillic text often store tag strings as
raw **Windows-1251** bytes while declaring the encoding as **ISO-8859-1
(Latin-1)**.  Modern software reads those bytes as Latin-1 and shows
garbled characters:

| What you see         | What it should be    |
|----------------------|----------------------|
| `Ãðóïïà êðîâè`       | `Группа крови`       |
| `Âèêòîð Öîé`         | `Виктор Цой`         |

The fix is a simple re-encoding:

```python
garbled_latin1_string.encode("latin-1").decode("cp1251")
```

---

## Files

| File | Purpose |
|------|---------|
| `fix_mp3_tags.py` | Core Python script — reads ID3 tags, detects mis-encoded frames, converts to UTF-8, saves |
| `requirements.txt` | Python dependency (`mutagen`) |
| `install.sh` | One-shot installer: installs `mutagen`, copies the script, and installs the Automator Quick Action |
| `TranscodeTagsMP3.workflow/` | Automator Quick Action that wires Finder → `fix_mp3_tags.py` |
| `tests/` | `pytest` unit and integration tests |

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

The script runs silently in the background.  Any conversion messages are
written to `~/Library/Logs/fix_mp3_tags.log` if you redirect output there
from the Automator workflow.

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

## Running tests

```bash
pip3 install pytest mutagen
pytest tests/ -v
```

---

## How it works

`fix_mp3_tags.py` iterates over every ID3 text frame (`TIT2`, `TPE1`,
`TALB`, …).  For each string it tries:

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
