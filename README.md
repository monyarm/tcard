# tcard

Tabletop cards on stdout, sized for a thermal printer.

```
tcard dnd:5e spell fireball | tp
tcard bag_of_holding | tp
tcard rogue:assassin:assassinate | tp
tcard pf1 spell fireball | tp
```

## Install (local)

```
pipx install .
# or
python3 -m pip install --user .
```

Nothing to build, no dependencies. To run from a checkout without installing:

```
python3 -m tcard fireball | tp
```

## Use

```
tcard [SYSTEM] [KIND] NAME...
```

Leading parts may be omitted when the lookup is unambiguous:

```
tcard dnd:5e spell fireball      # canonical
tcard 5e spell fireball          # 5e is an alias for dnd:5e
tcard 5e fireball                # kind inferred
tcard spell fireball             # system from config
tcard fireball                   # both inferred
```

Content kinds:

```
spell  item  class_ability
invocation  metamagic  maneuver  fighting_style  pact_boon  infusion
rune  arcane_shot  elemental_discipline  renown_boon
feat  condition  action  background
```

Names: use `_` for spaces and ignore apostrophes (`tasha's_hideous_laughter`).
Class features take `class:feature`, `subclass:feature` or `class:subclass:feature`:

```
tcard fighter:second_wind
tcard rogue:assassin:assassinate
tcard 5e class_ability champion:improved_critical
```

Flags: `--source CODE`, `--cols N`, `--brief`, `--all`, `--refresh`.

- `--cols` must not exceed the width `tp` uses. Default `tp` font = 32 columns;
  a larger `tp -s` means fewer columns.
- `--brief` prints the header and stat block only.
- `--all` lists every match; names collide (`Shield` is a spell and an item).
- Data comes from `https://5e.tools/data` and is cached in `~/.cache/tcard/dnd-5e/`.
  Each kind is downloaded on first use. `--refresh` refetches.
- Pathfinder 1e comes from `https://www.d20pfsrd.com`. `tcard pf1 spell fireball`
  uses 26 letter pages (~20 s once) to build the spell index. Other kinds use the
  site's 23 sitemap pages (~27k URLs, one download) filtered by path:
  `feat`, `trait`, `equipment`, `magic_item`, `race`, `archetype`,
  `prestige_class`, `monster`, `deity`, plus one kind per class feature family
  (`rogue_talent`, `witch_hex`, `magus_arcana`, `alchemist_discovery`,
  `rage_power`, `ki_power`, `arcane_school`, `arcanist_exploit`,
  `ninja_trick`, `slayer_talent`, `bardic_masterpiece`, `wild_talent`,
  `weapon_training`, `bloodline`, `mystery`, `curse`, `order`, `spirit`,
  `domain`). Examples:

  ```
  tcard pf1 rogue_talent bleeding_attack
  tcard pf1 rogue_talent rogue:bleeding_attack
  tcard pf1 witch_hex city_sight
  tcard pf1 trait magic:aeromantic_affinity
  tcard pf1 trait racial:arcane_dabbler
  tcard pf1 magic_item bag_of_holding
  tcard pf1 monster dire_rat
  tcard pf1 deity sarenrae
  ```

  Familiars and animal companions are `bestiary/monster-listings/...` pages too,
  so `monster` covers them (`tcard pf1 monster owl`).

  Deities are the one kind that does not come from d20pfsrd: deity write-ups are
  Product Identity and stay off the site, so `deity` reads the Pathfinder 1e
  Archives of Nethys (`https://aonprd.com/DeitiesByGroup.aspx` for the ~460 names,
  one page each). Only the rules sections are kept; the "for followers of X"
  link lists are dropped.

  Traits take `trait:<group>:<name>`; groups are the site's own
  (`magic`, `racial`, `combat`, `social`, `religion`, `campaign`, ...).
  Pages are fetched on demand and cached in `~/.cache/tcard/pf1/`.
  3PP content is filtered by path heuristics, so a few community entries can
  still appear in `--all` listings.
- Long spells and features run to a second page; `tp` waits 3 s between pages.

Config: `~/.config/tcard/config.toml`, optional.

```toml
systems = ["dnd:5e"]
kinds   = ["spell", "item", "class_ability"]   # inference order; empty = all kinds
prefer  = ["XPHB", "XDMG", "PHB", "DMG"]       # 2024 sources first
cols    = 32
```

## Test

```
python3 tests/run.py
```
