# Product Requirements Document: TranscodeTagsMP3

## 1. Project Overview

### 1.1 Purpose

TranscodeTagsMP3 is a macOS utility that fixes garbled MP3 ID3 tag encoding issues, specifically converting Windows-1251 (CP1251) Cyrillic text that was mis-stored as Latin-1 (ISO-8859-1) back to proper UTF-8 encoding. This makes track names, artist names, and album titles readable.

### 1.2 Target Platform

- **Primary:** macOS (both Apple Silicon and Intel)
- **Secondary:** Core Python script is cross-platform for testing
- **Minimum macOS Version:** macOS 10.14+ (Catalina and later recommended)

### 1.3 Problem Statement

MP3 files tagged on Windows systems often store Cyrillic text as raw Windows-1251 bytes while declaring the encoding as ISO-8859-1 (Latin-1). When modern software reads these files, it interprets the bytes as Latin-1, resulting in garbled text display:

| Garbled (Latin-1 interpretation) | Correct (CP1251 decoding) |
| -------------------------------- | ------------------------- |
| `Ãðóïïà êðîâè`                   | `Группа крови`            |
| `Âèêòîð Öîé`                     | `Виктор Цой`              |

## 2. Functional Requirements

### 2.1 Core Functionality

- **FR-1:** Detect and fix mis-encoded ID3v2 text frames in MP3 files
- **FR-2:** Convert Windows-1251 bytes stored as Latin-1 to proper UTF-8
- **FR-3:** Use Cyrillic-majority heuristic (≥50% Cyrillic characters) to prevent false positives
- **FR-4:** Preserve already-correct UTF-8 tags unchanged
- **FR-5:** Save modified files as ID3v2.3 format only when changes are made
- **FR-6:** Process multiple files in batch mode

### 2.2 User Interface

- **FR-7:** Provide macOS Finder integration via Quick Action or Services (right-click context menu)
- **FR-8:** Support command-line invocation for advanced users
- **FR-9:** Run silently with background logging for Finder integration
- **FR-10:** Provide diagnostic and troubleshooting tools

### 2.3 Installation & Configuration

- **FR-11:** One-command installation script
- **FR-12:** Automatic dependency installation (mutagen library)
- **FR-13:** Automatic Automator workflow installation
- **FR-14:** Diagnostic script to verify installation
- **FR-15:** Cleanup script for complete removal

## 3. Non-Functional Requirements

### 3.1 Reliability

- **NFR-1:** Never corrupt MP3 audio data (tags only)
- **NFR-2:** Graceful error handling with informative messages

### 3.3 Usability

- **NFR-3:** Clear error messages in log files

### 3.4 Maintainability

- **NFR-4:** Comprehensive test suite (unit and integration tests)
- **NFR-5:** Well-documented code with inline comments
- **NFR-6:** Modular architecture for easy updates

## 4. Technical Architecture

### 4.1 System Components

```
┌─────────────────────────────────────────────────────────┐
│                    User Interaction                      │
│  Finder Context Menu → Quick Action → Automator Workflow│
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Wrapper Script (run_fix_mp3_tags.sh)       │
│  - Logging redirection                                   │
│  - Environment setup                                     │
│  - File iteration                                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│           Core Python Script (fix_mp3_tags.py)          │
│  - ID3 tag reading (mutagen)                            │
│  - Encoding detection (Cyrillic heuristic)              │
│  - CP1251 → UTF-8 conversion                            │
│  - ID3v2.3 tag writing                                  │
└─────────────────────────────────────────────────────────┘
```

### 4.2 Component Details

#### 4.2.1 Automator Workflow (`TranscodeTagsMP3.workflow`)

- **Type:** Quick Action (Service)
- **Trigger:** Right-click on MP3 files in Finder
- **Input:** Audio files (`public.mp3` or `com.apple.Automator.fileSystemObject.audio`)
- **Action:** Run Shell Script
- **Shell:** `/bin/zsh`
- **Input Method:** As arguments (`inputMethod=1`)
- **Command:** `/bin/zsh ~/Library/Application\ Scripts/TranscodeTagsMP3/run_fix_mp3_tags.sh "$@"`

**Critical Configuration:**

- Must use tilde expansion with backslash-escaped spaces: `~/Library/Application\ Scripts/`
- Must use `inputMethod=1` (as arguments) not `0` (stdin)
- Must avoid XML entities in COMMAND_STRING for reliable parsing

#### 4.2.2 Wrapper Script (`run_fix_mp3_tags.sh`)

- **Purpose:** Handle logging and shell-level operations
- **Location:** `~/Library/Application Scripts/TranscodeTagsMP3/run_fix_mp3_tags.sh`
- **Key Functions:**
  - Create log directory: `~/Library/Logs/`
  - Redirect stdout/stderr to log: `~/Library/Logs/TranscodeTagsMP3.log`
  - Iterate over file arguments: `for f in "$@"`
  - Invoke Python script with absolute path: `/usr/bin/python3`

**Design Rationale:**

- Keeps shell logic out of Automator XML (prevents parsing issues)
- Provides comprehensive logging without modifying Python script
- Uses absolute paths for reliability in restricted macOS Services environment

#### 4.2.3 Core Script (`fix_mp3_tags.py`)

- **Language:** Python 3.9+
- **Location:** `~/Library/Application Scripts/TranscodeTagsMP3/fix_mp3_tags.py`
- **Key Functions:**
  - `fix_encoding(text)`: Convert CP1251 bytes to UTF-8 with Cyrillic heuristic
  - `fix_mp3_file(path)`: Process single MP3 file
  - `main()`: CLI entry point with batch processing

**Encoding Algorithm:**

1. Attempt to encode text as Latin-1 (will fail if already Unicode)
2. Decode resulting bytes as CP1251
3. Verify ≥50% of alphabetic characters are Cyrillic (U+0400-U+04FF)
4. If valid, accept conversion; otherwise, keep original

#### 4.2.4 Installation Script (`install.sh`)

- **Purpose:** One-shot automated installation
- **Steps:**
  1. Verify macOS and Python 3 availability
  2. Install mutagen via pip with PEP 668 compliance
  3. Copy Python script to Application Scripts directory
  4. Copy wrapper script to Application Scripts directory
  5. Install Automator workflow to ~/Library/Services/
  6. Refresh Services cache (`pbs -flush`)

#### 4.2.5 Diagnostic Script (`diagnose.sh`)

- **Purpose:** Troubleshooting and verification
- **Checks:**
  - Python script existence and permissions
  - Wrapper script existence and permissions
  - Workflow installation and configuration
  - Python and mutagen availability
  - Log file content analysis
  - Workflow corruption detection (cat command, wrong inputMethod)

#### 4.2.6 Cleanup Script (`cleanup.sh`)

- **Purpose:** Complete removal before reinstallation
- **Actions:**
  - Remove workflow from ~/Library/Services/
  - Remove scripts from Application Scripts directory
  - Remove log file
  - Clear Automator caches (com.apple.Automator, automator.runner)
  - Flush Services database

## 5. Technologies and Dependencies

### 5.1 Programming Languages

- **Python:** 3.9+ (core logic)
- **Shell:** Zsh (wrapper and installation scripts)
- **XML:** Property List format (Automator workflow configuration)

### 5.2 Required Libraries

#### Python Dependencies

```
mutagen==1.47.0
```

- **Purpose:** ID3 tag reading and writing
- **License:** GPL-2.0
- **Installation:** User-local with `--break-system-packages` flag for PEP 668 compliance

#### Testing Dependencies (Development Only)

```
pytest>=7.0
mutagen>=1.46
```

### 5.3 macOS System Components

- **Automator:** Quick Action (Service) framework
- **Finder:** File browser integration
- **Services Database:** `/System/Library/CoreServices/pbs`
- **Application Scripts:** Sandboxed script storage location

### 5.4 File System Paths

| Component      | Installation Path                                                    |
| -------------- | -------------------------------------------------------------------- |
| Python Script  | `~/Library/Application Scripts/TranscodeTagsMP3/fix_mp3_tags.py`     |
| Wrapper Script | `~/Library/Application Scripts/TranscodeTagsMP3/run_fix_mp3_tags.sh` |
| Workflow       | `~/Library/Services/TranscodeTagsMP3.workflow`                       |
| Log File       | `~/Library/Logs/TranscodeTagsMP3.log`                                |

## 6. Security and Permissions

### 6.1 Required Permissions

- **File System Access:** Read/write access to user-selected MP3 files
- **Application Scripts Access:** Read access to `~/Library/Application Scripts/TranscodeTagsMP3/`
- **Services:** Ability to register and run Quick Actions (preferable over Services)
- **No Network Access:** Application operates entirely offline

### 6.2 Security Considerations

- **Sandboxed Execution:** Scripts run in macOS Application Scripts sandbox
- **User Authorization:** Files only processed when explicitly selected by user
- **No Privileged Access:** No root or administrator rights required
- **Input Validation:** File type checking via ID3 header verification
- **Safe Operations:** Only modifies metadata, never audio streams

### 6.3 Privacy

- **No Data Collection:** No telemetry or analytics
- **No External Communication:** Fully offline operation
- **Local Processing Only:** All operations performed on-device
- **No Cloud Storage:** No backup or sync to external services

## 7. Compliance Requirements

### 7.1 Platform Compliance

#### macOS Gatekeeper

- **Requirement:** Unsigned scripts must be run via user-initiated action
- **Implementation:** Quick Action triggered by explicit user selection
- **Workaround:** Scripts installed to Application Scripts (trusted location)

#### macOS Sandboxing

- **Requirement:** Scripts in Application Scripts directory have limited access
- **Implementation:** Access only to user-selected files passed as arguments
- **Benefit:** Enhanced security without code signing

#### macOS Services

- **Requirement:** Workflows must be properly configured XML property lists
- **Implementation:** Valid Automator workflow with correct service metadata
- **Cache Management:** Services database refresh required after installation

### 7.2 Python PEP 668 Compliance

- **Requirement:** Python installations marked as "externally managed" prevent system-wide pip installs
- **Issue:** Homebrew Python on modern macOS enforces PEP 668
- **Solution:** Use `--break-system-packages` flag with fallback
- **Implementation:**
  ```bash
  python3 -m pip install --quiet --user --break-system-packages "mutagen==1.47.0" 2>/dev/null || \
      python3 -m pip install --quiet --user "mutagen==1.47.0"
  ```

### 7.3 File Format Compliance

- **ID3v2.3 Standard:** All modified files saved with ID3v2.3 tags
- **Backward Compatibility:** ID3v2.3 supported by all modern players
- **Forward Compatibility:** Can read ID3v2.4 tags but saves as v2.3
- **No ID3v1 Support:** Only processes ID3v2 frames

## 8. Known Limitations

### 8.1 Technical Limitations

1. **ID3v1 Tags:** Not supported (only ID3v2 frames processed)
2. **Encoding Detection:** Heuristic-based (requires ≥50% Cyrillic characters)
3. **Single Encoding:** Only handles CP1251 → UTF-8 conversion
4. **No Undo:** Modified files cannot be automatically reverted (no backup creation)
5. **File Access:** Requires write permissions on MP3 files

### 8.2 macOS-Specific Limitations

1. **Workflow Caching:** macOS aggressively caches Automator workflows; requires cleanup + reboot for updates
2. **Path Spaces:** Automator has special requirements for paths with spaces
3. **Services Environment:** Minimal PATH (`/usr/bin:/bin:/usr/sbin:/sbin`), requires absolute paths
4. **Cache Locations:** Multiple cache directories (Automator, automator.runner, Saved Application State)

### 8.3 Platform Limitations

1. **macOS Only:** Finder integration only available on macOS
2. **Python Version:** Requires Python 3.9+ (for type hints and modern features)
3. **Shell Dependency:** Requires Zsh (default on macOS Catalina+)

## 9. Installation Requirements

### 9.1 System Requirements

- **Operating System:** macOS 10.14+ (Mojave or later)
- **Architecture:** Universal (Apple Silicon and Intel)
- **Python:** 3.9 or later
- **Shell:** Zsh (default on macOS Catalina+)
- **Disk Space:** < 1 MB (scripts and dependencies)

### 9.2 User Requirements

- **Privileges:** Standard user (no administrator rights needed)
- **Technical Level:** Basic (can run shell scripts)
- **File Access:** Write permissions on MP3 files to be processed

### 9.3 Installation Process

1. Clone or download repository
2. Open Terminal
3. Navigate to repository directory
4. Run: `bash install.sh`
5. (Optional) Enable Quick Action in System Settings if not auto-enabled
6. (Optional) Reboot for clean Services cache

### 9.4 Troubleshooting Requirements

- **Diagnostic Tool:** `bash diagnose.sh` - Verifies installation
- **Cleanup Tool:** `bash cleanup.sh` - Complete removal
- **Log Access:** `~/Library/Logs/TranscodeTagsMP3.log` - Execution history

## 10. Testing Requirements

### 10.1 Test Coverage

- **Unit Tests:** Encoding conversion logic
- **Integration Tests:** End-to-end MP3 file processing
- **Fixture Tests:** Broken tag generation and repair verification
- **Platform Tests:** Cross-platform Python script compatibility

### 10.2 Test Execution

```bash
# Install test dependencies
pip install pytest mutagen

# Run test suite
cd transcodetagsmp3
python3 -m pytest tests/ -v
```

### 10.3 Test Cases

1. Cyrillic text round-trip conversion
2. ASCII text preservation
3. Empty string handling
4. Already-correct Unicode text (no modification)
5. Latin-1 text protection (heuristic filter)
6. MP3 files with correct tags (no changes)
7. MP3 files with broken tags (fixes applied)
8. Non-MP3 files (skipped)
9. Missing files (error handling)

## 11. Future Enhancements

### 11.1 Planned Features

- [ ] Support for additional Cyrillic encodings (KOI8-R, ISO 8859-5)
- [ ] ID3v1 tag support
- [ ] macOS Notification Center notifications on completion
- [ ] CLI flags: `--verbose`, `--quiet`, `--dry-run`
- [ ] Standalone macOS `.pkg` installer
- [ ] Code signing for Gatekeeper approval

### 11.2 Under Consideration

- [ ] Automatic backup creation before modification
- [ ] GUI application (SwiftUI or Electron)
- [ ] Batch processing progress indicator
- [ ] Support for other metadata formats (Vorbis Comments, APEv2)
- [ ] Encoding auto-detection via machine learning

### 11.3 Won't Implement

- **Audio Transcoding:** Out of scope (metadata only)
- **Cloud Sync:** Privacy and offline-first design
- **Windows/Linux Finder Integration:** Platform-specific Quick Actions not portable

## 12. Success Criteria

### 12.1 Installation Success

- [ ] `install.sh` completes without errors
- [ ] `diagnose.sh` shows all components installed correctly
- [ ] Quick Action appears in Finder context menu
- [ ] `mutagen` library successfully installed

### 12.2 Operational Success

- [ ] Selected MP3 files processed without errors
- [ ] Garbled Cyrillic text converted to readable UTF-8
- [ ] Already-correct tags remain unchanged
- [ ] Log file created with session details
- [ ] Exit code 0 for successful processing

### 12.3 Quality Success

- [ ] No audio data corruption
- [ ] No false positive conversions (Latin-1 text preserved)
- [ ] All tests pass
- [ ] No workflow configuration errors

## 13. Support and Maintenance

### 13.1 Issue Reporting

- **Platform:** GitHub Issues
- **Required Information:**
  - macOS version and architecture
  - Python version
  - Output of `diagnose.sh`
  - Contents of log file
  - Sample file (if privacy permits)

### 13.2 Common Issues

1. **"Service cannot be run"**: Workflow corrupted especiallly script part (run cleanup + reboot)
2. **"No such file or directory"**: Path quoting issue (fixed in latest version)
3. **"Files: 0"**: Wrong inputMethod in cached workflow (run cleanup + reboot)
4. **"externally-managed-environment"**: PEP 668 issue (fixed with `--break-system-packages`)

### 13.3 Maintenance Schedule

- **Dependency Updates:** Monitor mutagen releases for bug fixes
- **macOS Compatibility:** Test on new macOS versions
- **Python Compatibility:** Test with new Python versions
- **Security Patches:** Review and apply as needed

## 14. License and Legal

### 14.1 Project License

To be determined (suggest MIT or GPL-2.0 to match mutagen)

### 14.2 Third-Party Licenses

- **mutagen:** GPL-2.0 License
- **Python:** PSF License

### 14.3 Disclaimers

- Software provided "as is" without warranty
- Users responsible for backup of files before processing
- No guarantee of encoding detection accuracy (heuristic-based)

## 15. Glossary

- **ID3:** Industry-standard metadata format for MP3 files
- **CP1251:** Windows-1251 character encoding for Cyrillic text
- **Latin-1:** ISO-8859-1 character encoding for Western European languages
- **UTF-8:** Universal character encoding supporting all languages
- **Quick Action:** macOS Finder integration feature (formerly "Service")
- **Automator:** macOS visual workflow automation tool
- **Application Scripts:** Sandboxed directory for third-party scripts
- **PEP 668:** Python Enhancement Proposal for externally managed environments
- **mutagen:** Python library for reading and writing audio metadata

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-22  
**Status:** Draft
