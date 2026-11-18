"""Monster stat blocks keep stat mode across DEFENSE/OFFENSE dividers."""

from tcard.sources.pf1 import page

MARKUP = """<article><h1>Dire Rat</h1>
<p><b>Init</b> +3; <b>Senses</b> low-light vision</p>
<p class="divider">DEFENSE</p>
<p><b>AC</b> 14, touch 14<br /><b>hp</b> 5 (1d8+1)<br /><b>Fort</b> +3, <b>Ref</b> +5</p>
<p class="divider">OFFENSE</p>
<p><b>Speed</b> 40 ft., climb 20 ft.</p>
<p class="divider">DESCRIPTION</p>
<p>A dire rat is a scavenger.</p>
</article>"""


def test_stat_fields_survive_unknown_dividers():
    card = page.parse(MARKUP)
    fields = dict(card.fields)
    assert card.title == "Dire Rat"
    assert fields["Init"] == "+3"
    assert fields["AC"] == "14, touch 14"
    assert fields["hp"] == "5 (1d8+1)"
    assert fields["Fort"] == "+3"
    assert fields["Speed"] == "40 ft., climb 20 ft."
    assert card.subtitle == ""


def test_body_section_still_after_description_divider():
    card = page.parse(MARKUP)
    prose = [part for _, parts in card.sections for part in parts]
    assert "A dire rat is a scavenger." in prose
