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
spell  item  class_ability  subclass  monster
invocation  metamagic  maneuver  fighting_style  pact_boon  infusion
rune  arcane_shot  elemental_discipline  renown_boon
feat  condition  action  background  species  variant_rule
```

Species (the 2024 name for races) prints type, size, speed, darkvision,
resistances and the trait list; 2014 races add their ability scores. Variant
rules print their rule text:

```
tcard species aasimar
tcard species dragonborn --source PHB
tcard variant_rule cover
```

Monsters print the stat block: AC, HP, speed, saves, skills, defenses, senses,
languages, CR, two ability-score tables, then traits, actions, bonus actions,
reactions, legendary, mythic, lair and regional sections:

```
tcard monster goblin
tcard monster adult_red_dragon
```

Names: use `_` for spaces and ignore apostrophes (`tasha's_hideous_laughter`).
Class features take `class:feature`, `subclass:feature` or `class:subclass:feature`:

```
tcard fighter:second_wind
tcard rogue:assassin:assassinate
tcard 5e class_ability champion:improved_critical
```

A whole subclass prints every feature it grants, grouped by level:
`tcard subclass assassin` (or `tcard subclass rogue:assassin` when the name is
shared). `--brief` would print only the header, so leave it off for subclasses.

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
  `feat`, `trait`, `racial_trait`, `equipment`, `magic_item`, `race`, `archetype`,
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
  tcard pf1 racial_trait arcane_dabbler
  tcard pf1 magic_item bag_of_holding
  tcard pf1 monster dire_rat
  tcard pf1 deity sarenrae
  ```

  Familiars and animal companions are `bestiary/monster-listings/...` pages too,
  so `monster` covers them (`tcard pf1 monster owl`).

  Archetypes print one section per class feature (`tcard pf1 archetype acrobat`
  gives `Expert Acrobat (Ex)`, `Second Chance (Ex)`, …).

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
- Vampire: The Masquerade 5th edition comes from `https://vtm.paradoxwikis.com`.
  The wiki answers every request with a JS bot gate, so pages are fetched through
  `https://r.jina.ai/` and cached in `~/.cache/tcard/vtm-v5/`. The first
  discipline lookup fetches all 12 discipline pages (~30 s once); everything else
  is one page. Kinds: `discipline`, `clan`, `loresheet`, `predator_type`,
  `ritual`, `merit`, `flaw`.

  Disciplines, clans and loresheets are containers: print the whole thing, or
  one part after the colon.

  ```
  tcard vtm:v5 discipline auspex
  tcard vtm:v5 discipline auspex:scry_the_soul
  tcard vtm:v5 clan brujah
  tcard vtm:v5 clan brujah:bane          # bane_2 is the variant bane
  tcard vtm:v5 clan brujah:banes
  tcard vtm:v5 loresheet bahari
  tcard vtm:v5 loresheet bahari:2        # or an entry name
  tcard vtm:v5 ritual blood_sorcery:astromancy
  tcard vtm:v5 ritual oblivion:gift_of_false_life
  tcard vtm:v5 merit look:beautiful
  tcard vtm:v5 flaw look:ugly
  tcard vtm:v5 predator_type alleycat
  ```

  Loresheets come from `whitewolf.fandom.com`, because the Paradox wiki only
  indexes them: the names come from its `Loresheet` page and `Category:Loresheets`,
  and the dot-rated entries are read from each loresheet's own page.

  Dot ratings print as `●`/`○`. DejaVu Sans Mono draws both in exactly one cell,
  and `tp` keeps any glyph its font can draw.
- Vampire: The Masquerade 20th Anniversary comes from `whitewolf.fandom.com`
  wikitext, cached in `~/.cache/tcard/vtm-v20/`. Kinds: `discipline`, `clan`,
  `bloodline`, `ritual`, `path`, `merit`, `flaw`.

  ```
  tcard vtm:v20 discipline auspex
  tcard vtm:v20 discipline auspex:heightened_senses
  tcard vtm:v20 clan brujah
  tcard vtm:v20 clan brujah:banes        # or :bane_2, :compulsion
  tcard vtm:v20 bloodline baali
  tcard vtm:v20 ritual thaumaturgy:bind_the_accusing_tongue
  tcard vtm:v20 ritual necromancy:knowing_stone
  tcard vtm:v20 path path_of_caine
  tcard vtm:v20 merit one:ambidextrous
  tcard vtm:v20 flaw two:blind
  ```

  Rituals span seven tradition list pages (Thaumaturgy, Necromancy, Akhu,
  Anarch, Dur-An-Ki, Koldunic, Sadhana); Thaumaturgy publishes a rank table and
  the others publish dot bullets, and both shapes feed the same card.
- Pathfinder 2e comes from the Foundry data repo (`github.com/foundryvtt/pf2e`,
  branch `v14-dev`) as item JSON. The first use does a blobless sparse checkout
  into `~/.cache/tcard/pf2/repo` (one clone, then only the packs a kind needs);
  `--refresh` pulls the branch again. Kinds: `spell`, `feat`, `equipment`,
  `ancestry`, `heritage`, `background`, `class`, `class_feature`, `deity`,
  `monster`, `condition`, `action`, `hazard`.

  ```
  tcard pf:2e spell fireball
  tcard pf:2e feat toughness
  tcard pf:2e equipment longsword
  tcard pf:2e ancestry dwarf
  tcard pf:2e deity sarenrae
  tcard pf:2e monster goblin_warrior
  tcard pf:2e condition prone
  ```

  Descriptions are HTML with Foundry macros (`@UUID[...]`, `@Damage[...]`,
  `@Check[...]`, `@Template[...]`); they are expanded to plain words before
  wrapping. Monsters keep their stat block: one row of ability modifiers under
  the fields, then the flavour text and one section per embedded ability.
- Cyberpunk 2020 comes from `cybersmily.net`, which serves the whole dataset as
  static JSON. It is cached in `~/.cache/tcard/cp-2020/`. Equipment is split by
  shop category rather than lumped into one kind: `weapon`, `armor`, `cyberware`,
  `program`, `vehicle`, `martial_art`, `weapon_option`, `role`, `skill`,
  `corporation`, plus 22 gear kinds (`electronics`, `security`, `drugs`,
  `medical`, `tools`, `surveillance`, `communication`, `lifestyle`,
  `demolition`, `military_gear`, `transport`, `braindance`, ...).

  Weapon stat blocks have no prose in the data, so descriptions are pulled from
  the Cyberpunk wiki (`cyberpunk.fandom.com`); weapons the wiki does not cover
  print stats only. Cyberware without a Humanity Cost or Surgery code in the
  JSON falls back to the `bio.htm` bioware tables on `datafortress2020.com`
  (expired certificate, read with verification off). Hyphens are treated as
  spaces, so `hip_mounted_powerpack` finds `Hip-Mounted Powerpack`.

  Cards print every field the record carries: weapons show the book category,
  subcategory, firing modes, burst, armour piercing, thrown and minimum BOD;
  cyberware shows subtype, humanity cost, surgery and option slots; skills show
  their option and manoeuvre bonuses; weapon options show a cost multiplier.

  ```
  tcard cp:2020 weapon arasaka_restraint_caster
  tcard cp:2020 armor heavy_leather_jacket
  tcard cp:2020 cyberware alpha_tuff_bone
  tcard cp:2020 role solo
  tcard cp:2020 martial_art aikido
  tcard cp:2020 program hammer
  tcard cp:2020 vehicle 1959_international_harvester
  tcard cp:2020 corporation budgetarms
  ```
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
