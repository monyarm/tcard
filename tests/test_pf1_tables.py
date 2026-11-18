"""PF1 tables survive parsing as Table objects and render inside the width."""

from pathlib import Path

from tcard.model import Table
from tcard.render.layout import layout
from tcard.render.text import render
from tcard.sources.pf1 import spell

MARKUP = """<html><body><article>
<h1>Test Spell</h1>
<p><b>School</b> evocation [fire]; <b>Level</b> sorcerer/wizard 3</p>
<p><b>Casting Time</b> 1 standard action</p>
<p class="divider">EFFECT</p>
<p><b>Range</b> close (25 ft. + 5 ft./2 levels)</p>
<p class="divider">DESCRIPTION</p>
<p>Before.</p>
<table><thead><tr><th>d6</th><th>Result</th></tr></thead>
<tbody><tr><td>1</td><td>Bad</td></tr><tr><td>2</td><td>Worse</td></tr></tbody></table>
<p>After.</p>
</article></body></html>"""


def test_table_kept_in_document_order():
    card = spell.parse(MARKUP, "Test Spell")
    parts = card.sections[0][1]
    assert parts[0] == "Before.", parts
    assert isinstance(parts[1], Table), parts
    assert parts[2] == "After.", parts


def test_table_header_and_rows():
    card = spell.parse(MARKUP, "Test Spell")
    table = card.sections[0][1][1]
    assert table.header is True
    assert table.rows == [["d6", "Result"], ["1", "Bad"], ["2", "Worse"]], table.rows


def test_table_renders_inside_width():
    card = spell.parse(MARKUP, "Test Spell")
    lines = layout(card, 32)
    text = render(lines)
    assert "d6" in text and "Result" in text and "Worse" in text
    for line in text.splitlines():
        assert len(line) <= 32, line
        assert line.isascii(), line
    assert "d6 Result" in text, text
    rendered = [line for line in lines if line.kind.value == "table"]
    assert rendered[0].table is not None


def test_fixture_page_still_parses_without_tables():
    markup = (Path(__file__).parent / "fixtures" / "pf1-fireball.html").read_text()
    card = spell.parse(markup, "Fireball")
    assert card.title == "Fireball"
    assert all(not isinstance(part, Table) for _, parts in card.sections for part in parts)
