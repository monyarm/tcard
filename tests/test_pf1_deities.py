"""Archives of Nethys deity pages (d20pfsrd cannot host them)."""

import os
import tempfile

from tcard.sources.pf1 import deities

INDEX = """<html><body>
<a href="DeityDisplay.aspx?ItemName=Abadar">Abadar</a>
<a href="DeityDisplay.aspx?ItemName=Ah%20Pook">Ah Pook</a>
<a href="DeityDisplay.aspx?ItemName=Abadar">Abadar</a>
<a href="/DeityDetails.aspx">by alignment</a>
</body></html>"""

PAGE = """<html><body><div class="main" id="main">
<h1 style="text-align:center"><a href="DeityDetails.aspx">Deities by Alignment</a></h1>
<span id="x"><h1 class="title"><img src="images\\pfs.gif" /> Sarenrae</h1>
<h2><b>The Dawnflower</b></h2>
<b>Source</b> <a href="http://paizo.com/x"><i>Inner Sea Gods pg. 132</i></a><br />
<b>Pathfinder Wiki</b> <a href="http://www.pathfinderwiki.com/wiki/Sarenrae">Sarenrae</a>
<h3 class="framing">Details</h3>
<b>Alignment</b> NG<br />
<b>Pantheon</b> Core Deities<br />
<b>Areas of Concern</b> Healing, honesty, redemption, the sun<br />
<b>Domains</b> <a href="DomainDisplay.aspx?ItemName=Fire">Fire</a>, <a href="DomainDisplay.aspx?ItemName=Sun">Sun</a><br />
<b>Favored Weapon</b> Scimitar
<h3 class="framing">Obedience</h3>
Offer to heal a stranger of his wounds.<br />
Gain a +2 sacred bonus on Perception checks.
<h2 class="title">For Followers of Sarenrae</h2>
<h3 class="framing">Archetypes</h3>
Some archetype list
<h3 class="framing">Spells</h3>
Some spell list
<h2 class="title">Unique Spell Rules</h2>
<h3 class="framing">Cleric/Warpriest</h3>
<i>Flame Blade</i> can be prepared as a 2nd-level spell
</div></body></html>"""


def _patch_cache(body):
    def run(method):
        with tempfile.TemporaryDirectory() as tmp:
            old = os.environ.get("XDG_CACHE_HOME")
            os.environ["XDG_CACHE_HOME"] = tmp
            original = deities.cache.fetch
            deities.cache.fetch = lambda url: INDEX if url.endswith("DeitiesByGroup.aspx") else body
            try:
                return method()
            finally:
                deities.cache.fetch = original
                if old is None:
                    os.environ.pop("XDG_CACHE_HOME", None)
                else:
                    os.environ["XDG_CACHE_HOME"] = old

    return run


def test_index_lists_each_deity_once():
    def check():
        names = [r["name"] for r in deities.records()]
        assert names == ["Abadar", "Ah Pook"]
        assert deities.records()[0]["url"].endswith("ItemName=Abadar")

    _patch_cache(PAGE)(check)


def test_card_title_subtitle_and_fields():
    card = deities.parse(PAGE)
    fields = dict(card.fields)
    assert card.title == "Sarenrae"
    assert card.subtitle == "The Dawnflower"
    assert fields["Alignment"] == "NG"
    assert fields["Pantheon"] == "Core Deities"
    assert fields["Domains"] == "Fire, Sun"
    assert fields["Favored Weapon"] == "Scimitar"
    assert "Source" not in fields
    assert "Pathfinder Wiki" not in fields


def test_sections_keep_rules_and_drop_link_lists():
    card = deities.parse(PAGE)
    headings = [heading for heading, _ in card.sections]
    assert "Obedience" in headings
    assert "Cleric/Warpriest" in headings
    assert not any("For Followers" in heading for heading in headings)
    assert "Archetypes" not in headings
    assert "Spells" not in headings
    obedience = dict(card.sections)["Obedience"]
    assert any("Offer to heal a stranger" in part for part in obedience)
