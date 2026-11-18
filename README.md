# tcard

Tabletop cards on stdout, sized for a thermal printer.

```
tcard dnd:5e spell fireball | tp
tcard bag_of_holding | tp
tcard rogue:assassin:assassinate | tp
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
feat  condition  action
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
