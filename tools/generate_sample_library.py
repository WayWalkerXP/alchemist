#!/usr/bin/env python3
"""
generate_sample_library.py

Generates a synthetic audiobook test corpus for the Alchemist project.

Requirements:
    ffmpeg
    ffprobe

Run:
    python tools/generate_sample_library.py

The generated files contain only synthesized audio and generated metadata.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_ROOT = ROOT / "sample_data"
AUDIO_EXT = ".m4b"


@dataclass
class Chapter:
    title: str
    start_ms: int
    end_ms: int


@dataclass
class SampleBook:
    slug: str
    title: str
    author: str | None
    album: str | None
    series: str | None = None
    series_part: str | None = None
    asin: str | None = None
    isbn: str | None = None
    narrator: str | None = None
    folder_book: bool = False
    tracks: int = 1
    chapters: list[Chapter] = field(default_factory=list)
    legacy_series_tag: bool = False
    conflicting_folder_metadata: bool = False
    cover: bool = True
    duration_seconds: int = 12
    bitrate: str = "64k"
    channels: int = 1
    target: str = "incoming"


BOOKS = [
    SampleBook(
        slug="single_happy_path",
        title="The Test Alchemist",
        album="The Test Alchemist",
        author="Ada Example",
        series="Sample Series",
        series_part="1",
        asin="B000TEST01",
        narrator="Narrator One",
        chapters=[
            Chapter("Opening", 0, 4000),
            Chapter("Middle", 4000, 8000),
            Chapter("Ending", 8000, 12000),
        ],
    ),
    SampleBook(
        slug="folder_book_happy_path",
        title="Folder Book Example",
        album="Folder Book Example",
        author="Ada Example",
        series="Sample Series",
        series_part="2",
        asin="B000TEST02",
        folder_book=True,
        tracks=3,
    ),
    SampleBook(
        slug="missing_author",
        title="Missing Author",
        album="Missing Author",
        author=None,
        asin="B000TEST03",
    ),
    SampleBook(
        slug="legacy_series_tag",
        title="Legacy Series Tag",
        album="Legacy Series Tag",
        author="Ada Example",
        series="Legacy Saga",
        series_part="3",
        asin="B000TEST05",
        legacy_series_tag=True,
    ),
    SampleBook(
        slug="asin_duplicate_incoming",
        title="Duplicate Incoming",
        album="Duplicate Incoming",
        author="Ada Example",
        asin="B000DUP001",
        target="incoming",
    ),
    SampleBook(
        slug="asin_duplicate_library",
        title="Duplicate Incoming",
        album="Duplicate Incoming",
        author="Ada Example",
        asin="B000DUP001",
        target="abs_library",
    ),
]


def run(cmd):
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)


def require_tool(name):
    if shutil.which(name) is None:
        raise RuntimeError(f"Required tool not found: {name}")


def reset():
    if SAMPLE_ROOT.exists():
        shutil.rmtree(SAMPLE_ROOT)
    for d in ("incoming", "abs_library", "archive", "artifacts", "expected"):
        (SAMPLE_ROOT / d).mkdir(parents=True, exist_ok=True)


def metadata_file(book, path):
    lines = [";FFMETADATA1"]
    def add(k, v):
        if v:
            lines.append(f"{k}={v}")
    add("title", book.title)
    add("album", book.album)
    add("artist", book.author)
    add("album_artist", book.author)
    add("composer", book.narrator)
    add("ASIN", book.asin)
    add("ISBN", book.isbn)
    add("series", book.series)
    if book.series_part:
        add("SERIES_SEQUENCE" if book.legacy_series_tag else "series-part", book.series_part)
    for ch in book.chapters:
        lines += [
            "",
            "[CHAPTER]",
            "TIMEBASE=1/1000",
            f"START={ch.start_ms}",
            f"END={ch.end_ms}",
            f"title={ch.title}",
        ]
    path.write_text("\n".join(lines), encoding="utf-8")


def make_cover(path):
    run(["ffmpeg","-y","-f","lavfi","-i","color=c=blue:s=600x600:d=1","-frames:v","1",str(path)])


def make_audio(path, seconds, channels):
    run(["ffmpeg","-y","-f","lavfi","-i",f"sine=frequency=440:duration={seconds}","-ac",str(channels),str(path)])


def make_m4b(book, output):
    tmp = output.parent / ".tmp"
    tmp.mkdir(exist_ok=True)
    wav = tmp / "audio.wav"
    meta = tmp / "metadata.txt"
    cover = tmp / "cover.jpg"
    make_audio(wav, book.duration_seconds, book.channels)
    metadata_file(book, meta)
    cmd = ["ffmpeg","-y","-i",str(wav),"-f","ffmetadata","-i",str(meta)]
    if book.cover:
        make_cover(cover)
        cmd += ["-i",str(cover),"-map","0:a","-map","2:v","-c:v","mjpeg","-disposition:v","attached_pic"]
    else:
        cmd += ["-map","0:a"]
    cmd += ["-map_metadata","1","-c:a","aac","-b:a",book.bitrate,"-ac",str(book.channels),"-movflags","use_metadata_tags",str(output)]
    run(cmd)
    shutil.rmtree(tmp)


def write_abs_json(book, folder):
    data = {
        "title": book.album or book.title,
        "authors": [{"name": book.author}] if book.author else [],
        "series": [{"name": book.series, "sequence": book.series_part}] if book.series else [],
        "asin": book.asin,
    }
    (folder/"metadata.json").write_text(json.dumps(data, indent=2), encoding="utf-8")


def generate(book):
    base = SAMPLE_ROOT / book.target
    if book.target == "abs_library":
        folder = base / (book.author or "Unknown") / (book.series or "Standalone") / (book.album or book.title)
        folder.mkdir(parents=True, exist_ok=True)
        write_abs_json(book, folder)
        make_m4b(book, folder / f"{book.album or book.title}{AUDIO_EXT}")
    elif book.folder_book:
        folder = base / book.slug
        folder.mkdir(parents=True, exist_ok=True)
        for i in range(1, book.tracks + 1):
            b = SampleBook(**{**book.__dict__, "title": f"Chapter {i:02d}", "cover": i == 1})
            make_m4b(b, folder / f"{i:02d} - Chapter {i:02d}{AUDIO_EXT}")
    else:
        make_m4b(book, base / f"{book.slug}{AUDIO_EXT}")


def main():
    require_tool("ffmpeg")
    require_tool("ffprobe")
    reset()
    for book in BOOKS:
        generate(book)
    print(f"Generated sample library at {SAMPLE_ROOT}")


if __name__ == "__main__":
    main()
