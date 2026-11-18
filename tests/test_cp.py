"""CP2020 cards from the static JSON plus fandom prose, no network."""

import json
import unittest.mock as mock

from tcard.render.layout import layout
from tcard.render.text import render
from tcard.sources import registry
from tcard.sources.cp import KINDS, cache, cards, wiki

WEAPON = {
    "name": "Arasaka Restraint Caster",
    "type": "P",
    "damage": "Tangle",
    "ammo": "15mm restraint",
    "shots": 4,
    "rof": 1,
    "range": 25,
    "wa": -1,
    "conc": "J",
    "avail": "P",
    "rel": "ST",
    "cost": 200,
    "source": {"book": "Chromebook 2", "page": 12},
}

WIKITEXT = """{{Infobox Weapon
| name = Arasaka Restraint Caster
| type = Pistol
}}

The '''Arasaka Restraint Caster''' fires a net of monomolecular wire.<ref>Chromebook 2</ref>

It is popular with corporate security teams.

== Gallery ==
[[File:caster.png]]
"""

ARMOR = {
    "name": "Heavy Leather Jacket",
    "isHard": False,
    "isActive": False,
    "isSkinWeave": False,
    "ev": 0,
    "cost": 50,
    "baseSP": 4,
    "locations": {"torso": 4, "rarm": 4, "larm": 4},
}

CYBERWARE = {
    "name": "Alpha Tuff Bone",
    "type": "BIOWARE",
    "notes": "Bone lace adds +2 to body type for damage.",
    "cost": 1300,
    "hc": "1d6/2",
    "surgery": "M",
}

GEAR = {"name": "Flashlight", "category": "SURVIVAL GEAR", "notes": "Waterproof.", "cost": 5, "wt": 0.5}

ROLE = {
    "name": "Solo",
    "specialability": {"name": "Combat Sense", "stat": "INT", "ipmod": 1, "description": "Training in awareness."},
    "salary": [2000, 3000, 4500],
    "skills": ["Awareness/Notice", ["Handgun", "Rifle"]],
}

VEHICLE = {
    "name": "1959 International Harvester",
    "type": "truck",
    "topspeed": 80,
    "accelerate": 5,
    "cargo": "kg",
    "mass": "kg",
    "range": 400,
}

PROGRAM = {
    "name": "Hammer",
    "class": "intrusion",
    "str": 4,
    "mu": 3,
    "cost": 200,
    "options": ["Speed", "Armor"],
    "description": "Attacks a Data Fortress wall.",
}

ART = {"name": "Aikido", "ipMod": 2, "punch": 1, "kick": 0, "block": 2, "dodge": 1}

CORP = {"name": "Budgetarms", "industry": "Weapons", "hq": "Detroit", "version": ["2020"]}


def _wikitext(page, refresh=False):
    return WIKITEXT if page == "Arasaka Restraint Caster" else None


def _card(builder, record):
    with mock.patch.object(cache, "wikitext", _wikitext):
        return builder(record)


def fields(card):
    return dict(card.fields)


def rendered(card):
    return render(layout(card, 32))


def test_weapon_card_carries_wiki_prose():
    card = _card(cards.weapon, WEAPON)
    assert card.title == "Arasaka Restraint Caster"
    assert card.subtitle == "Pistol"
    assert fields(card)["Damage"] == "Tangle"
    assert fields(card)["Range"] == "25 m"
    assert fields(card)["Accuracy"] == "-1"
    assert fields(card)["Concealability"] == "Jacket"
    assert fields(card)["Availability"] == "Poor"
    assert fields(card)["Cost"] == "200 eb"
    body = " ".join(card.sections[0][1])
    assert "monomolecular wire" in body
    assert "Gallery" not in body and "Chromebook 2" not in body


def test_weapon_without_wiki_page_is_stats_only():
    card = cards.weapon(WEAPON | {"name": "Unknown Gun"})
    assert card.sections == []
    assert fields(card)["Damage"] == "Tangle"


def test_armor_has_location_table():
    card = cards.armor(ARMOR)
    assert card.subtitle == "Armor"
    assert fields(card)["Stopping Power"] == "4"
    assert fields(card)["Armor"] == "Soft"
    table = card.sections[0][1][0]
    assert table.rows[0] == ["Location", "SP"]
    assert ["Torso", "4"] in table.rows


def test_cyberware_and_gear_keep_notes():
    ware = cards.cyberware(CYBERWARE)
    assert ware.subtitle == "Bioware"
    assert fields(ware)["Humanity Cost"] == "1d6/2"
    assert fields(ware)["Surgery"] == "Minor"
    assert "Bone lace" in ware.sections[0][1][0]

    item = cards.gear(GEAR)
    assert item.subtitle == "Survival Gear"
    assert item.sections[0][1][0] == "Waterproof."


def test_cyberware_keeps_zero_hc_and_none_surgery():
    # "0" humanity cost and "None" surgery are real values, not missing ones.
    ware = cards.cyberware({"type": "CYBERLIMB", "subtype": "BUILTIN", "name": "Magnetic Hands/Feet",
                            "notes": "For easier Zero-Gee movement", "cost": 60, "hc": "0", "surgery": "N"})
    assert fields(ware)["Humanity Cost"] == "0"
    assert fields(ware)["Surgery"] == "None"
    assert fields(ware)["Subtype"] == "Builtin"


def test_surgery_codes_map_to_words():
    ware = cards.cyberware({"name": "X", "cost": 1, "hc": "2", "surgery": "CRx2"})
    assert fields(ware)["Surgery"] == "Critical x2"


def test_role_lists_salary_and_skills():
    card = cards.role(ROLE)
    assert fields(card)["Special Ability"] == "Combat Sense"
    assert fields(card)["Salary"].startswith("1: 2000, 2: 3000")
    assert fields(card)["Skills"] == "Awareness/Notice, Handgun or Rifle"


def test_vehicle_skips_bare_units():
    card = cards.vehicle(VEHICLE)
    assert fields(card)["Top Speed"] == "80 mph"
    assert fields(card)["Range"] == "400 km"
    assert "Cargo" not in fields(card)
    assert "Mass" not in fields(card)


def test_program_martial_art_and_corp():
    program = cards.program(PROGRAM)
    assert program.subtitle == "Intrusion Program"
    assert fields(program)["Options"] == "Speed, Armor"
    assert program.sections[0][1][0].startswith("Attacks a Data Fortress")

    art = cards.martial_art(ART)
    assert fields(art)["IP Multiplier"] == "2"
    table = art.sections[0][1][0]
    assert ["Punch", "+1"] in table.rows and ["Kick", "+0"] in table.rows

    corp = cards.corporation(CORP)
    assert fields(corp)["Industry"] == "Weapons"
    assert fields(corp)["Headquarters"] == "Detroit"


def test_hyphens_match_spaces():
    kind = KINDS["weapon_option"]
    records = [{"name": "Hip-Mounted Powerpack"}, {"name": "Other"}]
    with mock.patch.object(kind, "records", lambda refresh=False: records):
        assert kind.matches(records, "hip_mounted_powerpack")[0]["name"] == "Hip-Mounted Powerpack"


def test_role_payload_unwraps_dict():
    payload = json.dumps({"roles": [ROLE]})
    loader = __import__("tcard.sources.cp", fromlist=["_list"])._list("apps/chargen/cp2020rolesext.json")
    with mock.patch.object(cache, "data", lambda relative, refresh=False: json.loads(payload)):
        assert [row["name"] for row in loader()] == ["Solo"]


def test_bom_payload_decodes():
    body = b"\xef\xbb\xbf" + json.dumps([{"name": "Gun"}]).encode()
    with mock.patch.object(cache, "_get", lambda url, refresh=False: body):
        assert cache.data("data/moreguns.json")[0]["name"] == "Gun"


def test_wiki_prose_drops_templates_and_tables():
    markup = "{{Infobox Weapon|name=Gun}}\n\nReal '''text''' here.\n\n{|\n|cell\n|}\n\n== References ==\nref text"
    assert wiki.prose(markup) == ["Real text here."]


def test_cards_render_plain_at_32():
    for card in (cards.weapon(WEAPON), cards.armor(ARMOR), cards.cyberware(CYBERWARE),
                 cards.gear(GEAR), cards.role(ROLE), cards.vehicle(VEHICLE),
                 cards.program(PROGRAM), cards.martial_art(ART), cards.corporation(CORP)):
        text = rendered(card)
        assert all(len(line) <= 32 for line in text.splitlines())
        for junk in ("<", "{{", "[[", "|}"):
            assert junk not in text


def test_registry_knows_cyberpunk():
    assert "cp:2020" in registry.systems()
    assert registry.resolve("cp") == "cp:2020"
    kinds = registry.kinds("cp:2020")
    assert "weapon" in kinds and "role" in kinds and "cyberware" in kinds
    assert "electronics" in kinds
    assert len(kinds) == 32


def test_weapon_prints_the_book_category_and_firing_modes():
    card = cards.weapon(dict(WEAPON, category="EXOTICS", subcategory="HEAVY",
                             fullAuto=True, burstFire=True, burst="3m",
                             ap="1/2 vs Soft", thrown=True, bod=9))
    fields = dict(card.fields)
    assert fields["Category"] == "Exotics"
    assert fields["Subcategory"] == "Heavy"
    assert fields["Firing Modes"] == "Full auto, Burst fire"
    assert fields["Burst"] == "3m"
    assert fields["Armour Piercing"] == "1/2 vs Soft"
    assert fields["Thrown"] == "Yes"
    assert fields["Minimum BOD"] == "9"


def test_cyberware_exotic_bodysculpt_reads_as_bioware():
    card = cards.cyberware({"name": "Fangs", "type": "EXOTIC BODYSCULPT",
                            "cost": 500, "hc": "1", "surgery": "M"})
    assert card.subtitle == "Bioware"
    assert dict(card.fields)["Surgery"] == "Minor"


def test_cyberware_prints_option_slots_and_falls_back_to_datafortress():
    record = {"name": "Neural Bridge", "type": "CYBERLIMB", "cost": 600}
    with mock.patch.object(cards.datafortress, "lookup",
                           return_value={"hc": "2", "surgery": "Major",
                                         "effect": "Works with both hands."}):
        card = cards.cyberware(record)
    fields = dict(card.fields)
    assert fields["Humanity Cost"] == "2"
    assert fields["Surgery"] == "Major"
    assert card.sections[0][1] == ["Works with both hands."]


def test_weapon_option_prints_a_cost_multiplier():
    card = cards.weapon_option({"name": "Scope", "type": "Rifle",
                                "costMultiplier": "0.25"})
    assert dict(card.fields)["Cost Multiplier"] == "x0.25"


def test_skill_prints_its_option_and_manoeuvre_bonuses():
    card = cards.skill({"name": "Martial Art: Aikido", "stat": "REF",
                        "ipmod": 2, "option": "Martial Art: Aikido",
                        "maBonuses": {"punch": 1, "kick": -1}})
    fields = dict(card.fields)
    assert fields["Option"] == "Martial Art: Aikido"
    assert fields["Manoeuvres"] == "Punch +1, Kick -1"


def test_role_prints_secondary_skills():
    card = cards.role({"name": "Solo", "specialability": {"name": "Combat Sense"},
                       "skills": [["Handgun", "Rifle"]],
                       "secondary": [["Demolitions", "Disguise"]]})
    fields = dict(card.fields)
    assert fields["Secondary Skills"] == "Demolitions or Disguise"


def test_datafortress_rows_pair_stats_with_effect_text():
    from tcard.sources.cp import datafortress
    markup = ("<tr><td>Type</td><td>Cost</td><td>HC</td><td>Surgery Code</td></tr>"
              "<tr><td>Neural Bridge</td><td>$500</td><td>2</td><td>Major</td></tr>"
              "<tr><td>Effect</td></tr><tr><td>Works with both hands.</td></tr>")
    items = datafortress.parse(markup)
    assert len(items) == 1
    assert items[0] == {"name": "Neural Bridge", "cost": "$500", "hc": "2",
                        "surgery": "Major", "effect": "Works with both hands."}
