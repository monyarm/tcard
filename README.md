# tcard

Tabletop cards on stdout, sized for a thermal printer.

```
tcard dnd:5e spell fireball | tp
tcard fireball | tp
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
tcard [SYSTEM:] [KIND] NAME...
```

System selectors use a colon: `dnd:5e`, and later `pf:1e`, `vtm:v5`, `cp:2020`.
Leading parts may be omitted when the lookup is unambiguous:

```
tcard dnd:5e spell fireball   # canonical
tcard dnd:5e fireball         # kind inferred
tcard spell fireball          # system from config
tcard fireball                # both inferred
```

Flags: `--source CODE`, `--cols N`, `--brief`, `--all`, `--refresh`.

- `--cols` must not exceed the width `tp` uses. Default `tp` font = 32 columns;
  a larger `tp -s` means fewer columns.
- `--brief` prints the header and stat block only.
- `--all` lists every match; useful because names collide (`Shield` is a spell).
- Data comes from `https://5e.tools/data` and is cached in `~/.cache/tcard/`.
  `--refresh` refetches.

Config: `~/.config/tcard/config.toml`, optional.

```toml
systems = ["dnd:5e"]
kinds   = ["spell"]
prefer  = ["XPHB", "PHB"]
cols    = 32
```

## Test

```
python3 tests/run.py
```
