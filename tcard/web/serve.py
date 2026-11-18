"""Expose the local server to other devices: tailscale serve/funnel or cloudflared.

The HTTP server always stays on loopback; these only put a proxy in front of it,
so nothing is bound to a network interface and nothing prints without a key.
"""

from __future__ import annotations

import json
import re
import select
import shutil
import subprocess
import sys
import time

URL = re.compile(r"https://[A-Za-z0-9-]+\.(?:trycloudflare\.com|ts\.net)")


class ServeError(Exception):
    pass


class Tunnel:
    def __init__(self, url: str = "", process: subprocess.Popen | None = None,
                 note: str = ""):
        self.url = url
        self.process = process
        self.note = note

    def stop(self) -> None:
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()

    def close(self) -> None:
        self.stop()


def _run(command: list[str]) -> str:
    try:
        done = subprocess.run(command, capture_output=True, timeout=60)
    except FileNotFoundError as exc:
        raise ServeError(f"{command[0]} not found on PATH") from exc
    if done.returncode:
        message = done.stderr.decode("utf-8", "replace").strip()
        first = next((line for line in message.splitlines() if line.strip()),
                     f"{' '.join(command)} exited {done.returncode}")
        if "serve config denied" in message or "Access denied" in message:
            first += " (run: sudo tailscale set --operator=$USER)"
        raise ServeError(first)
    return done.stdout.decode("utf-8", "replace")


def tailscale_name() -> str:
    data = json.loads(_run(["tailscale", "status", "--json"]) or "{}")
    name = str(data.get("Self", {}).get("DNSName", "")).rstrip(".")
    if not name:
        raise ServeError("tailscale has no DNS name yet (is the tailnet up?)")
    return name


def tailscale(port: int, funnel: bool = False) -> Tunnel:
    """Serve on the tailnet (or the public internet with funnel)."""
    if shutil.which("tailscale") is None:
        raise ServeError("tailscale not found on PATH")
    command = ["tailscale", "funnel" if funnel else "serve", "--bg", str(port)]
    _run(command)
    note = "" if funnel else "tailnet only"
    return Tunnel(f"https://{tailscale_name()}", note=note)


def _cloudflared_url(process: subprocess.Popen, seconds: float = 25.0) -> str:
    deadline = time.monotonic() + seconds
    assert process.stdout is not None
    buffer = ""
    while time.monotonic() < deadline:
        ready, _, _ = select.select([process.stdout], [], [], 0.5)
        if not ready:
            if process.poll() is not None:
                break
            continue
        # Unbuffered pipe: reading a character at a time through a buffered
        # reader leaves the rest in Python's buffer, where select cannot see it.
        chunk = process.stdout.read(4096)
        if not chunk:
            break
        buffer += chunk.decode("utf-8", "replace")
        found = URL.search(buffer)
        if found:
            return found.group(0)
    message = buffer.strip().splitlines()[-1] if buffer.strip() else "no tunnel URL"
    raise ServeError(f"cloudflared gave no public URL ({message})")


def cloudflare(port: int, name: str = "") -> Tunnel:
    """A quick trycloudflare.com URL, or a named tunnel when one is given."""
    binary = shutil.which("cloudflared")
    if binary is None:
        raise ServeError("cloudflared not found on PATH (nix shell -p cloudflared)")
    if name:
        process = subprocess.Popen([binary, "tunnel", "run", name],
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return Tunnel("", process, note=f"tunnel {name}")
    process = subprocess.Popen([binary, "tunnel", "--url", f"http://127.0.0.1:{port}"],
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0)
    try:
        url = _cloudflared_url(process)
    except Exception:
        process.terminate()
        raise
    return Tunnel(url, process, note="quick tunnel, new URL each start")


def start(how: str, port: int) -> Tunnel:
    mode, _, name = how.partition(":")
    mode = mode or "auto"
    if mode == "auto":
        mode = "tailscale" if shutil.which("tailscale") else "cloudflare"
    if mode == "tailscale":
        return tailscale(port)
    if mode == "funnel":
        return tailscale(port, funnel=True)
    if mode == "cloudflare":
        return cloudflare(port, name)
    raise ServeError(f"unknown --serve mode {how!r} (auto, tailscale, funnel, cloudflare)")


def advise(tunnel: Tunnel) -> str:
    if tunnel.note:
        return tunnel.note
    return "signed in devices only" if "ts.net" in tunnel.url else "anyone with the link"


if __name__ == "__main__":  # pragma: no cover - manual check
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    how = sys.argv[2] if len(sys.argv) > 2 else "auto"
    print(start(how, port).url)
