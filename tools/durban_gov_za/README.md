# eThekwini (Durban) schedule updater

Fork-only tooling that downloads regional DOCX schedules from
[durban.gov.za](https://www.durban.gov.za/page/refuse-collection-schedules),
parses area-to-weekday mappings, and regenerates the `COLLECTION_AREAS` block in
`durban_gov_za.py`.

This directory is **not** submitted upstream. Upstream PRs contain only the
generated provider file, documentation, and the `za` country-code entry.

## Automated weekly check

A GitHub Actions workflow (`.github/workflows/update-durban-gov-za.yml`) runs on
your fork to watch for changes in the council's published DOCX schedules. Keep
this workflow on your `tooling/durban-updater` branch — do **not** include it in
upstream PRs.

| When | How |
|------|-----|
| **Schedule** | Every Monday at 06:00 UTC |
| **Manual run** | Actions → *Update Durban schedule mapping* → *Run workflow* |

**What it does each run:**

1. Installs the updater dependencies.
2. Downloads the latest regional DOCX files from durban.gov.za and parses them.
3. Regenerates the `COLLECTION_AREAS` block in `durban_gov_za.py` (in the
   ephemeral CI checkout — nothing is committed automatically).
4. Runs `ruff check --fix` and `ruff format` on the source file so the diff
   reflects mapping changes only, not formatting drift.
5. Compares the result against the committed source file.

**If the mapping changed**, the workflow opens a GitHub issue titled *"Durban
schedule mapping update available"*. The issue is a reminder to review the new
mapping and cut a clean upstream PR — it does not open a PR or push commits for
you.

**When you see that issue:**

1. Check out `tooling/durban-updater` locally.
2. Run `python tools/durban_gov_za/update.py` to refresh the mapping.
3. Follow the [clean upstream PR workflow](#clean-upstream-pr-workflow) below.
4. Close the issue once the upstream PR is open (or merged).

If no mapping changes are detected, the workflow finishes silently.

The `# Based on schedules dated:` comment in the generated block is derived from the
newest `YYYY/MM/DD` segment in the council DOCX URLs, not the date the updater was
run. That keeps weekly runs stable when the published schedules have not changed.

## Setup

```bash
pip install -r tools/durban_gov_za/requirements.txt
```

## Update the mapping

From the repository root:

```bash
python tools/durban_gov_za/update.py
```

The script runs `ruff check --fix` and `ruff format` on the target file after
writing the generated block, so output matches repo style before you commit or
open a PR.

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
