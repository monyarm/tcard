"""Local web UI: browse the registry, preview a card, print it with tp."""

from __future__ import annotations

import argparse
import json
import mimetypes
import secrets
import signal
import sys
import threading
import webbrowser
from collections import OrderedDict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse

from .. import config
from . import data, print as printing, serve

STATIC = Path(__file__).resolve().parent / "static"
KEY_COOKIE = "tcard_key"
ACCESS_KEY = ""
VIEW_ONLY = False
DRY_RUN = False
_CARDS: "OrderedDict[tuple, str]" = OrderedDict()
_CARDS_LOCK = threading.Lock()


def _cards_cache(system: str, kind: str, name: str, source: str, cols: int,
                 brief: bool) -> str:
    key = (system, kind, name, source, cols, brief)
    with _CARDS_LOCK:
        hit = _CARDS.get(key)
        if hit is not None:
            _CARDS.move_to_end(key)
            return hit
    text = printing.card_text(system, kind, name, source, cols, brief)
    with _CARDS_LOCK:
        _CARDS[key] = text
        while len(_CARDS) > 64:
            _CARDS.popitem(last=False)
    return text


def _filters(query: dict[str, list[str]]) -> dict[str, list[str]]:
    reserved = {"system", "kind", "q", "name", "source", "cols", "brief", "offset",
                "limit", "k"}
    out = {}
    for key, values in query.items():
        if key in reserved:
            continue
        joined = ",".join(values)
        picked = [value.strip() for value in joined.split(",") if value.strip()]
        if picked:
            out[key] = picked
    return out


def _card(query: dict[str, list[str]]) -> dict:
    system = _one(query, "system")
    kind = _one(query, "kind")
    name = _one(query, "name")
    if not name:
        raise printing.PrintError("missing card name", 2)
    cols = int(_one(query, "cols") or 32)
    text = _cards_cache(system, kind, name, _one(query, "source"), cols,
                        _one(query, "brief").lower() in ("1", "true", "on"))
    return {"text": text, "lines": text.count("\n"), "cols": cols}


def _one(query: dict[str, list[str]], key: str) -> str:
    values = query.get(key) or [""]
    return values[0].strip()


class Handler(BaseHTTPRequestHandler):
    server_version = "tcard-web"

    def log_message(self, *args) -> None:  # quiet; the UI is local
        pass

    # -- responses ---------------------------------------------------------
    def _send(self, status: int, body: bytes, kind: str = "application/json",
              extra: dict[str, str] | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload: dict, status: int = 200) -> None:
        self._send(status, json.dumps(payload).encode("utf-8"))

    def _error(self, status: int, message: str) -> None:
        self._json({"error": message}, status)

    # -- auth --------------------------------------------------------------
    def _key_ok(self) -> bool:
        if not ACCESS_KEY:
            return True
        cookie = self.headers.get("Cookie", "")
        return any(part.split("=", 1) == [KEY_COOKIE, ACCESS_KEY]
                   for part in cookie.split("; ") if "=" in part)

    def _login(self) -> bool:
        """Accept ?k=… once, then keep it in a cookie."""
        given = _one(parse_qs(urlparse(self.path).query), "k")
        if given and secrets.compare_digest(given, ACCESS_KEY):
            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Set-Cookie",
                             f"{KEY_COOKIE}={ACCESS_KEY}; HttpOnly; SameSite=Lax; Path=/")
            rest = urlparse(self.path).path or "/"
            self.send_header("Location", rest)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return True
        return False

    def _denied(self) -> None:
        page = ("<!doctype html><meta charset=utf-8><title>tcard</title>"
                "<body style='font:16px system-ui;margin:3rem;max-width:30rem'>"
                "<h1>tcard</h1><p>This card printer needs the key it was shared with.</p>"
                "<form><input name=k placeholder='access key' autofocus "
                "style='font:16px monospace;padding:.5rem;width:100%'>"
                "<button style='margin-top:.5rem;padding:.5rem 1rem'>open</button>"
                "</form></body>")
        self._send(HTTPStatus.UNAUTHORIZED, page.encode("utf-8"), "text/html; charset=utf-8")

    def _guard(self) -> bool:
        if self._login():
            return False
        if not self._key_ok():
            self._denied()
            return False
        return True

    # -- routes ------------------------------------------------------------
    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if self._login():
            return
        if path.startswith("/static/") or path == "/":
            if not self._key_ok():
                self._denied()
                return
            self._static(path)
            return
        if not self._guard():
            return
        query = parse_qs(urlparse(self.path).query)
        try:
            if path == "/api/systems":
                self._json({"systems": data.systems()})
            elif path == "/api/index":
                system, kind = _one(query, "system"), _one(query, "kind")
                if not system or not kind:
                    raise printing.PrintError("system and kind are required", 2)
                if system not in data.registry.SYSTEMS:
                    raise printing.PrintError(f"unknown system {system!r}", 1)
                if kind not in data.registry.kinds(system):
                    raise printing.PrintError(f"unknown kind {kind!r} for {system}", 1)
                refresh = _one(query, "refresh").lower() in ("1", "true", "on")
                if refresh:
                    with _CARDS_LOCK:
                        _CARDS.clear()
                self._json(data.search(system, kind, _one(query, "q"), _filters(query),
                                       int(_one(query, "offset") or 0),
                                       int(_one(query, "limit") or data.LIMIT),
                                       refresh=refresh))
            elif path == "/api/card":
                self._json(_card(query))
            elif path == "/api/health":
                self._json({"tcard": True, "tp": printing.tp_binary(),
                            "shared": bool(ACCESS_KEY), "view_only": VIEW_ONLY,
                            "dry_run": DRY_RUN, "cols": data.COLUMNS})
            else:
                self._error(HTTPStatus.NOT_FOUND, f"no route {path}")
        except KeyError as exc:
            self._error(HTTPStatus.NOT_FOUND, f"unknown system or kind {exc.args[0]!r}")
        except printing.PrintError as exc:
            self._error(_status(exc.code), str(exc))
        except ValueError as exc:
            self._error(HTTPStatus.BAD_REQUEST, str(exc))

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if not self._guard():
            return
        if path != "/api/print":
            self._error(HTTPStatus.NOT_FOUND, f"no route {path}")
            return
        if VIEW_ONLY:
            self._error(HTTPStatus.FORBIDDEN, "this server is view-only")
            return
        length = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
            query = {key: [str(value)] for key, value in body.items()}
            card = _card(query)
            sent = printing.print_card(card["text"], dry_run=DRY_RUN)
            self._json({"ok": True, "text": card["text"], "lines": card["lines"],
                        "tp": sent.get("tp", ""), "dry_run": DRY_RUN})
        except printing.PrintError as exc:
            self._error(_status(exc.code), str(exc))
        except (json.JSONDecodeError, ValueError, KeyError) as exc:
            self._error(HTTPStatus.BAD_REQUEST, f"bad request: {exc}")

    def _static(self, path: str) -> None:
        name = "index.html" if path == "/" else path.removeprefix("/static/")
        target = (STATIC / name).resolve()
        if STATIC.resolve() not in target.parents or not target.is_file():
            self._error(HTTPStatus.NOT_FOUND, f"no file {name}")
            return
        body = target.read_bytes()
        kind = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if kind.startswith("text/") or kind in ("application/javascript",):
            kind += "; charset=utf-8"
        self._send(HTTPStatus.OK, body, kind)


def _status(code: int) -> int:
    if code == 2:
        return HTTPStatus.BAD_REQUEST
    if code == 3:
        return HTTPStatus.BAD_GATEWAY
    return HTTPStatus.NOT_FOUND


def main(argv: list[str] | None = None) -> int:
    global ACCESS_KEY, VIEW_ONLY, DRY_RUN
    parser = argparse.ArgumentParser(prog="tcard web", description="Browse and print cards in a browser.")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--cols", type=int, default=config.load().cols)
    parser.add_argument("--serve", nargs="?", const="auto", metavar="HOW",
                        help="share it: auto, tailscale, funnel, cloudflare[:name]")
    parser.add_argument("--key", help="access key for shared mode (random when omitted)")
    parser.add_argument("--view-only", action="store_true", help="disable printing")
    parser.add_argument("--dry-run", action="store_true", help="render without sending to tp")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    if not 8 <= args.cols <= 200:
        print("tcard web: cols must be between 8 and 200", file=sys.stderr)
        return 2
    data.COLUMNS = args.cols
    VIEW_ONLY = args.view_only
    DRY_RUN = args.dry_run
    if args.serve:
        ACCESS_KEY = args.key or secrets.token_urlsafe(9)

    try:
        httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    except OSError as exc:
        print(f"tcard web: cannot listen on {args.host}:{args.port}: {exc}", file=sys.stderr)
        return 3

    local = f"http://{args.host}:{args.port}/"
    tunnel = None
    try:
        if args.serve:
            tunnel = serve.start(args.serve, args.port)
            if tunnel.url:
                link = f"{tunnel.url}/?k={quote(ACCESS_KEY)}"
                print(f"tcard web: shared at {link}", flush=True)
                print(f"tcard web: {serve.advise(tunnel)}", flush=True)
            else:
                print(f"tcard web: tunnel started ({tunnel.note})", flush=True)
            print(f"tcard web: access key {ACCESS_KEY}", flush=True)
        print(f"tcard web: {local}", flush=True)
        if not args.no_browser:
            threading.Timer(0.4, webbrowser.open, (local,)).start()
        # SIGTERM must unwind through the finally block, or the tunnel child
        # process is left running after the server is gone.
        signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt))
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    except serve.ServeError as exc:
        print(f"tcard web: {exc}", file=sys.stderr)
        return 3
    finally:
        # serve_forever already stopped (signal, interrupt or failure); closing
        # the socket is what is left. shutdown() would block here forever.
        httpd.server_close()
        if tunnel is not None:
            tunnel.stop()
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
