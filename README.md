# Audiobook Converter

A safe, batch-oriented audiobook conversion utility that converts source audiobooks into optimized M4B files for an MP3Tag/Audible metadata workflow.

The converter is designed for large audiobook collections where **data preservation, chapter preservation, validation, and recoverability** are more important than raw speed.

---

# Features

## Audio Conversion

- Converts audiobooks to M4B format
- Uses FFmpeg for audio processing
- Supports any audio format FFmpeg can read
- Automatically selects the correct bitrate based on source bitrate and channel count
- Supports both:
  - Standard audiobooks (mono output)
  - GraphicAudio / Dramatic Audio productions (stereo output)

---

## Metadata Preservation

Preserves:

- Title
- Author
- Artist
- Album Artist
- Album
- Composer
- Embedded metadata
- Chapters

The converter validates that chapter counts match before archiving the original file.

---

## Automatic GraphicAudio Detection

Automatically detects dramatic audio productions using metadata and filename analysis.

Supported indicators:

- GraphicAudio
- Graphic Audio
- Dramatic Audio
- Audio Drama
- Full Cast

When detected:

- Stereo productions remain stereo
- Bitrate rules are adjusted appropriately

---

## Safe Processing

The converter is designed around a transaction model.

A file is considered complete only after:

1. Conversion succeeds
2. Validation succeeds
3. Final output is promoted
4. Original file is archived
5. Logging and counters are updated

This prevents partial processing from corrupting the workflow.

---

## Validation

After conversion the output file is validated.

Checks include:

- File exists
- File is readable
- Expected channel count
- Expected bitrate
- Duration matches source
- Chapter count matches source

If validation fails:

- Output is discarded
- Original remains untouched

---

## Cover Art Extraction

Optional sidecar cover extraction.

When enabled:

- Embedded artwork is extracted
- Saved as JPG or PNG
- Stored separately from converted files

Cover extraction failures never stop conversion.

---

## Progress Reporting

Displays live progress while processing:

```text
🏁 Progress:
10/26 processed | 16 remaining | 10 converted | 0 skipped | 0 failed
```

---

## Keyboard Controls

The converter can be controlled while running.

### Pause

Press:

```text
p
```

Current file finishes processing.

Processing pauses before the next file starts.

Resume by pressing:

```text
Enter
```

---

### Graceful Quit

Press:

```text
q
```

Current file finishes processing.

You will be prompted:

```text
Quit requested.
Do you want to stop processing now? [y/N]
```

---

### Ctrl+C

First Ctrl+C:

- Requests graceful shutdown

Second Ctrl+C:

- Immediate termination
- Best-effort cleanup of temporary files

---

## Dry Run Mode

Analyze files without modifying anything.

```bash
python audiobook_converter.py --dry-run
```

Dry run performs:

- Discovery
- Metadata analysis
- Bitrate calculations
- Filename generation
- Conversion planning

Dry run does not:

- Convert files
- Move files
- Write output files

---

# Requirements

## Python

Python 3.11 or newer

---

## FFmpeg

FFmpeg must be installed and available in PATH.

Required tools:

```text
ffmpeg
ffprobe
```

---

## Python Packages

Install dependencies:

```bash
pip install colorama
```

---

# Installation

Clone the repository:

```bash
git clone https://github.com/yourname/audiobook-converter.git

cd audiobook-converter
```

Install dependencies:

```bash
pip install -r requirements.txt
```

or

```bash
pip install colorama
```

---

# Configuration

The converter uses an INI configuration file.

Default:

```text
audiobook_converter.ini
```

Alternative:

```bash
python audiobook_converter.py --config myconfig.ini
```

---

## First Run

If the configuration file does not exist:

1. The converter launches an interactive setup wizard
2. Prompts for configuration values
3. Displays the resulting configuration
4. Allows confirmation before saving

If rejected:

- A blank template configuration is created
- The program exits

---

# Example Configuration

```ini
[paths]
source_dir = /data/incoming
target_dir = /data/mp3tag
converted_dir = /data/originals

[encoding]
max_bitrate = 64
codec = libfdk_aac
fallback_codec = aac

[general]
log_file = audiobook_converter.log

[display]
use_color = true
use_emoji = true

[artwork]
extract_cover = true
cover_dir = /data/covers

[reporting]
run_history_csv = audiobook_converter_runs.csv
```

---

# Directory Workflow

Input:

```text
source_dir/
```

Converted files:

```text
target_dir/
```

Archived originals:

```text
converted_dir/
```

Optional cover art:

```text
cover_dir/
```

---

# Bitrate Rules

Before any decision is made, source bitrate is normalized to the nearest 8 kbps.

Examples:

```text
127 -> 128
126 -> 128
65  -> 64
63  -> 64
```

---

## Standard Audiobooks

### Stereo / Multi-Channel

| Source Bitrate | Output |
|--------------|--------|
| >=128 kbps | 64 kbps mono |
| 64-127 kbps | bitrate / 2 mono |
| <64 kbps | skipped |

### Mono

| Source Bitrate | Output |
|--------------|--------|
| <32 kbps | skipped |
| 32-63 kbps | preserve bitrate |
| >=64 kbps | 64 kbps mono |

---

## GraphicAudio / Dramatic Audio

Only applies to stereo or multi-channel source files.

| Source Bitrate | Output |
|--------------|--------|
| >=128 kbps | 128 kbps stereo |
| <128 kbps | 64 kbps stereo |

Mono dramatic-audio files use the normal mono rules.

---

# Output Naming

Preferred format:

```text
Author - Title.m4b
```

Author lookup order:

1. artist
2. album_artist
3. author
4. composer

Title lookup order:

1. title
2. album
3. original filename

Example:

```text
Craig Alanson - Columbus Day.m4b
```

---

# Logging

All activity is logged.

Includes:

- Startup
- Shutdown
- File discovery
- Bitrate decisions
- Validation results
- Conversion results
- Errors
- Warnings
- Summary statistics

---

# Run History CSV

A persistent CSV history file is maintained.

One row is appended per run.

Columns:

| Column | Description |
|----------|-------------|
| date | Run date |
| time | Run start time |
| numBooksProcessed | Successfully converted books |
| numBytesOriginal | Total original size |
| numBytesAfterConversion | Total converted size |
| numBytesDiff | Space saved |
| pctDiff | Percent reduction |
| runTime | Total runtime |

Example:

```csv
date,time,numBooksProcessed,numBytesOriginal,numBytesAfterConversion,numBytesDiff,pctDiff,runTime
2026-05-31,18:32:14,25,18765432123,9123456789,9641975334,51.38,00:22:18
```

---

# Error Handling

The converter is designed to continue processing whenever possible.

A failure in one file:

- Does not stop the batch
- Is logged
- Leaves the original untouched

The only condition that stops the batch immediately is:

```text
Disk space exhaustion
```

---

# Safety Guarantees

The converter will:

✅ Preserve chapters

✅ Preserve metadata

✅ Validate output before archiving originals

✅ Never overwrite existing outputs

✅ Never delete originals

✅ Continue after file-level failures

✅ Support graceful shutdown

---

# License

- GPLv3
For more information, refer to LICENSE file.

---

# Acknowledgements

Built with:

- Python
- FFmpeg
- FFprobe
- Colorama

Designed for large audiobook collections and metadata-driven workflows.
