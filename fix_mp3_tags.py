#!/usr/bin/env python3
"""
fix_mp3_tags.py — Fix MP3 ID3 tag encoding from misread Windows-1251 (CP1251) to UTF-8.

Background
----------
Many MP3 files tagged on Windows systems with Cyrillic (Russian) text store the
tag strings as raw Windows-1251 bytes, but declare the encoding in the ID3 frame
as ISO-8859-1 (Latin-1).  When modern software reads those bytes as Latin-1 it
produces garbled characters (e.g. "Ïðèâåò" instead of "Привет").

The fix is straightforward:
  garbled_latin1_string.encode('latin-1').decode('cp1251')

This script accepts one or more MP3 file paths, detects all text frames that
can be round-tripped through Latin-1 → CP1251, applies the conversion, and
re-saves the file with UTF-8 encoding (ID3 v2.3).

macOS Quick Action usage
------------------------
Install with ./install.sh, then right-click any MP3 in Finder and choose
  Quick Actions ▸ Fix MP3 Tags Encoding

Command-line usage
------------------
    python3 fix_mp3_tags.py file1.mp3 [file2.mp3 ...]
"""

import os
import sys

try:
    from mutagen.id3 import ID3, ID3NoHeaderError
    from mutagen.id3 import Encoding
except ImportError:
    print("Error: 'mutagen' is required.  Install it with:  pip3 install mutagen")
    sys.exit(1)


def fix_encoding(text: str) -> str:
    """
    Attempt to fix a Windows-1251 string that was stored/read as Latin-1.

    If *text* encodes cleanly to Latin-1 bytes and those bytes decode as valid
    CP1251, and the result looks like genuine Cyrillic text, return the
    corrected string.  Otherwise return *text* unchanged.
    """
    # If the text already contains real Cyrillic, it was decoded correctly.
    if any(0x0400 <= ord(ch) <= 0x04FF for ch in text):
        return text

    try:
        candidate = text.encode("latin-1").decode("cp1251")
    except (UnicodeEncodeError, UnicodeDecodeError):
        # Text contains characters above Latin-1 (already real Unicode) or
        # bytes that are not valid CP1251 — leave it alone.
        return text

    if candidate == text:
        return text

    # Heuristic: only apply the fix when the decoded candidate is predominantly
    # Cyrillic.  This prevents corrupting legitimate Latin-1 text (e.g. "café")
    # where a stray CP1251 mapping might produce a lone Cyrillic character.
    cyrillic_count = 0
    alpha_count = 0
    for ch in candidate:
        if ch.isalpha():
            alpha_count += 1
            if 0x0400 <= ord(ch) <= 0x04FF:
                cyrillic_count += 1

    if cyrillic_count == 0:
        return text
    # alpha_count is at least cyrillic_count > 0 here, so no division by zero.
    if alpha_count and (cyrillic_count / alpha_count) < 0.5:
        return text

    return candidate


def fix_mp3_file(filepath: str) -> bool:
    """
    Fix ID3 tag encoding for a single MP3 file.

    Returns True on success (even if no tags changed), False on error.
    """
    print(f"Processing: {filepath}")

    try:
        tags = ID3(filepath)
    except ID3NoHeaderError:
        print("  No ID3 tags found — skipping.")
        return True
    except Exception as exc:
        print(f"  Error reading tags: {exc}")
        return False

    any_changed = False
    for key in list(tags.keys()):
        frame = tags[key]
        if not hasattr(frame, "text"):
            continue

        frame_changed = False
        new_texts = []
        for fragment in frame.text:
            if not isinstance(fragment, str):
                new_texts.append(fragment)
                continue
            fixed = fix_encoding(fragment)
            if fixed != fragment:
                print(f"  {key}: {fragment!r}  →  {fixed!r}")
                frame_changed = True
            new_texts.append(fixed)

        if frame_changed:
            frame.text = new_texts
            frame.encoding = Encoding.UTF8
            any_changed = True

    if any_changed:
        try:
            tags.save(filepath, v2_version=3)
            print("  Saved.")
        except Exception as exc:
            print(f"  Error saving: {exc}")
            return False
    else:
        print("  Tags already look correct — nothing changed.")

    return True


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: fix_mp3_tags.py <file1.mp3> [file2.mp3 ...]")
        sys.exit(1)

    ok = 0
    failed = 0
    for path in sys.argv[1:]:
        if not os.path.isfile(path):
            print(f"Skipping (not a file): {path}")
            failed += 1
            continue
        if not path.lower().endswith(".mp3"):
            print(f"Skipping (not an MP3): {path}")
            continue
        if fix_mp3_file(path):
            ok += 1
        else:
            failed += 1

    print(f"\nDone: {ok} processed, {failed} error(s).")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
