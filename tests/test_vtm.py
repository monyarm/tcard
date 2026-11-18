"""VTM cards: disciplines, clans, merits, rituals, loresheets, no network."""

import unittest.mock as mock

from tcard.render.layout import layout
from tcard.render.text import render
from tcard.sources.vtm import (
    cache, clans, disciplines, advantages, loresheets, pack, predators, rituals,
)

DISC_INDEX = """## The Disciplines

| Discipline | Description | Clan |
| --- | --- | --- |
| [![Image 1: Auspex icon.png](https://x/Auspex_icon.png)](https://vtm.paradoxwikis.com/index.php?title=File:Auspex_icon.png&filetimestamp=1)**[Auspex](https://vtm.paradoxwikis.com/Auspex "Auspex")** | Perception | Malkavian |
| [![Image 2: Oblivion icon.png](https://x/Oblivion_icon.png)](https://vtm.paradoxwikis.com/index.php?title=File:Oblivion_icon.png&filetimestamp=1)**[Oblivion](https://vtm.paradoxwikis.com/Oblivion "Oblivion")** | Death | Hecata |
"""

AUSPEX = """Markdown Content:
Auspex

_**Voyeurism, Scrying, Anima Visus**_

**Clan affinity:**

* * *

**Type:**Mental

* * *

**Masquerade threat:**Low

* * *

**Resonance:**Phlegmatic

Considered a potent double sword, Auspex sifts truth from lies.

## List of available powers

### Level 1

| Name | Effect | Cost | Prerequisite | Amalgam | Duration | Dice pool | Opposing pool | Additional Notes | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Heightened Senses** | Enhance vampiric senses. | Free | None | No | Until Deactivated | Wits + Resolve | N/A | - | [![Image](x)](y) |

### Level 3

| Name | Effect | Cost | Prerequisite | Amalgam | Duration | Dice pool | Opposing pool | Additional Notes | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Scry the Soul**[Errata](https://x) | Read a mind. | One Rouse Check | None | No | One turn | Intelligence + Auspex | Composure + Subterfuge | - | [![Image](x)](y) |

## Other Amalgams
"""

OBLIVION_DISC = """Markdown Content:
Oblivion

_**The Abyss**_

**Type:**Mental

**Masquerade threat:**High

**Resonance:**Sanguine

## List of available powers

### Level 1

| Name | Effect | Cost | Prerequisite | Amalgam | Duration | Dice pool | Opposing pool | Additional Notes | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Shadow Cloak** | Wrap yourself in shadow. | Free | None | No | One scene | Resolve + Oblivion | N/A | - | [![Image](x)](y) |
"""

CLAN_INDEX = """## The main clans

[](https://vtm.paradoxwikis.com/index.php?title=File:Brujah_icon.png&filetimestamp=1)**[Brujah](https://vtm.paradoxwikis.com/Brujah "Brujah")**

Fighters against the system.

## Clanless

[](https://vtm.paradoxwikis.com/File:Caitiff_icon.png)**[Caitiff](https://vtm.paradoxwikis.com/Caitiff "Caitiff")**

Clanless and curse-less.
"""

BRUJAH = """Markdown Content:
Brujah

Rebels against injustice.

## Disciplines

*   **Celerity** allows the Brujah to strike fast.
*   **Potence** gives them the strength behind their attacks.
*   **Presence** is never the last resort with a Brujah.

## Bane

**Violent Temper** - A rage is simmering in the back of the mind. [[3]](https://x)

## Variant Bane

**Violence** - When a messy critical occurs. Superficial.Errata

## Compulsion

**Rebellion** - The Brujah craves to take a stance against the status quo.

## Example archetypes

*   **Undead Activist** - Death didn't stop this Kindred.
"""

ADVANTAGES = """## Merits and Flaws

### Looks

| Merits | Dot Value | Description | Flaws | Dot Value | Description |
| --- | --- | --- | --- | --- | --- |
| **Beautiful** | **••** | Add one die to related Social pools. | **Ugly** | **(•)** | Lose one die from related Social pools. |
|  |  |  | **Repulsive** | **(••)** | Lose two dice from related Social pools. |

### Linguistics

| Merits | Dot Value | Description | Flaws | Dot Value | Description |
| --- | --- | --- | --- | --- | --- |
| **Linguistics** | **• +** | Speak another language. |  |  |  |

## Backgrounds and Flaws

### Allies

| Merits | Dot Value | Description |
| --- | --- | --- |
| **Allies** | **•** | Backgrounds are not merits. |

### Mask

| Merits | Dot Value | Description | Flaws | Dot Value | Description |
| --- | --- | --- | --- | --- | --- |
| **Mask** | **• - ••** | A fake identity. |  |  |  |
| **Zeroed** | **•** | Purged from the world. |  |  |  |
"""

PREDATOR = """Markdown Content:
Each vampire has their preferred method.

## Alleycat

Alleycats are a vampire who feeds by brute force.

*   Gain one specialty in Brawl (Grappling)
*   Gain one dot of either [Celerity](https://x) or [Potence](https://x)

## Bagger

Baggers drink stored blood.

*   Gain one specialty in Streetwise (Black Market)
"""

BLOOD_SORCERY = """### Level 1

| Name | Effect | Cost | Origin | Ritual Roll | Additional Notes | Source |
| --- | --- | --- | --- | --- | --- | --- |
| **Astromancy** | Read the stars. | One Rouse Check | Tremere | Intelligence + Blood Sorcery | Requires a clear sky. | [![Image](x)](y) |
"""

OBLIVION = """### Level 2

| Name | Effect | Cost | Pre-requisite | Ritual Roll | Additional Notes | Source |
| --- | --- | --- | --- | --- | --- | --- |
| **Gift of False Life** | Raise a corpse. | One Rouse Check | Ashes to Ashes | Resolve + Oblivion | - | [![Image](x)](y) |
"""

LORESHEET_INDEX = """A '''loresheet''' is a special type of Advantage.

==Vampire: The Masquerade==
===[[Vampire: The Masquerade 5th Edition Corebook|Corebook]]===
*[[Bahari#Loresheet|The Bahari]]
*[[Theo Bell#Loresheet|Theo Bell]]

==See Also==
"""

BAHARI = """== Overview ==
The Bahari are cultists of pain.

=== Loresheet ===
* {{Dot|1}} '''Dangerous Reputation:''' Bahari intimidate vampires.
* {{Dot|2}} '''Ritual Scarification:''' Gain a dot of Fortitude.
* {{Dot|3}} '''Blood and Faith:''' Spend a Rouse Check.{{cn}}

== References ==
"""

PAGES = {
    disciplines.INDEX: DISC_INDEX,
    "Auspex": AUSPEX,
    "Oblivion": OBLIVION_DISC,
    clans.INDEX: CLAN_INDEX,
    "Brujah": BRUJAH,
    advantages.INDEX: ADVANTAGES,
    predators.INDEX: PREDATOR,
    "Blood_Sorcery_Rituals": BLOOD_SORCERY,
    "Oblivion_Ceremonies": OBLIVION,
}

WIKI = {loresheets.INDEX: LORESHEET_INDEX, "Bahari": BAHARI}

# The compendium pack carries the book text; the wiki keeps the one-liners.
PACK = {
    ("auspex", "scry the soul"): {
        "prose": ["By focusing on a person, the vampire can perceive the state "
                  "of that person's psyche as a shifting aura of colors."],
        "fields": {
            "Cost": "One Rouse Check",
            "Pool": "Intelligence + Auspex",
            "Opposing": "Composure + Subterfuge",
            "Duration": "One turn, or Story teller's discretion",
            "System": "Make an Intelligence + Auspex vs Composure + Subterfuge roll.\n"
                      "- The emotional state of the subject\n"
                      "- The Resonance of their Blood",
        },
    },
    ("ceremonies", "gift of false life"): {
        "prose": [],
        "fields": {
            "Prerequisite": "Ashes to Ashes",
            "Ingredients": "A human body.",
            "Process": "Apply the concoction to the corpse.",
            "System": "Raise a number of corpses equal to their Oblivion rating.",
        },
    },
}


def _lookup(name, discipline=None):
    """Same order as the real lookup: discipline-qualified, then name only."""
    key = name.lower().removeprefix("the ")
    exact = PACK.get((str(discipline or "").lower(), key))
    return exact or next((value for (_, power), value in PACK.items() if power == key), None)


# The advantages and clans packs: the wiki keeps a clause, the pack the page.
FEATURES = {
    "beautiful": {"prose": ["You add one extra die to all appropriate Social "
                            "dice pools, as your appearance is striking."],
                  "fields": {}},
}
CLAN_TEXT = {"brujah": ["The dream of the learned clan is a world where all "
                        "injustice has been eliminated."]}


def _feature(name):
    return FEATURES.get(name.lower().removeprefix("the "))


def _clan(name):
    return CLAN_TEXT.get(name.lower(), [])


def _page(name, refresh=False):
    return PAGES[name]


def _wikitext(name, refresh=False):
    return WIKI[name]


def _get(url, refresh=False):
    return '{"query": {"categorymembers": []}}'


def _with_pages(call):
    with mock.patch.object(cache, "page", _page), mock.patch.object(cache, "wikitext", _wikitext), \
            mock.patch.object(cache, "get", _get), \
            mock.patch.object(pack, "lookup", _lookup), \
            mock.patch.object(pack, "feature", _feature), \
            mock.patch.object(pack, "clan", _clan):
        return call()


def _rendered(card):
    return render(layout(card, 32))


def test_discipline_card():
    record = next(r for r in _with_pages(disciplines.records) if "levels" in r)
    card = disciplines.to_card(record)
    assert card.title == "Auspex"
    assert card.subtitle == "Voyeurism, Scrying, Anima Visus"
    assert dict(card.fields) == {"Type": "Mental", "Masquerade threat": "Low", "Resonance": "Phlegmatic"}
    headings = [heading for heading, _ in card.sections]
    assert headings == ["Level 1", "Level 3"]
    assert card.sections[0][1][0].startswith("- Heightened Senses: Enhance vampiric senses")


def test_discipline_power_by_path():
    records = _with_pages(disciplines.records)
    matches = disciplines.DisciplineKind().matches(records, "auspex:scry the soul")
    assert len(matches) == 1
    card = _with_pages(lambda: disciplines.to_card(matches[0]))
    assert card.title == "Scry the Soul"
    assert card.subtitle == "Auspex " + "\u25cf" * 3
    fields = dict(card.fields)
    assert fields["Cost"] == "One Rouse Check"
    assert fields["Pool"] == "Intelligence + Auspex"
    assert fields["Opposing"] == "Composure + Subterfuge"
    assert "Prerequisite" not in fields and "Amalgam" not in fields
    body = card.sections[0][1]
    assert body[0].startswith("By focusing on a person")
    assert "System: Make an Intelligence + Auspex" in body[1]
    assert "- The emotional state of the subject" in body[2]


def test_power_without_pack_text_falls_back_to_the_wiki_effect():
    records = _with_pages(disciplines.records)
    card = _with_pages(lambda: disciplines.to_card(
        disciplines.DisciplineKind().matches(records, "auspex:heightened senses")[0]))
    assert dict(card.fields)["Cost"] == "Free"
    assert card.sections[0][1] == ["Enhance vampiric senses."]


def test_clan_card_and_bane_parts():
    kind = clans.ClanKind()
    records = _with_pages(clans.records)
    assert [r["name"] for r in records] == ["Brujah", "Caitiff"]

    whole = _with_pages(lambda: kind.card(records[0]))
    assert whole.title == "Brujah"
    assert dict(whole.fields)["Disciplines"] == "Celerity, Potence, Presence"
    assert whole.sections[0] == ("", CLAN_TEXT["brujah"])
    assert [heading for heading, _ in whole.sections] == ["", "Bane", "Variant Bane", "Compulsion"]

    bane = _with_pages(lambda: kind.card(kind.matches(records, "brujah:bane")[0]))
    assert bane.title == "Violent Temper"
    assert bane.subtitle == "Brujah Bane"
    assert "Superficial." in _with_pages(lambda: kind.card(kind.matches(records, "brujah:bane_2")[0])).sections[0][1][0]

    both = _with_pages(lambda: kind.card(kind.matches(records, "brujah:banes")[0]))
    assert both.subtitle == "Bane and Variant Bane"
    assert len(both.sections) == 2

    compulsion = _with_pages(lambda: kind.card(kind.matches(records, "brujah:compulsion")[0]))
    assert compulsion.title == "Rebellion"


def test_merit_and_flaw_group_addressing():
    merits = advantages.AdvantageKind("merit")
    flaws = advantages.AdvantageKind("flaw")
    merit_records = _with_pages(merits.records)
    flaw_records = _with_pages(flaws.records)
    assert {r["name"] for r in merit_records} == {"Beautiful", "Linguistics", "Zeroed"}
    assert {r["name"] for r in flaw_records} == {"Ugly", "Repulsive"}
    # Background rows are not merits, but merits listed beside one still are.
    assert "Allies" not in {r["name"] for r in merit_records}
    assert "Mask" not in {r["name"] for r in merit_records}

    zeroed = _with_pages(lambda: advantages.to_card(merits.matches(merit_records, "zeroed")[0]))
    assert zeroed.subtitle == "Merit (Mask)"
    assert dict(zeroed.fields)["Dots"] == "\u25cf\u25cb\u25cb\u25cb\u25cb"

    match = merits.matches(merit_records, "look:beautiful")
    card = _with_pages(lambda: advantages.to_card(match[0]))
    assert card.subtitle == "Merit (Look)"
    assert card.sections[0][1] == FEATURES["beautiful"]["prose"]
    assert dict(card.fields)["Dots"] == "\u25cf\u25cf\u25cb\u25cb\u25cb"

    assert merits.matches(merit_records, "beautiful")
    assert flaws.matches(flaw_records, "look:ugly")
    assert not merits.matches(merit_records, "look:ugly")
    assert [r["name"] for r in merits.matches(merit_records, "look")] == ["Beautiful"]
    assert merits.display(merit_records[0]) == "Beautiful (Look)"


def test_predator_card():
    record = next(r for r in _with_pages(predators.records) if r["name"] == "Alleycat")
    card = predators.to_card(record)
    assert card.subtitle == "Predator Type"
    body = card.sections[0][1]
    assert any("brute force" in part for part in body)
    assert any(part.startswith("- Gain one specialty") for part in body)


def test_ritual_table_rows():
    records = _with_pages(rituals.records)
    assert [r["name"] for r in records] == ["Astromancy", "Gift of False Life"]
    card = _with_pages(lambda: rituals.to_card(records[1]))
    assert card.subtitle == "Oblivion Ritual"
    fields = dict(card.fields)
    assert fields["Level"] == "2"
    assert fields["Pre-requisite"] == "Ashes to Ashes"
    body = card.sections[0][1]
    assert "Ingredients: A human body." in body
    assert any("corpses equal to their Oblivion rating" in part for part in body)


def test_ritual_without_pack_text_falls_back_to_the_wiki_effect():
    records = _with_pages(rituals.records)
    card = _with_pages(lambda: rituals.to_card(records[0]))
    assert card.sections[0][1] == ["Read the stars.", "Requires a clear sky."]


def test_ritual_path_lookup():
    kind = rituals.RitualKind()
    records = _with_pages(rituals.records)
    matches = kind.matches(records, "oblivion:gift of false life")
    assert len(matches) == 1
    assert kind.display(matches[0]) == "Gift of False Life (Oblivion)"


def test_loresheet_whole_and_entry():
    kind = loresheets.LoresheetKind()
    records = _with_pages(loresheets.records)
    assert [r["name"] for r in records] == ["The Bahari", "Theo Bell"]
    assert kind.key(records[0]) == "bahari"

    whole = _with_pages(lambda: kind.card(records[0]))
    assert whole.subtitle == "Loresheet"
    first = whole.sections[0]
    assert first[0] == "Level 1 \u25cf\u25cb\u25cb\u25cb\u25cb"
    assert first[1][0].startswith("Dangerous Reputation:")

    entry = _with_pages(lambda: kind.card(kind.matches(records, "bahari:ritual scarification")[0]))
    assert entry.title == "Ritual Scarification"
    assert entry.subtitle == "The Bahari Loresheet"
    assert dict(entry.fields)["Dots"] == "\u25cf\u25cf\u25cb\u25cb\u25cb"

    by_level = _with_pages(lambda: kind.card(kind.matches(records, "bahari:3")[0]))
    assert by_level.title == "Blood and Faith"


def test_every_vtm_card_renders_at_32_columns():
    cards = []
    discipline_records = _with_pages(disciplines.records)
    cards.extend(_with_pages(lambda: disciplines.to_card(r)) for r in discipline_records)
    clan_records = _with_pages(clans.records)
    cards.append(_with_pages(lambda: clans.to_card(clan_records[0])))
    cards.extend(_with_pages(lambda r=r: advantages.to_card(r)) for r in _with_pages(advantages.records))
    cards.extend(predators.to_card(r) for r in _with_pages(predators.records))
    cards.extend(_with_pages(lambda: rituals.to_card(r)) for r in _with_pages(rituals.records))
    sheet = _with_pages(lambda: loresheets.to_card(
        next(r for r in loresheets.records() if r["name"] == "The Bahari")))
    cards.append(sheet)

    for card in cards:
        text = _rendered(card)
        assert text.endswith("\n")
        for line in text.splitlines():
            assert len(line) <= 32, line
            assert "<" not in line and "{{" not in line and "[[" not in line


def test_vtm_is_registered():
    from tcard.sources import registry

    assert registry.resolve("vtm") == "vtm:v5"
    assert registry.resolve("v5") == "vtm:v5"
    kinds = registry.kinds("vtm:v5")
    assert set(kinds) == {"discipline", "clan", "loresheet", "predator_type", "ritual", "merit", "flaw"}


def test_pack_details_splits_labels_bullets_and_pools():
    markup = ("<p>The vampire sees auras.</p>"
              "<p>\u25a0 Cost: One Rouse Check </p>"
              "<p>\u25a0 Dice Pools: Intelligence + Auspex vs Composure + Subterfuge </p>"
              "<p>\u25a0 System: Roll.<br>\u25fb A warm colour<br>\u25fb A cold colour</p>"
              "<p>Source: <em>Corebook (p. 250)</em></p>")
    detail = pack.details(markup)
    assert detail["prose"] == ["The vampire sees auras."]
    fields = detail["fields"]
    assert fields["Cost"] == "One Rouse Check"
    assert fields["Pool"] == "Intelligence + Auspex"
    assert fields["Opposing"] == "Composure + Subterfuge"
    assert fields["System"] == "Roll.\n- A warm colour\n- A cold colour"
    assert "Source" not in fields


def test_pack_repairs_split_words_in_both_cases():
    assert pack._repair("A vam pire with out rest") == "A vampire without rest"
    assert pack._repair("Vam pire dam age") == "Vampire damage"
    assert pack._repair("withholding harmless") == "withholding harmless"


def test_pack_feature_keys_drop_dots_and_credit_lines():
    assert pack._feature_key("• Zeroed") == "zeroed"
    assert pack._feature_key("Flaw: (••) Repulsive") == "repulsive"
    assert pack._feature_key("••• Persistent Blush") == "persistent blush"
    assert pack._feature_key("Semblance of the Methuselah") == "semblance of methuselah"


def test_pack_entries_rebuild_shared_key_prefixes():
    import struct

    def varint(value):
        out = bytearray()
        while True:
            byte = value & 0x7F
            value >>= 7
            out.append(byte | (0x80 if value else 0))
            if not value:
                return bytes(out)

    body = b""
    body += varint(0) + varint(1) + varint(1) + b"a" + b"1"
    body += varint(1) + varint(1) + varint(1) + b"b" + b"2"
    block = body + struct.pack("<I", 0) + struct.pack("<I", 1)
    assert list(pack.entries(block)) == [(b"a", b"1"), (b"ab", b"2")]
