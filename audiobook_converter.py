#!/usr/bin/env python3
"""Safely convert audiobook files to M4B for an MP3Tag staging workflow.

The converter intentionally favors clear, explicit control flow over compact code.
It scans every file in the configured source tree, asks ffprobe whether the file is
readable media, applies conservative bitrate rules, converts with FFmpeg, validates
that the output is usable, and only then archives the original file.
"""

from __future__ import annotations

import argparse
import configparser
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from colorama import Fore, Style, init as colorama_init

CONFIG_FILE = "audiobook_converter.ini"
LOCK_FILE = "audiobook_converter.lock"
METADATA_KEYS = ("artist", "album_artist", "author", "composer", "title", "album")
INVALID_FILENAME_CHARS = '<>:"/\\|?*\0'
WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}


class ConfigError(Exception):
    """Raised when the INI configuration is missing or invalid."""


class LockError(Exception):
    """Raised when another converter instance already owns the lock file."""


class ProbeError(Exception):
    """Raised when ffprobe cannot read or describe a media file."""


@dataclass(frozen=True)
class AppConfig:
    """Validated application configuration loaded from the INI file."""

    source_dir: Path
    target_dir: Path
    converted_dir: Path
    max_bitrate_kbps: int
    preferred_codec: str
    fallback_codec: str
    log_file: Path
    use_color: bool
    use_emoji: bool


@dataclass(frozen=True)
class AudioInfo:
    """Relevant ffprobe data for a source or output audiobook file."""

    path: Path
    bitrate_bps: int
    channels: int
    codec: str
    duration_seconds: float
    chapter_count: int
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def bitrate_kbps(self) -> int:
        """Return the bitrate rounded to the nearest whole kilobit per second."""

        return round(self.bitrate_bps / 1000)


@dataclass(frozen=True)
class ConversionPlan:
    """All derived decisions needed to convert one source file."""

    source_path: Path
    final_path: Path
    temporary_path: Path
    archive_path: Path
    target_bitrate_kbps: int
    codec: str


@dataclass
class ProcessingStats:
    """Counters displayed in the final summary."""

    scanned: int = 0
    converted: int = 0
    skipped: int = 0
    failed: int = 0


class ConfigManager:
    """Load and validate configuration from audiobook_converter.ini."""

    REQUIRED_SECTIONS = ("paths", "encoding", "general", "display")

    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path

    def load(self) -> AppConfig:
        """Read, validate, and normalize the INI configuration."""

        if not self.config_path.exists():
            raise ConfigError(f"Configuration file not found: {self.config_path}")

        parser = configparser.ConfigParser()
        parser.read(self.config_path)

        for section in self.REQUIRED_SECTIONS:
            if section not in parser:
                raise ConfigError(f"Missing required configuration section: [{section}]")

        source_dir = self._required_path(parser, "paths", "source_dir")
        target_dir = self._required_path(parser, "paths", "target_dir")
        converted_dir = self._required_path(parser, "paths", "converted_dir")
        log_file = Path(self._required_value(parser, "general", "log_file")).expanduser().resolve()

        max_bitrate_kbps = parser.getint("encoding", "max_bitrate", fallback=64)
        if max_bitrate_kbps <= 0:
            raise ConfigError("[encoding] max_bitrate must be greater than zero")

        preferred_codec = self._required_value(parser, "encoding", "codec")
        fallback_codec = self._required_value(parser, "encoding", "fallback_codec")
        use_color = parser.getboolean("display", "use_color", fallback=True)
        use_emoji = parser.getboolean("display", "use_emoji", fallback=True)

        for directory in (source_dir, target_dir, converted_dir):
            directory.mkdir(parents=True, exist_ok=True)
            if not directory.is_dir():
                raise ConfigError(f"Configured path is not a directory: {directory}")

        # A staging or archive directory inside the source tree can cause the
        # converter to discover its own outputs on later runs, so fail early.
        for derived_dir, label in ((target_dir, "target_dir"), (converted_dir, "converted_dir")):
            if derived_dir == source_dir or source_dir in derived_dir.parents:
                raise ConfigError(f"[paths] {label} must not be inside source_dir")

        log_file.parent.mkdir(parents=True, exist_ok=True)

        return AppConfig(
            source_dir=source_dir,
            target_dir=target_dir,
            converted_dir=converted_dir,
            max_bitrate_kbps=max_bitrate_kbps,
            preferred_codec=preferred_codec,
            fallback_codec=fallback_codec,
            log_file=log_file,
            use_color=use_color,
            use_emoji=use_emoji,
        )

    def _required_value(self, parser: configparser.ConfigParser, section: str, key: str) -> str:
        value = parser.get(section, key, fallback="").strip()
        if not value:
            raise ConfigError(f"Missing required configuration value: [{section}] {key}")
        return value

    def _required_path(self, parser: configparser.ConfigParser, section: str, key: str) -> Path:
        return Path(self._required_value(parser, section, key)).expanduser().resolve()


class ConsoleDisplay:
    """Centralized color and emoji handling for console output."""

    EMOJIS = {
        "scan": "🔍",
        "convert": "🎧",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
        "archive": "📦",
        "summary": "🏁",
    }

    def __init__(self, use_color: bool, use_emoji: bool) -> None:
        self.use_color = use_color
        self.use_emoji = use_emoji
        colorama_init(autoreset=True, strip=not use_color)

    def info(self, message: str, emoji: str | None = None) -> None:
        self._write(message, Fore.WHITE + Style.BRIGHT, emoji)

    def success(self, message: str) -> None:
        self._write(message, Fore.WHITE + Style.BRIGHT, "success")

    def warning(self, message: str) -> None:
        self._write(message, Fore.YELLOW, "warning")

    def error(self, message: str) -> None:
        self._write(message, Fore.RED, "error", stream=sys.stderr)

    def summary(self, message: str) -> None:
        self._write(message, Fore.WHITE + Style.BRIGHT, "summary")

    def _write(self, message: str, color: str, emoji: str | None, stream: Any = sys.stdout) -> None:
        prefix = ""
        if self.use_emoji and emoji:
            prefix = f"{self.EMOJIS.get(emoji, emoji)} "
        if self.use_color:
            print(f"{color}{prefix}{message}{Style.RESET_ALL}", file=stream)
        else:
            print(f"{prefix}{message}", file=stream)


class LockFile:
    """Small cross-platform lock file based on exclusive file creation."""

    def __init__(self, lock_path: Path) -> None:
        self.lock_path = lock_path
        self._fd: int | None = None

    def acquire(self) -> None:
        """Create the lock file or raise LockError if it already exists."""

        try:
            self._fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(self._fd, f"pid={os.getpid()}\n".encode("utf-8"))
        except FileExistsError as exc:
            raise LockError(f"Another instance appears to be running: {self.lock_path}") from exc

    def release(self) -> None:
        """Close and remove the lock file, ignoring cleanup failures."""

        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
        try:
            self.lock_path.unlink(missing_ok=True)
        except OSError:
            logging.exception("Failed to remove lock file: %s", self.lock_path)

    def __enter__(self) -> "LockFile":
        self.acquire()
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.release()


class FFmpegAnalyzer:
    """Wrapper around ffprobe and FFmpeg capability checks."""

    def available_audio_encoders(self) -> set[str]:
        """Return the set of audio encoder names reported by FFmpeg."""

        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg -encoders failed: {result.stderr.strip()}")

        encoders: set[str] = set()
        for line in result.stdout.splitlines():
            # Encoder rows look like: " A..... aac                  AAC ...".
            stripped = line.strip()
            if not stripped or len(stripped) < 8:
                continue
            flags = stripped.split(maxsplit=1)[0]
            if flags.startswith("A") and len(stripped.split()) >= 2:
                encoders.add(stripped.split()[1])
        return encoders

    def probe(self, path: Path) -> AudioInfo:
        """Analyze a file with ffprobe and return normalized audio information."""

        command = [
            "ffprobe",
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            "-show_chapters",
            str(path),
        ]
        result = subprocess.run(command, text=True, capture_output=True, check=False)
        if result.returncode != 0:
            raise ProbeError(result.stderr.strip() or "ffprobe failed")

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise ProbeError("ffprobe returned invalid JSON") from exc

        audio_stream = self._primary_audio_stream(data)
        if audio_stream is None:
            raise ProbeError("ffprobe found no audio stream")

        bitrate_bps = self._extract_bitrate(data, audio_stream)
        if bitrate_bps is None or bitrate_bps <= 0:
            raise ProbeError("audio bitrate could not be determined")

        channels = self._safe_int(audio_stream.get("channels"), default=0)
        if channels <= 0:
            raise ProbeError("channel count could not be determined")

        duration_seconds = self._extract_duration(data, audio_stream)
        if duration_seconds <= 0:
            raise ProbeError("duration could not be determined")

        return AudioInfo(
            path=path,
            bitrate_bps=bitrate_bps,
            channels=channels,
            codec=str(audio_stream.get("codec_name", "unknown")),
            duration_seconds=duration_seconds,
            chapter_count=len(data.get("chapters", [])),
            metadata=self._extract_metadata(data, audio_stream),
        )

    def _primary_audio_stream(self, data: dict[str, Any]) -> dict[str, Any] | None:
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "audio":
                return stream
        return None

    def _extract_bitrate(self, data: dict[str, Any], audio_stream: dict[str, Any]) -> int | None:
        for value in (audio_stream.get("bit_rate"), data.get("format", {}).get("bit_rate")):
            bitrate = self._safe_int(value, default=0)
            if bitrate > 0:
                return bitrate
        return None

    def _extract_duration(self, data: dict[str, Any], audio_stream: dict[str, Any]) -> float:
        for value in (audio_stream.get("duration"), data.get("format", {}).get("duration")):
            try:
                duration = float(value)
            except (TypeError, ValueError):
                continue
            if duration > 0:
                return duration
        return 0.0

    def _extract_metadata(self, data: dict[str, Any], audio_stream: dict[str, Any]) -> dict[str, str]:
        metadata: dict[str, str] = {}
        combined_tags: dict[str, Any] = {}
        combined_tags.update(audio_stream.get("tags", {}))
        combined_tags.update(data.get("format", {}).get("tags", {}))

        casefolded_tags = {str(key).casefold(): str(value).strip() for key, value in combined_tags.items()}
        for key in METADATA_KEYS:
            value = casefolded_tags.get(key.casefold(), "")
            if value:
                metadata[key] = value
        return metadata

    def _safe_int(self, value: Any, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default


class ConversionPlanner:
    """Apply filename, duplicate, and bitrate rules for a source file."""

    def __init__(self, config: AppConfig, codec: str) -> None:
        self.config = config
        self.codec = codec

    def create_plan(self, source_info: AudioInfo) -> ConversionPlan | None:
        """Return a conversion plan, or None when bitrate rules require a skip."""

        target_bitrate_kbps = self._target_bitrate(source_info)
        if target_bitrate_kbps is None:
            return None

        output_name = self._output_filename(source_info)
        final_path = self.config.target_dir / output_name
        temporary_path = final_path.with_name(f"{final_path.stem}.tmp{final_path.suffix}")
        archive_path = self.config.converted_dir / source_info.path.relative_to(self.config.source_dir)

        return ConversionPlan(
            source_path=source_info.path,
            final_path=final_path,
            temporary_path=temporary_path,
            archive_path=archive_path,
            target_bitrate_kbps=target_bitrate_kbps,
            codec=self.codec,
        )

    def _target_bitrate(self, source_info: AudioInfo) -> int | None:
        source_kbps = source_info.bitrate_kbps
        max_bitrate = self.config.max_bitrate_kbps

        if source_info.channels > 1:
            if source_kbps >= 128:
                return min(64, max_bitrate)
            if source_kbps >= 64:
                return min(max(round(source_kbps / 2), 1), max_bitrate)
            return None

        if source_kbps < 32:
            return None
        if source_kbps < 64:
            return min(source_kbps, max_bitrate)
        return min(64, max_bitrate)

    def _output_filename(self, source_info: AudioInfo) -> str:
        metadata = source_info.metadata
        author = self._first_metadata_value(metadata, ("artist", "album_artist", "author", "composer"))
        title = self._first_metadata_value(metadata, ("title", "album"))

        if not author:
            author = "Unknown Author"
        if not title:
            title = source_info.path.stem

        return f"{sanitize_filename(author)} - {sanitize_filename(title)}.m4b"

    def _first_metadata_value(self, metadata: dict[str, str], keys: tuple[str, ...]) -> str:
        for key in keys:
            value = metadata.get(key, "").strip()
            if value:
                return value
        return ""


class ValidationManager:
    """Validate converted M4B files before originals are archived."""

    BITRATE_TOLERANCE_RATIO = 0.20
    DURATION_TOLERANCE_SECONDS = 2.0
    DURATION_TOLERANCE_RATIO = 0.01

    def __init__(self, analyzer: FFmpegAnalyzer) -> None:
        self.analyzer = analyzer

    def validate(self, source_info: AudioInfo, plan: ConversionPlan, output_path: Path) -> bool:
        """Return True when the converted file satisfies all critical checks."""

        if not output_path.exists():
            logging.error("Validation failed; output file does not exist: %s", output_path)
            return False

        try:
            output_info = self.analyzer.probe(output_path)
        except ProbeError as exc:
            logging.error("Validation failed; output is not readable: %s", exc)
            return False

        if output_info.channels != 1:
            logging.error("Validation failed; expected mono audio, found %s channel(s)", output_info.channels)
            return False

        if not self._bitrate_matches(output_info.bitrate_bps, plan.target_bitrate_kbps * 1000):
            logging.error(
                "Validation failed; expected approximately %s kbps, found %s kbps",
                plan.target_bitrate_kbps,
                output_info.bitrate_kbps,
            )
            return False

        if not self._duration_matches(source_info.duration_seconds, output_info.duration_seconds):
            logging.error(
                "Validation failed; source duration %.2fs differs from output duration %.2fs",
                source_info.duration_seconds,
                output_info.duration_seconds,
            )
            return False

        if output_info.chapter_count != source_info.chapter_count:
            logging.error(
                "Validation failed; source has %s chapter(s), output has %s chapter(s)",
                source_info.chapter_count,
                output_info.chapter_count,
            )
            return False

        self._warn_about_missing_metadata(source_info, output_info)
        logging.info("Validation successful: %s", output_path)
        return True

    def _bitrate_matches(self, actual_bps: int, expected_bps: int) -> bool:
        tolerance = max(5_000, round(expected_bps * self.BITRATE_TOLERANCE_RATIO))
        return abs(actual_bps - expected_bps) <= tolerance

    def _duration_matches(self, source_seconds: float, output_seconds: float) -> bool:
        tolerance = max(self.DURATION_TOLERANCE_SECONDS, source_seconds * self.DURATION_TOLERANCE_RATIO)
        return abs(source_seconds - output_seconds) <= tolerance

    def _warn_about_missing_metadata(self, source_info: AudioInfo, output_info: AudioInfo) -> None:
        for key, source_value in source_info.metadata.items():
            if source_value and not output_info.metadata.get(key):
                logging.warning("Metadata appears missing in output: %s", key)


class AudiobookConverter:
    """Coordinate discovery, analysis, conversion, validation, and archiving."""

    def __init__(
        self,
        config: AppConfig,
        display: ConsoleDisplay,
        analyzer: FFmpegAnalyzer,
        planner: ConversionPlanner,
        validator: ValidationManager,
        dry_run: bool,
    ) -> None:
        self.config = config
        self.display = display
        self.analyzer = analyzer
        self.planner = planner
        self.validator = validator
        self.dry_run = dry_run
        self.stats = ProcessingStats()

    def run(self) -> ProcessingStats:
        """Process every regular file below source_dir and return final counters."""

        logging.info("Starting audiobook conversion; dry_run=%s", self.dry_run)
        for path in self._discover_files():
            self.stats.scanned += 1
            self._process_one_file(path)
        logging.info("Finished audiobook conversion")
        return self.stats

    def _discover_files(self) -> list[Path]:
        logging.info("Discovering files under %s", self.config.source_dir)
        return sorted(path for path in self.config.source_dir.rglob("*") if path.is_file())

    def _process_one_file(self, path: Path) -> None:
        self.display.info(f"Scanning: {path.name}", "scan")
        logging.info("Discovered file: %s", path)

        try:
            source_info = self.analyzer.probe(path)
            logging.info(
                "Probe result for %s: bitrate=%s kbps, channels=%s, codec=%s, duration=%.2f, chapters=%s",
                path,
                source_info.bitrate_kbps,
                source_info.channels,
                source_info.codec,
                source_info.duration_seconds,
                source_info.chapter_count,
            )
        except ProbeError as exc:
            self._skip(f"Skipped: {path.name} ({exc})")
            logging.warning("Skipping unreadable or unsupported file %s: %s", path, exc)
            return
        except Exception:
            self._fail(f"Failed: unexpected ffprobe error for {path.name}")
            logging.exception("Unexpected probe error for %s", path)
            return

        plan = self.planner.create_plan(source_info)
        if plan is None:
            self._skip(f"Skipped: bitrate below threshold ({source_info.bitrate_kbps} kbps)")
            logging.warning("Skipping %s because bitrate is below threshold", path)
            return

        logging.info(
            "Bitrate decision for %s: source=%s kbps, target=%s kbps",
            path,
            source_info.bitrate_kbps,
            plan.target_bitrate_kbps,
        )

        if plan.final_path.exists():
            self._skip(f"Skipped: output already exists ({plan.final_path.name})")
            logging.warning("Skipping %s because output already exists: %s", path, plan.final_path)
            return

        if self.dry_run:
            self._describe_dry_run(source_info, plan)
            return

        self._convert_validate_and_archive(source_info, plan)

    def _describe_dry_run(self, source_info: AudioInfo, plan: ConversionPlan) -> None:
        self.display.info(f"Would convert: {plan.source_path.name} -> {plan.final_path}", "convert")
        self.display.info(f"Would use codec {plan.codec} at {plan.target_bitrate_kbps} kbps mono")
        self.display.info(f"Would validate duration, bitrate, mono audio, and {source_info.chapter_count} chapter(s)")
        self.display.info(f"Would archive original to: {plan.archive_path}", "archive")
        logging.info("Dry run plan: %s", plan)

    def _convert_validate_and_archive(self, source_info: AudioInfo, plan: ConversionPlan) -> None:
        self.display.info(f"Converting: {plan.final_path.name}", "convert")
        logging.info("Converting %s to temporary output %s", plan.source_path, plan.temporary_path)

        plan.temporary_path.unlink(missing_ok=True)
        command = self._ffmpeg_command(plan)
        result = subprocess.run(command, text=True, capture_output=True, check=False)
        if result.returncode != 0:
            plan.temporary_path.unlink(missing_ok=True)
            self._fail("Failed: ffmpeg returned non-zero exit code")
            logging.error("FFmpeg failed for %s: %s", plan.source_path, result.stderr.strip())
            return

        logging.info("FFmpeg conversion completed for %s", plan.source_path)
        if not self.validator.validate(source_info, plan, plan.temporary_path):
            plan.temporary_path.unlink(missing_ok=True)
            self._fail("Failed: validation failed")
            return

        try:
            self._promote_temporary_output(plan)
            logging.info("Promoted temporary output to final output: %s", plan.final_path)
        except OSError:
            plan.temporary_path.unlink(missing_ok=True)
            self._fail("Failed: could not promote temporary output")
            logging.exception("Could not promote %s to %s", plan.temporary_path, plan.final_path)
            return

        try:
            self._archive_original(plan)
        except OSError:
            self._fail("Failed: could not archive original after conversion")
            logging.exception("Could not archive original %s to %s", plan.source_path, plan.archive_path)
            return

        self.stats.converted += 1
        self.display.success("Conversion successful")
        self.display.info("Archived original", "archive")
        logging.info("Conversion and archive successful for %s", plan.source_path)

    def _promote_temporary_output(self, plan: ConversionPlan) -> None:
        """Move the validated temporary file into place without overwriting.

        The temporary and final files live in the same directory, so a hard link is
        a safe way to create the final path with O_EXCL-like behavior.  If the
        final path appeared after duplicate planning, os.link fails instead of
        replacing someone else's file.
        """

        os.link(plan.temporary_path, plan.final_path)
        plan.temporary_path.unlink()

    def _ffmpeg_command(self, plan: ConversionPlan) -> list[str]:
        return [
            "ffmpeg",
            "-hide_banner",
            "-y",
            "-i",
            str(plan.source_path),
            "-map",
            "0:a:0",
            "-map_metadata",
            "0",
            "-map_chapters",
            "0",
            "-vn",
            "-ac",
            "1",
            "-c:a",
            plan.codec,
            "-b:a",
            f"{plan.target_bitrate_kbps}k",
            "-f",
            "mp4",
            str(plan.temporary_path),
        ]

    def _archive_original(self, plan: ConversionPlan) -> None:
        if plan.archive_path.exists():
            raise FileExistsError(f"Archive destination already exists: {plan.archive_path}")
        plan.archive_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(plan.source_path), str(plan.archive_path))
        logging.info("Archived original to %s", plan.archive_path)

    def _skip(self, message: str) -> None:
        self.stats.skipped += 1
        self.display.warning(message)

    def _fail(self, message: str) -> None:
        self.stats.failed += 1
        self.display.error(message)


def sanitize_filename(value: str) -> str:
    """Remove characters that are invalid or troublesome on Windows/Linux."""

    cleaned = "".join(" " if char in INVALID_FILENAME_CHARS else char for char in value)
    cleaned = " ".join(cleaned.split()).strip(" .")
    if not cleaned:
        cleaned = "Untitled"
    if cleaned.upper() in WINDOWS_RESERVED_NAMES:
        cleaned = f"{cleaned}_"
    return cleaned[:180]


def choose_codec(analyzer: FFmpegAnalyzer, config: AppConfig, display: ConsoleDisplay) -> str:
    """Select the configured encoder, falling back only when necessary."""

    encoders = analyzer.available_audio_encoders()
    if config.preferred_codec in encoders:
        logging.info("Using configured codec: %s", config.preferred_codec)
        return config.preferred_codec

    warning = f"Configured codec {config.preferred_codec!r} is unavailable; trying fallback {config.fallback_codec!r}"
    display.warning(warning)
    logging.warning(warning)

    if config.fallback_codec in encoders:
        logging.info("Using fallback codec: %s", config.fallback_codec)
        return config.fallback_codec

    raise ConfigError(
        f"Neither configured codec {config.preferred_codec!r} nor fallback codec "
        f"{config.fallback_codec!r} is available in FFmpeg"
    )


def configure_logging(log_file: Path) -> None:
    """Configure file logging for all application activity."""

    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )


def format_elapsed(seconds: float) -> str:
    """Format elapsed seconds as HH:MM:SS."""

    total_seconds = int(round(seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert audiobook files to validated M4B outputs.")
    parser.add_argument("--dry-run", action="store_true", help="Analyze and display actions without modifying files.")
    parser.add_argument("--no-color", action="store_true", help="Disable colored console output.")
    parser.add_argument("--no-emoji", action="store_true", help="Disable emoji output.")
    return parser.parse_args(argv)


def print_summary(display: ConsoleDisplay, stats: ProcessingStats, elapsed: str) -> None:
    """Display and log the final summary report."""

    lines = [
        "Processing Complete",
        f"Files Scanned: {stats.scanned}",
        f"Converted: {stats.converted}",
        f"Skipped: {stats.skipped}",
        f"Failed: {stats.failed}",
        f"Elapsed Time: {elapsed}",
    ]
    display.summary(lines[0])
    for line in lines[1:]:
        display.info(line)
    logging.info("Summary: %s", "; ".join(lines))


def main(argv: list[str] | None = None) -> int:
    """Program entry point."""

    args = parse_args(argv if argv is not None else sys.argv[1:])
    start_time = time.monotonic()
    repo_cwd = Path.cwd()

    try:
        config = ConfigManager(repo_cwd / CONFIG_FILE).load()
        use_color = config.use_color and not args.no_color
        use_emoji = config.use_emoji and not args.no_emoji
        display = ConsoleDisplay(use_color=use_color, use_emoji=use_emoji)
        configure_logging(config.log_file)
        logging.info("Startup complete; configuration loaded from %s", repo_cwd / CONFIG_FILE)

        with LockFile(repo_cwd / LOCK_FILE):
            analyzer = FFmpegAnalyzer()
            codec = choose_codec(analyzer, config, display)
            planner = ConversionPlanner(config, codec)
            validator = ValidationManager(analyzer)
            converter = AudiobookConverter(config, display, analyzer, planner, validator, args.dry_run)
            stats = converter.run()
            print_summary(display, stats, format_elapsed(time.monotonic() - start_time))
            logging.info("Shutdown complete")
            return 0 if stats.failed == 0 else 1

    except LockError as exc:
        ConsoleDisplay(use_color=not args.no_color, use_emoji=not args.no_emoji).error(str(exc))
        return 1
    except ConfigError as exc:
        ConsoleDisplay(use_color=not args.no_color, use_emoji=not args.no_emoji).error(str(exc))
        return 1
    except FileNotFoundError as exc:
        ConsoleDisplay(use_color=not args.no_color, use_emoji=not args.no_emoji).error(
            f"Required executable not found: {exc.filename}"
        )
        return 1
    except KeyboardInterrupt:
        ConsoleDisplay(use_color=not args.no_color, use_emoji=not args.no_emoji).warning("Interrupted by user")
        logging.warning("Interrupted by user")
        return 130
    except Exception:
        ConsoleDisplay(use_color=not args.no_color, use_emoji=not args.no_emoji).error("Unexpected fatal error; see log for details")
        logging.exception("Unexpected fatal error")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
