# tcard: 5e.tools content expansion

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add items, class abilities, optional features, feats, conditions and actions to `tcard`, with `5e` accepted as a system alias and underscore/apostrophe-insensitive names.

**Architecture:** Each content kind is a `Kind` object (records loader + `Card` builder + matcher) registered in `sources/fivee/__init__.py`. `sources/fivee/cache.py` generalizes the existing fetch-once JSON cache. The renderer and `Card` model are untouched, so no new layout code is needed.

**Tech Stack:** Python 3.11+, stdlib only (urllib, json, tomllib). Tests via `python3 tests/run.py`, no pytest.

**Spec:** `docs/superpowers/specs/2026-11-18-tcard.md`

## Global Constraints

- Output stays pure ASCII and every line <= `cols` (layout asserts both).
- 32 columns default; `--cols` overrides between 8 and 200.
- No new dependencies, no Nix files in this repo.
- Cache lives under `$XDG_CACHE_HOME|~/.cache/tcard/dnd-5e`; first use of a kind fetches its files once.
- Names match case-insensitively, `_` equals a space, apostrophes are ignored.
- Systems: canonical `dnd:5e`, alias `5e`; both accepted.
- Exit codes: 0 printed, 1 no/ambiguous match, 2 usage, 3 cache/network.

## Review Focus

1. `rogue:assassin:assassinate` must not be mistaken for a system selector (it contains `:`) and must resolve the 2014 subclass while `assassinate` alone still resolves by class order.
2. Item `value` is copper pieces; a card must print gp (`150000` -> `1500 gp`), never raw cp.
3. Item `type` is an abbreviation (`HA`, `RG|DMG`, `M`); an unknown or missing abbreviation must fall back to "Wondrous Item", not crash or leak the code.
4. `Bag of Holding` exists in DMG and XDMG; default must follow `prefer` and `--source DMG` must still work.
5. Optional features share one file but five feature types map to one kind (`FS:F/R/P/B`); filtering must not drop any of them.

---

### Task 1: Query normalisation and the Kind interface

**Files:**
- Create: `tcard/names.py`, `tcard/sources/base.py`
- Test: `tests/test_names.py`

**Interfaces:**
- Produces: `normalize(text: str) -> str`, `split_path(query: str) -> list[str]`; `Kind` with `id`, `records(refresh=False)`, `card(record)`, `key(record)`, `display(record)`, `matches(records, query)`.

- [x] **Step 1: Write failing tests** — `normalize("Tasha’s_Hideous  Laughter") == "tashas hideous laughter"`; `normalize("Second__Wind") == "second wind"`; `split_path("rogue:assassin:assassinate") == ["rogue","assassin","assassinate"]`; `split_path("fighter: second_wind") == ["fighter","second wind"]`; `Kind().matches([...], "fir")` returns prefix hits only when no exact hit.
- [x] **Step 2: Run** `python3 tests/run.py` — fails on import.
- [x] **Step 3: Implement** `names.py` (underscore -> space, strip `' ’ ‘ \``, casefold, collapse whitespace) and `base.py` (`Kind.matches` = exact key match, else prefix; `key` = `normalize(name)`; `display` = name).
- [x] **Step 4: Run tests** — pass.
- [x] **Step 5: Commit** `feat: query normalisation and Kind interface`.

### Task 2: Generic cache + CLI matching through Kind

**Files:**
- Create: `tcard/sources/fivee/cache.py`
- Modify: `tcard/sources/registry.py`, `tcard/cli.py`, `tcard/config.py`
- Test: `tests/test_cli.py`, `tests/test_registry.py`

**Interfaces:**
- `cache.load_json(rel: str, refresh: bool = False) -> object`; `cache.cache_dir() -> Path`; `cache.get(url) -> bytes`.
- `registry.resolve(token: str) -> str` maps `5e` to `dnd:5e`; `registry.names() -> list[str]` includes aliases.
- `split_terms` accepts a system token only when it resolves; a token whose prefix before `:` is a known system family but does not resolve raises exit 2; anything else with `:` is part of the name.

- [x] **Step 1: Write failing tests** — `tcard 5e fireball` resolves; `tcard dnd:5e fireball` resolves; `tcard rogue:assassin:assassinate` does not raise a system error; `tcard dnd:9e fireball` exits 2.
- [x] **Step 2: Run** — fails.
- [x] **Step 3: Implement** cache module (reusing `index.cache_dir`/`_get`/`_store`), registry aliases, `split_terms` family rule, `cfg.kinds or list(available)`.
- [x] **Step 4: Run tests** — pass, including existing 93.
- [x] **Step 5: Commit** `feat: system aliases and generic data cache`.

### Task 3: Items

**Files:**
- Create: `tcard/sources/fivee/items.py`, `tcard/sources/fivee/fields.py`
- Modify: `tcard/sources/fivee/__init__.py`
- Test: `tests/test_items.py`, fixture `tests/fixtures/items.json`

**Interfaces:**
- `records(refresh=False) -> list[dict]` merges `items.json["item"]` with `items-base.json["baseitem"]` and `["item"]`, deduped on `(name, source)`.
- `to_card(record) -> Card`: subtitle `"{Rarity} {Type}"` or `"{Type}"` for mundane; fields Attunement, Damage/AC, Weight, Value, Source.
- `type_name(code, tables) -> str` uses `itemType` abbreviation -> name; missing/unknown -> `"Wondrous Item"`.
- `value_gp(cp) -> str` -> `f"{cp/100:g} gp"`; weight -> `f"{weight:g} lb"`.
- `fields.source_field(record)` and `fields.format_prereq(value)` shared by later tasks.

- [ ] **Step 1: Write failing tests** — Bag of Holding: `Uncommon Wondrous Item`, `Attunement: Required`, `15 lb`, `1500 gp`? (value absent -> field omitted), `Source: DMG p.153`; Longsword: `Melee Weapon`, `Damage: 1d8 slashing, versatile (1d10)`, `Value: 15 gp`; Plate Armor: `Damage: AC 18, Str 15, stealth disadvantage`; Ring of Protection: `Attunement: Required`, `AC +1`; unknown `type` code does not leak the code.
- [ ] **Step 2: Run** — fails.
- [ ] **Step 3: Implement** loaders, abbreviation tables, field formatting, card builder with `flatten`+`render_tags`.
- [ ] **Step 4: Run tests** — pass.
- [ ] **Step 5: Commit** `feat: item cards`.

### Task 4: Class abilities

**Files:**
- Create: `tcard/sources/fivee/klass.py`
- Modify: `tcard/sources/fivee/__init__.py`
- Test: `tests/test_klass.py`, fixture `tests/fixtures/class-fighter.json`

**Interfaces:**
- `records(refresh=False)` loads `class/index.json` then every `class/class-*.json`, returning `classFeature + subclassFeature` deduped.
- `to_card(record)`: subtitle `"{className}"` or `"{className} ({subclassShortName})"`; fields Level, Source.
- `matches(records, query)`: 1 segment = feature name across all classes; 2 = `class:feature`, or `subclass:feature` when segment one is not a class; 3 = `class:subclass:feature`. Class/subclass compare exactly on normalized name; feature uses exact then prefix.

- [ ] **Step 1: Write failing tests** — `fighter:second_wind` -> "Second Wind", subtitle "Fighter", `Level: 1`; `rogue:assassin:assassinate`; bare `assassinate` finds it; `fighter:champion:improved_critical`; wrong class gives no match.
- [ ] **Step 2: Run** — fails.
- [ ] **Step 3: Implement** loader, path matcher, card.
- [ ] **Step 4: Run** — pass.
- [ ] **Step 5: Commit** `feat: class ability cards`.

### Task 5: Optional features

**Files:**
- Create: `tcard/sources/fivee/optional.py`
- Modify: `tcard/sources/fivee/__init__.py`
- Test: `tests/test_optional.py`, fixture `tests/fixtures/optionalfeatures.json`

**Interfaces:**
- `KINDS`: `invocation` (EI), `metamagic` (MM), `maneuver` (MV:B), `fighting_style` (FS:F, FS:R, FS:P, FS:B), `pact_boon` (PB), `infusion` (AI), `rune` (RN), `arcane_shot` (AS), `elemental_discipline` (ED), `renown_boon` (RP).
- `records(refresh=False)` returns all 233 once; each kind filters on `featureType` intersection.
- `to_card`: subtitle the human label ("Eldritch Invocation"), fields Prerequisite (when present) and Source.

- [ ] **Step 1: Write failing tests** — `invocation agonizing_blast` subtitle "Eldritch Invocation"; `metamagic quickened_spell`; `fighting_style archery` matches at least one of the four FS codes; a maneuvering feature never appears under `invocation`.
- [ ] **Step 2: Run** — fails.
- [ ] **Step 3: Implement** label table, filtering kind class, card.
- [ ] **Step 4: Run** — pass.
- [ ] **Step 5: Commit** `feat: optional feature cards`.

### Task 6: Feats, conditions, actions

**Files:**
- Create: `tcard/sources/fivee/feats.py`, `tcard/sources/fivee/conditions.py`, `tcard/sources/fivee/actions.py`, `tcard/sources/fivee/simple.py`
- Modify: `tcard/sources/fivee/__init__.py`
- Test: `tests/test_simple_kinds.py`, fixtures `tests/fixtures/{feats,conditions,actions}.json`

**Interfaces:**
- `simple.SimpleKind(id, loader, builder)` implements `Kind` from two callables.
- feats: subtitle = `category` title-cased (`Origin`), field Prerequisite when present; conditions: subtitle "Condition"; actions: subtitle "Action", field Time via `spell.format_time`.

- [ ] **Step 1: Write failing tests** — `feat lucky` -> "Origin", prerequisite text; `condition prone` -> "Condition"; `action dash` -> "Action" with time "1 action"; each card ASCII at 32 cols.
- [ ] **Step 2: Run** — fails.
- [ ] **Step 3: Implement** three loaders and builders, register kinds after class_ability.
- [ ] **Step 4: Run** — pass.
- [ ] **Step 5: Commit** `feat: feat, condition and action cards`.

### Task 7: Registry order, docs, sweep

**Files:**
- Modify: `tcard/sources/fivee/__init__.py` (order: spell, item, class_ability, optional kinds, feat, condition, action), `README.md`, `docs/superpowers/specs/2026-11-18-tcard.md`
- Test: `tests/test_cli.py` (order), `tests/test_sweep.py` (all cached records render at 32 cols)

- [ ] **Step 1: Write failing test** — `kinds()` order starts `["spell", "item", "class_ability"]`; `tcard shield` still resolves the spell.
- [ ] **Step 2: Run** — fails.
- [ ] **Step 3: Implement** ordering plus README/spec updates.
- [ ] **Step 4: Run full suite + live checks** — `python3 tests/run.py`; `python3 -m tcard bag_of_holding`, `fighter:second_wind`, `invocation agonizing_blast`, `condition prone`.
- [ ] **Step 5: Commit** `docs: document new content kinds`.
