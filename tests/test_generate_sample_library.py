from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "generate_sample_library.py"

spec = importlib.util.spec_from_file_location("generate_sample_library", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
assert spec.loader is not None
spec.loader.exec_module(module)


def test_make_m4b_uses_ffmetadata_for_metadata_input(monkeypatch, tmp_path):
    calls: list[list[str]] = []

    monkeypatch.setattr(module, "make_audio", lambda *args, **kwargs: None)
    monkeypatch.setattr(module, "make_cover", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        module,
        "metadata_file",
        lambda book, path: path.write_text(";FFMETADATA1", encoding="utf-8"),
    )
    monkeypatch.setattr(module, "run", lambda cmd: calls.append(cmd))

    book = module.SampleBook(
        slug="sample",
        title="Sample",
        author="Ada",
        album="Sample",
        cover=True,
        channels=1,
        bitrate="64k",
        duration_seconds=1,
    )

    module.make_m4b(book, tmp_path / "book.m4b")

    assert calls, "make_m4b should invoke ffmpeg"
    assert ["-f", "ffmetadata"] in [calls[0][i : i + 2] for i in range(len(calls[0]) - 1)]
    last_input_index = max(i for i, item in enumerate(calls[0]) if item == "-i")
    assert calls[0].index("-map_metadata") > last_input_index
    assert calls[0].index("-map_metadata") < calls[0].index(str(tmp_path / "book.m4b"))
    assert calls[0].index("-c:v") < calls[0].index(str(tmp_path / "book.m4b"))
    assert calls[0][calls[0].index("-c:v") + 1] == "mjpeg"
