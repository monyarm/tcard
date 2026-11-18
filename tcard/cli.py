"""argv to card on stdout."""

from __future__ import annotations

import argparse
import sys

from . import __version__, config
from .errors import TcardError
from .names import normalize
from .render.layout import layout
from .render.text import render
from .sources import registry

EXIT_OK = 0
EXIT_NO_MATCH = 1
EXIT_USAGE = 2


def split_terms(terms: list[str], systems: list[str], kinds: list[str]) -> tuple[str, str | None, str]:
    rest = list(terms)
    system = registry.resolve(systems[0]) if systems else "dnd:5e"
    if rest:
        token = rest[0]
        if registry.resolve(token) in registry.SYSTEMS:
            system = registry.resolve(token)
            rest.pop(0)
        elif ":" in token and token.split(":", 1)[0] in registry.families():
            known = ", ".join(registry.names()) or "none"
            raise TcardError(f"unknown system {token!r} (known: {known})", EXIT_USAGE)
    if not kinds:
        try:
            kinds = list(registry.kinds(system))
        except KeyError:
            kinds = []
    kind = rest.pop(0) if rest and rest[0] in kinds else None
    name = " ".join(rest).strip()
    if not name:
        raise TcardError("missing card name", EXIT_USAGE)
    return system, kind, name


def find(records: list[dict], name: str) -> list[dict]:
    wanted = name.casefold()
    names = [str(record.get("name", "")).casefold() for record in records]
    exact = [record for record, candidate in zip(records, names) if candidate == wanted]
    if exact:
        return exact
    return [record for record, candidate in zip(records, names) if candidate.startswith(wanted)]


def pick(matches: list[dict], prefer: list[str], source: str | None) -> dict | None:
    if not matches:
        return None
    if source:
        return next((record for record in matches if record.get("source") == source), None)
    order = {code: index for index, code in enumerate(prefer)}
    return min(matches, key=lambda record: (order.get(str(record.get("source")), len(order)), str(record.get("source"))))


def _report(lines: list[str], stream) -> None:
    print("\n".join(lines), file=stream)


def _run(args) -> int:
    cfg = config.load()
    if args.cols is not None:
        cfg.cols = args.cols
    if not 8 <= cfg.cols <= 200:
        raise TcardError(f"cols must be between 8 and 200, got {cfg.cols}", EXIT_USAGE)

    system, kind, name = split_terms(args.terms, cfg.systems, cfg.kinds)
    try:
        available = registry.kinds(system)
    except KeyError:
        raise TcardError(f"unknown system {system!r}", EXIT_USAGE) from None

    order = [kind] if kind else [item for item in cfg.kinds if item in available] or list(available)
    for item in order:
        if item not in available:
            raise TcardError(f"unknown kind {item!r} for {system}", EXIT_USAGE)

    records = {item: available[item].records(refresh=args.refresh) for item in order}
    wanted = normalize(name)

    if args.all:
        found = [(item, record) for item in order for record in available[item].matches(records[item], name)]
        if not found:
            raise TcardError(f"no match for {name!r}", EXIT_NO_MATCH)
        _report(_candidate_lines(found, available), sys.stdout)
        return EXIT_OK

    pool: list[dict] = []
    chosen = ""
    for item in order:
        hits = [record for record in records[item] if available[item].key(record) == wanted]
        if hits:
            pool, chosen = hits, item
            break

    if not pool:
        hits = [(item, record) for item in order for record in available[item].matches(records[item], name)]
        distinct = {available[item].display(record).casefold() for item, record in hits}
        if not distinct:
            raise TcardError(f"no match for {name!r}", EXIT_NO_MATCH)
        if len(distinct) > 1:
            _report([f"tcard: {name!r} is ambiguous:"] + _candidate_lines(hits, available), sys.stderr)
            return EXIT_NO_MATCH
        pool = [record for _, record in hits]
        chosen = hits[0][0]

    record = pick(pool, cfg.prefer, args.source)
    if record is None:
        if args.source:
            raise TcardError(f"no {name!r} in source {args.source}", EXIT_NO_MATCH)
        raise TcardError(f"no match for {name!r}", EXIT_NO_MATCH)

    card = available[chosen].card(record)
    try:
        lines = layout(card, cfg.cols, args.brief)
    except ValueError as exc:
        raise TcardError(str(exc), EXIT_USAGE) from exc
    sys.stdout.write(render(lines))
    return EXIT_OK


def _candidate_lines(pairs, available) -> list[str]:
    lines = []
    for item, record in pairs:
        source = record.get("source")
        suffix = f", {source}" if source else ""
        lines.append(f"  {available[item].display(record)} ({item}{suffix})")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tcard", description="Print tabletop cards for a thermal printer.")
    parser.add_argument(
        "terms",
        nargs="*",
        metavar="[SYSTEM] [KIND] NAME",
        help="e.g. dnd:5e spell fireball, dnd:5e fireball, fireball",
    )
    parser.add_argument("--source", help="prefer this book code, e.g. PHB")
    parser.add_argument("--cols", type=int, help="card width in characters (default 32)")
    parser.add_argument("--brief", action="store_true", help="header and fields only")
    parser.add_argument("--all", action="store_true", help="list every match instead of printing one")
    parser.add_argument("--refresh", action="store_true", help="refetch the 5e.tools snapshot")
    parser.add_argument("--version", action="version", version=f"tcard {__version__}")
    args = parser.parse_intermixed_args(argv)

    try:
        return _run(args)
    except config.ConfigError as exc:
        print(f"tcard: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except TcardError as exc:
        print(f"tcard: {exc}", file=sys.stderr)
        return exc.exit_code
