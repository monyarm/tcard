from tcard.sources.fivee.tags import render_tags


def test_damage_and_scaledamage():
    assert render_tags("takes {@damage 8d6} fire") == "takes 8d6 fire"
    # published wording is the per-slot increase, not the base
    assert render_tags("{@scaledamage 8d6|3-9|1d6}") == "1d6"
    assert render_tags("{@scaledice 2d4|3-9|1d4}") == "1d4"


def test_variantrule_uses_display_name():
    assert render_tags("in a {@variantrule Sphere [Area of Effect]|XPHB|Sphere}") == "in a Sphere"
    assert render_tags("{@variantrule Difficult Terrain|XPHB}") == "Difficult Terrain"


def test_hit_dc_chance():
    assert render_tags("{@hit 5} to hit, {@dc 15}, {@chance 50}") == "+5 to hit, DC 15, 50%"


def test_hit_already_signed():
    assert render_tags("{@hit -2}") == "-2"


def test_note_is_parenthesised():
    assert render_tags("see {@note this is a note}") == "see (this is a note)"


def test_quickref_uses_display_field():
    assert render_tags("{@quickref Cover||3}") == "Cover"


def test_display_overrides_and_unknown_tag():
    assert render_tags("{@spell fireball|PHB} and {@condition prone}") == "fireball and prone"
    assert render_tags("{@unheardof a|b}") == "a"


def test_book_with_page():
    assert render_tags("{@book Chapter 3|PHB|45}") == "Chapter 3, p.45"


def test_plain_text_untouched():
    assert render_tags("no tags here") == "no tags here"


def test_nested_tags_resolve():
    assert render_tags("{@note see {@spell fireball|PHB}}") == "(see fireball)"


def test_unbalanced_tag_is_dropped():
    assert render_tags("a {@damage 8d6 b") == "a "
