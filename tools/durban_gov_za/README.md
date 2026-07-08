# eThekwini (Durban) schedule updater

Fork-only tooling that downloads regional DOCX schedules from
[durban.gov.za](https://www.durban.gov.za/page/refuse-collection-schedules),
parses area-to-weekday mappings, and regenerates the `COLLECTION_AREAS` block in
`durban_gov_za.py`.

This directory is **not** submitted upstream. Upstream PRs contain only the
generated provider file, documentation, and the `za` country-code entry.

## Setup

```bash
pip install -r tools/durban_gov_za/requirements.txt
```

## Update the mapping

From the repository root:

```bash
python tools/durban_gov_za/update.py
```

Options:

- `--dry-run` — fetch and parse without writing files
- `--target PATH` — path to `durban_gov_za.py` (default: repo source file)
- `--cache-dir PATH` — download directory (default: `tools/durban_gov_za/downloads`)
- `--verify-ssl` — enable SSL certificate verification (disabled by default due to
  durban.gov.za certificate issues in some environments)

## Regenerate from cached DOCX only

If you already have DOCX files in `downloads/`:

```bash
python tools/durban_gov_za/generate_mapping.py \
  --target custom_components/waste_collection_schedule/waste_collection_schedule/source/durban_gov_za.py \
  --cache-dir tools/durban_gov_za/downloads
```

## Clean upstream PR workflow

1. Keep this tooling on `tooling/durban-updater` in your fork.
2. Run `update.py` to refresh the mapping.
3. Create a clean branch from `upstream/master` with only:
   - `custom_components/.../source/durban_gov_za.py`
   - `doc/source/durban_gov_za.md`
   - `update_docu_links.py` (`za` country code)
4. Open a PR to `mampfes/hacs_waste_collection_schedule:master`.

Example using a worktree:

```bash
git worktree add ../hacs-durban-pr upstream/master -b source/durban-gov-za
cp custom_components/waste_collection_schedule/waste_collection_schedule/source/durban_gov_za.py \
   ../hacs-durban-pr/custom_components/waste_collection_schedule/waste_collection_schedule/source/
cp doc/source/durban_gov_za.md ../hacs-durban-pr/doc/source/
cp update_docu_links.py ../hacs-durban-pr/
```

## Tests

```bash
PYTHONPATH=tools/durban_gov_za python -m pytest tools/durban_gov_za/tests/
```

Parser fixtures live in `tests/fixtures/`. Full DOCX downloads are cached under
`downloads/` (gitignored).
