"""Run the CLI for a card and hand its output to the printer.

The CLI stays the only renderer: this module never builds a Card. It shells out
to `python3 -m tcard`, then pipes that exact stdout into `tp`, so the browser
preview and the paper agree byte for byte.
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import threading

ROOT = pathlib.Path(__file__).resolve().parents[2]
TIMEOUT = 240
_LOCK = threading.Lock()


class PrintError(Exception):
    def __init__(self, message: str, code: int = 1):
        super().__init__(message)
        self.code = code


def tp_binary() -> str | None:
    return shutil.which("tp")


def argv(system: str, kind: str, name: str, source: str = "", cols: int = 32,
         brief: bool = False) -> list[str]:
    command = [sys.executable, "-m", "tcard", system, kind, name, "--cols", str(cols)]
    if source:
        command += ["--source", source]
    if brief:
        command.append("--brief")
    return command


def card_text(system: str, kind: str, name: str, source: str = "", cols: int = 32,
              brief: bool = False) -> str:
    """The card exactly as the CLI prints it."""
    if not 8 <= cols <= 200:
        raise PrintError(f"cols must be between 8 and 200, got {cols}", 2)
    try:
        done = subprocess.run(argv(system, kind, name, source, cols, brief),
                              cwd=ROOT, capture_output=True, timeout=TIMEOUT)
    except FileNotFoundError as exc:  # no python? then nothing works
        raise PrintError(str(exc), 3) from exc
    except subprocess.TimeoutExpired as exc:
        raise PrintError(f"tcard timed out after {TIMEOUT}s", 3) from exc
    if done.returncode:
        message = done.stderr.decode("utf-8", "replace").strip() or "tcard failed"
        raise PrintError(message.splitlines()[-1], done.returncode)
    return done.stdout.decode("utf-8", "replace")


def print_card(text: str, dry_run: bool = False) -> dict:
    """Send `text` to tp's stdin. One job at a time; tp streams pages itself."""
    printer = tp_binary()
    if dry_run:
        return {"ok": True, "dry_run": True, "tp": printer, "text": text}
    if not printer:
        raise PrintError("tp not found on PATH", 3)
    with _LOCK:
        try:
            done = subprocess.run([printer], input=text.encode("utf-8"),
                                  capture_output=True, timeout=TIMEOUT)
        except subprocess.TimeoutExpired as exc:
            raise PrintError(f"tp timed out after {TIMEOUT}s", 3) from exc
    error = done.stderr.decode("utf-8", "replace").strip()
    if done.returncode:
        raise PrintError(error or f"tp exited {done.returncode}", done.returncode)
    return {"ok": True, "tp": printer, "stderr": error, "text": text}
