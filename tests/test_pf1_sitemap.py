"""d20pfsrd sitemap filtering and page cache keys."""

import hashlib
import os
import tempfile

from tcard.sources.pf1 import cache, sitemap

INDEX = (
    '<?xml version="1.0"?><sitemapindex>'
    "<sitemap><loc>https://www.d20pfsrd.com/wp-sitemap-posts-page-1.xml</loc></sitemap>"
    "</sitemapindex>"
)

PAGE = """<?xml version="1.0"?><urlset>
<loc>https://www.d20pfsrd.com/feats/combat-feats/power-attack-combat/</loc>
<loc>https://www.d20pfsrd.com/traits/combat-traits/power-attack-trait/</loc>
<loc>https://www.d20pfsrd.com/equipment/weapons/longsword/</loc>
<loc>https://www.d20pfsrd.com/magic-items/wondrous-items/bag-of-holding/</loc>
<loc>https://www.d20pfsrd.com/races/core-races/dwarf/</loc>
<loc>https://www.d20pfsrd.com/classes/core-classes/rogue/archetypes/assassin/</loc>
<loc>https://www.d20pfsrd.com/classes/prestige-classes/apg/assassin/</loc>
<loc>https://www.d20pfsrd.com/classes/core-classes/rogue/rogue-talents/bleeding-attack/</loc>
<loc>https://www.d20pfsrd.com/extras/community-creations/house-rule/</loc>
<loc>https://www.d20pfsrd.com/races/3rd-party-races/gnoll/</loc>
<loc>https://www.d20pfsrd.com/work-area/staging/feats/broken/</loc>
<loc>https://www.d20pfsrd.com/__trashed/thing/</loc>
</urlset>"""


def _with_cache(body):
    def run(method):
        with tempfile.TemporaryDirectory() as tmp:
            old = os.environ.get("XDG_CACHE_HOME")
            os.environ["XDG_CACHE_HOME"] = tmp
            original = sitemap.cache.fetch
            sitemap.cache.fetch = lambda url: INDEX if url.endswith("sitemap.xml") else PAGE
            try:
                return method()
            finally:
                sitemap.cache.fetch = original
                if old is None:
                    os.environ.pop("XDG_CACHE_HOME", None)
                else:
                    os.environ["XDG_CACHE_HOME"] = old

    return run


def test_skips_community_and_staging_paths():
    def check():
        found = sitemap.urls()
        assert not any("/extras/" in url for url in found)
        assert not any("3rd-party" in url for url in found)
        assert not any("__trashed" in url for url in found)
        assert len(found) == 8

    _with_cache(PAGE)(check)


def test_names_come_from_slugs():
    assert sitemap.name_for("https://www.d20pfsrd.com/magic-items/bag-of-holding/") == "Bag Of Holding"


def test_feat_and_trait_do_not_collide():
    def check():
        feats = sitemap.records("feat")
        traits = sitemap.records("trait")
        assert [r["name"] for r in feats] == ["Power Attack Combat"]
        assert [r["name"] for r in traits] == ["Power Attack Trait"]
        assert feats[0]["url"] != traits[0]["url"]

    _with_cache(PAGE)(check)


def test_kind_filters():
    def check():
        assert len(sitemap.records("equipment")) == 1
        assert len(sitemap.records("magic_item")) == 1
        assert len(sitemap.records("race")) == 1
        assert len(sitemap.records("archetype")) == 1
        assert len(sitemap.records("prestige_class")) == 1
        abilities = sitemap.records("class_ability")
        assert [r["name"] for r in abilities] == ["Bleeding Attack"]
        assert abilities[0]["class"] == "rogue"
        assert abilities[0]["family"] == "rogue talents"
        assert all(r["name"] != "Assassin" for r in abilities)

    _with_cache(PAGE)(check)


def test_cached_urls_are_reused():
    def check():
        sitemap.urls()
        sitemap.cache.fetch = lambda url: (_ for _ in ()).throw(AssertionError("refetched"))
        assert len(sitemap.urls()) == 8

    _with_cache(PAGE)(check)


def test_page_cache_keyed_by_url_hash():
    first = {"name": "Power Attack", "url": "https://www.d20pfsrd.com/feats/power-attack/"}
    second = {"name": "Power Attack", "url": "https://www.d20pfsrd.com/traits/power-attack/"}
    with tempfile.TemporaryDirectory() as tmp:
        old = os.environ.get("XDG_CACHE_HOME")
        os.environ["XDG_CACHE_HOME"] = tmp
        original = cache.fetch
        cache.fetch = lambda url: f"<html>{url}</html>"
        try:
            first_path = cache.page(first)
            second_path = cache.page(second)
            digest = hashlib.sha1(first["url"].encode()).hexdigest()[:12]
            assert (cache.cache_dir() / "pages" / f"{digest}.html").exists()
            assert first_path != second_path
            assert "<html>" in cache.page(first)
        finally:
            cache.fetch = original
            if old is None:
                os.environ.pop("XDG_CACHE_HOME", None)
            else:
                os.environ["XDG_CACHE_HOME"] = old
