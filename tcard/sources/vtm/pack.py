"""Foundry V5 compendium pack: the full book text for a power or ritual.

The VTM Wiki only carries a one-line `Effect` per power, so the card body comes
from a community compendium published as a Foundry pack. Foundry stores packs
as LevelDB tables (`.ldb`), which this module reads directly: a tiny SSTable
reader plus snappy, no third-party dependency.
"""

from __future__ import annotations

import html
import json
import re
import struct

from ...errors import TcardError
from ...names import normalize
from . import cache

# Pinned commit, so a later rewrite of the repository cannot change the text.
REPO = "DeathDaisy/daisys-complete-foundry-wod5e-compository"
SHA = "8c735d0c6c84a033cb17d92f903178506f9084ce"
PACK = f"https://raw.githubusercontent.com/{REPO}/{SHA}/packs/disciplines/000028.ldb"

# The pack's own discipline keys differ from the wiki's page names.
DISCIPLINES = {
    "blood sorcery": "sorcery",
    "blood sorcery rituals": "rituals",
    "thin-blood alchemy": "alchemy",
    "thin blood alchemy": "alchemy",
    "oblivion ceremonies": "ceremonies",
}
# Pack labels that mean the same thing, or fit 32 columns better.
FIELD_NAMES = {
    "dice pools": "Pool",
    "dice pool": "Pool",
    "opposing pool": "Opposing",
    "opposing pools": "Opposing",
    "prerequisite power": "Prerequisite",
    "prerequisites": "Prerequisite",
    "pre-required power": "Prerequisite",
    "pre required power": "Prerequisite",
    "ingredient": "Ingredients",
    "activation cost": "Activation",
}
# The pack was converted from the PDFs, and that conversion left a space
# inside a word wherever the print broke one across a line, and dropped the
# hyphens of compound words. These are all of them in the pinned pack; the
# pin means the list cannot go stale under us.
SPLITS = {
    "ad dition": "addition",
    "aggres sive": "aggressive",
    "alche mist": "alchemist",
    "al lows": "allows",
    "ani malism": "animalism",
    "animal ism": "animalism",
    "any thing": "anything",
    "apart ment": "apartment",
    "approxi mately": "approximately",
    "at tention": "attention",
    "at tempting": "attempting",
    "automat ed": "automated",
    "automati cally": "automatically",
    "be comes": "becomes",
    "beck oning": "beckoning",
    "break ing": "breaking",
    "bul lets": "bullets",
    "burn ing": "burning",
    "capa ble": "capable",
    "circum stances": "circumstances",
    "claw ing": "clawing",
    "cold hearted": "cold-hearted",
    "com mand": "command",
    "com munication": "communication",
    "com pletely": "completely",
    "com posure": "composure",
    "communi cate": "communicate",
    "cre ates": "creates",
    "dam age": "damage",
    "de fense": "defense",
    "depend ing": "depending",
    "dex terity": "dexterity",
    "distilla tion": "distillation",
    "emo tional": "emotional",
    "en trancement": "entrancement",
    "equiva lent": "equivalent",
    "exam ple": "example",
    "fa ade": "facade",
    "feed ing": "feeding",
    "for titude": "fortitude",
    "forget ful": "forgetful",
    "giv ing": "giving",
    "hart shorn": "hartshorn",
    "hazard ous": "hazardous",
    "heartrend ingly": "heartrendingly",
    "in creases": "increases",
    "in dividual": "individual",
    "in doors": "indoors",
    "in juries": "injuries",
    "in telligence": "intelligence",
    "infor mation": "information",
    "inflec tions": "inflections",
    "involv ing": "involving",
    "leth argy": "lethargy",
    "look ing": "looking",
    "man age": "manage",
    "meaning fully": "meaningfully",
    "melan cholic": "melancholic",
    "mis leading": "misleading",
    "mix ture": "mixture",
    "neces sarily": "necessarily",
    "necessi tate": "necessitate",
    "nega tive": "negative",
    "non consenting": "non-consenting",
    "non verbally": "nonverbally",
    "of ten": "often",
    "op ponent": "opponent",
    "physi cal": "physical",
    "post hypnotic": "post-hypnotic",
    "pres ence": "presence",
    "pro foundly": "profoundly",
    "re solve": "resolve",
    "receiv ing": "receiving",
    "requir ing": "requiring",
    "return ing": "returning",
    "ro bustly": "robustly",
    "scar city": "scarcity",
    "semi permeable": "semipermeable",
    "signal ing": "signaling",
    "single mindedly": "single-mindedly",
    "slim mest": "slimmest",
    "some thing": "something",
    "sor cery": "sorcery",
    "story teller": "storyteller",
    "storytell ers": "storytellers",
    "stub bornness": "stubbornness",
    "sub dermal": "subdermal",
    "sub ject": "subject",
    "sub merged": "submerged",
    "subter fuge": "subterfuge",
    "success es": "successes",
    "suit able": "suitable",
    "super natural": "supernatural",
    "sur rounds": "surrounds",
    "sur vives": "survives",
    "them selves": "themselves",
    "they ve": "they've",
    "total ing": "totaling",
    "un der": "under",
    "un natural": "unnatural",
    "un observed": "unobserved",
    "un til": "until",
    "unex pectedly": "unexpectedly",
    "vam pire": "vampire",
    "vam pires": "vampires",
    "with out": "without",
}
_PAIR = re.compile("|".join(re.escape(broken) for broken in SPLITS), re.I)
_MARK = re.compile(r"^\u25a0\s*([^:]{2,40}):\s*(.*)$", re.S)
_PARA = re.compile(r"<p\b[^>]*>(.*?)</p>", re.S | re.I)
_BREAK = re.compile(r"<br\s*/?>", re.I)
_TAG = re.compile(r"<[^>]+>")
_ITEMS: list[dict] | None = None
_INDEX: dict | None = None
_BY_NAME: dict[str, dict] | None = None


def _snappy(data: bytes) -> bytes:
    """Snappy raw block decompression (varint length, then literal/copy tags)."""
    pos = 0

    def varint() -> int:
        nonlocal pos
        shift = result = 0
        while True:
            byte = data[pos]
            pos += 1
            result |= (byte & 0x7F) << shift
            if not byte & 0x80:
                return result
            shift += 7

    length = varint()
    out = bytearray()
    while pos < len(data) and len(out) < length:
        tag = data[pos]
        pos += 1
        kind = tag & 3
        if kind == 0:
            size = (tag >> 2) + 1
            if size > 60:
                extra = size - 60
                size = int.from_bytes(data[pos:pos + extra], "little") + 1
                pos += extra
            out += data[pos:pos + size]
            pos += size
            continue
        if kind == 1:
            size = ((tag >> 2) & 7) + 4
            offset = ((tag >> 5) << 8) | data[pos]
            pos += 1
        elif kind == 2:
            size = (tag >> 2) + 1
            offset = int.from_bytes(data[pos:pos + 2], "little")
            pos += 2
        else:
            size = (tag >> 2) + 1
            offset = int.from_bytes(data[pos:pos + 4], "little")
            pos += 4
        if offset <= 0 or offset > len(out):
            raise ValueError("corrupt snappy block")
        for _ in range(size):
            out.append(out[-offset])
    return bytes(out[:length])


def _varint(buf: bytes, pos: int) -> tuple[int, int]:
    shift = result = 0
    while True:
        byte = buf[pos]
        pos += 1
        result |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return result, pos
        shift += 7


def _block(buf: bytes, offset: int, length: int) -> bytes:
    raw = buf[offset:offset + length]
    return _snappy(raw) if buf[offset + length] == 1 else raw


def entries(data: bytes):
    """Key/value pairs of one SSTable data or index block."""
    count = struct.unpack("<I", data[-4:])[0]
    end = len(data) - 4 - 4 * count
    pos = 0
    key = b""
    while pos < end:
        shared, pos = _varint(data, pos)
        non_shared, pos = _varint(data, pos)
        value_len, pos = _varint(data, pos)
        key = key[:shared] + data[pos:pos + non_shared]
        pos += non_shared
        value = data[pos:pos + value_len]
        pos += value_len
        yield key, value


def read_pack(raw: bytes):
    """Every entry of an SSTable, walking its block index."""
    if raw[-8:] != b"\x57\xfb\x80\x8b\x24\x75\x47\xdb":
        raise ValueError("not an sstable")
    pos = 0
    _, pos = _varint(raw[-48:], pos)   # metaindex offset
    _, pos = _varint(raw[-48:], pos)   # metaindex length
    index_offset, pos = _varint(raw[-48:], pos)
    index_length, pos = _varint(raw[-48:], pos)
    for _, handle in entries(_block(raw, index_offset, index_length)):
        offset, at = _varint(handle, 0)
        length, _ = _varint(handle, at)
        yield from entries(_block(raw, offset, length))


def _repair(line: str) -> str:
    """Undo the PDF conversion's broken words, keeping the line's own case."""
    def join(match: re.Match) -> str:
        whole = SPLITS[match.group(0).lower()]
        return whole[:1].upper() + whole[1:] if match.group(0)[:1].isupper() else whole

    return _PAIR.sub(join, line)


def _clean(chunk: str) -> list[str]:
    chunk = _BREAK.sub("\n", chunk)
    text = html.unescape(_TAG.sub("", chunk)).replace("\xa0", " ")
    # `◻` marks a rules bullet and is sometimes inlined without a break.
    text = text.replace("\u25fb", "\n\u25fb")
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.split("\n")]
    return [_repair(line) for line in lines if line]


def details(markup: str) -> dict:
    """Split one `system.description` into prose lines and labelled fields."""
    prose: list[str] = []
    fields: dict[str, str] = {}
    label = ""
    for chunk in _PARA.findall(markup) or [markup]:
        label = ""
        for line in _clean(chunk):
            if line.lower().startswith("source:"):
                continue
            # `◻` marks the rules list inside System; keep it as a bullet.
            line = line.replace("\u25fb ", "- ").replace("\u25fb", "- ")
            match = _MARK.match(line)
            if match:
                label = match.group(1).strip()
                label = FIELD_NAMES.get(label.lower(), label)
                value = match.group(2).strip()
                if not value or label in fields:
                    label = ""
                    continue
                if label == "Pool" and " vs " in value:
                    # `Intelligence + Auspex vs Composure + Subterfuge` is two fields.
                    pool, opposing = value.split(" vs ", 1)
                    fields["Pool"] = pool.strip()
                    fields.setdefault("Opposing", opposing.strip())
                else:
                    fields[label] = value
                continue
            if label and line.startswith("- "):
                # The bullets under System belong to it, not to the prose.
                fields[label] = f"{fields[label]}\n{line}"
                continue
            label = ""
            prose.append(line)
    return {"prose": prose, "fields": fields}


def body_lines(label: str, value: str) -> list[str]:
    """`System: text` plus its `- ` sub-bullets, one card line each."""
    parts = value.split("\n")
    return [f"{label}: {parts[0]}", *(part for part in parts[1:] if part.strip())]


def items(refresh: bool = False) -> list[dict]:
    global _ITEMS
    if refresh or _ITEMS is None:
        try:
            raw = cache.get_bytes(PACK, refresh)
            _ITEMS = [json.loads(value) for _, value in read_pack(raw)
                      if value.startswith(b"{")]
        except (TcardError, ValueError, KeyError):
            # No pack means shorter cards, not a failed command.
            _ITEMS = []
    return _ITEMS


def _discipline(name: object) -> str:
    text = normalize(str(name or ""))
    return DISCIPLINES.get(text, text.replace(" ", "_"))


def _name_key(name: object) -> str:
    """`The Gift of False Life` and `Gift of False Life` are the same power."""
    text = normalize(str(name or ""))
    return text[4:] if text.startswith("the ") else text


def index(refresh: bool = False) -> tuple[dict, dict]:
    global _INDEX, _BY_NAME
    if refresh or _INDEX is None or _BY_NAME is None:
        by_key: dict = {}
        by_name: dict = {}
        for item in items(refresh):
            system = item.get("system") or {}
            if item.get("type") != "power" or not system.get("description"):
                continue
            by_key.setdefault((_discipline(system.get("discipline")), _name_key(item.get("name"))), item)
            by_name.setdefault(_name_key(item.get("name")), item)
        _INDEX, _BY_NAME = by_key, by_name
    return _INDEX, _BY_NAME


def lookup(name: str, discipline: object = None) -> dict | None:
    """Full text of one power, or None when the pack does not list it."""
    by_key, by_name = index()
    key = _name_key(name)
    item = by_key.get((_discipline(discipline), key)) if discipline else None
    item = item or by_name.get(key)
    if item is None:
        return None
    return details(str(item["system"]["description"]))
