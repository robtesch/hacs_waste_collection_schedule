# eThekwini (Durban) schedule updater

Fork-only tooling that downloads regional DOCX schedules from
[durban.gov.za](https://www.durban.gov.za/page/refuse-collection-schedules),
parses area-to-weekday mappings, and publishes hosted ICS calendars on the
`data/durban-gov-za` branch.

This directory is **not** submitted upstream. Upstream PRs contain only the
ICS-fetching provider file, documentation, and the `za` country-code entry.

## Hosted calendars

Generated output lives on branch **`data/durban-gov-za`**:

```
/
├── index.json
└── calendars/
    └── {region}/
        └── {area}.ics
```

Public URLs (used by the upstream `durban_gov_za` source):

- `https://raw.githubusercontent.com/robtesch/hacs_waste_collection_schedule/refs/heads/data/durban-gov-za/index.json`
- `https://raw.githubusercontent.com/robtesch/hacs_waste_collection_schedule/refs/heads/data/durban-gov-za/calendars/{region}/{area}.ics`

## Automated weekly update

A GitHub Actions workflow (`.github/workflows/update-durban-gov-za.yml`) runs on
your fork to watch for changes in the council's published DOCX schedules. Keep
this workflow on your fork's `master` branch — do **not** include it in upstream
PRs.

The workflow uses plain `git`/`pip` shell steps because some forks restrict
third-party GitHub Actions. If your fork allows marketplace actions, you can
switch back to `actions/checkout` and `actions/setup-python` if you prefer.

| When | How |
|------|-----|
| **Schedule** | Every Monday at 06:00 UTC |
| **Manual run** | Actions → *Update Durban schedule calendars* → *Run workflow* |

**What it does each run:**

1. Checks out `tooling/durban-updater` and the `data/durban-gov-za` branch.
2. Downloads the latest regional DOCX files from durban.gov.za and parses them.
3. Regenerates `index.json` and per-area ICS files on `data/durban-gov-za`.
4. Commits and pushes when the hosted calendars changed.

## Setup

```bash
pip install -r tools/durban_gov_za/requirements.txt
```

## Update hosted calendars locally

From the repository root:

```bash
python tools/durban_gov_za/update.py --output-dir /path/to/data/durban-gov-za/checkout
```

The default output directory is `data/durban-gov-za/` at the repo root.

Options:

- `--dry-run` — fetch and parse without writing files
- `--output-dir PATH` — data branch root (default: `data/durban-gov-za`)
- `--cache-dir PATH` — download directory (default: `tools/durban_gov_za/downloads`)
- `--verify-ssl` — enable SSL certificate verification (disabled by default due to
  durban.gov.za certificate issues in some environments)

## Regenerate from cached DOCX only

If you already have DOCX files in `downloads/`:

```bash
python tools/durban_gov_za/generate_mapping.py \
  --target /tmp/unused.py \
  --cache-dir tools/durban_gov_za/downloads
```

For ICS output from cache, call `update.py` with a populated `downloads/` folder
after placing `source_links.json` there, or run the full `update.py` fetch.

## Clean upstream PR workflow

1. Keep this tooling on `tooling/durban-updater` in your fork.
2. Push hosted calendars to `data/durban-gov-za` before opening the upstream PR.
3. Create a clean branch from `upstream/master` (e.g. `source/durban-gov-za-ics`) with only:
   - `custom_components/.../source/durban_gov_za.py`
   - `doc/source/durban_gov_za.md`
   - `update_docu_links.py` (`za` country code)
4. Open a PR to `mampfes/hacs_waste_collection_schedule:master`.

Example using a worktree:

```bash
git fetch upstream
git worktree add ../hacs-durban-ics upstream/master -b source/durban-gov-za-ics
cp custom_components/waste_collection_schedule/waste_collection_schedule/source/durban_gov_za.py \
   ../hacs-durban-ics/custom_components/waste_collection_schedule/waste_collection_schedule/source/
cp doc/source/durban_gov_za.md ../hacs-durban-ics/doc/source/
cp update_docu_links.py ../hacs-durban-ics/
```

## Tests

```bash
PYTHONPATH=tools/durban_gov_za python -m pytest tools/durban_gov_za/tests/
```

Parser fixtures live in `tests/fixtures/`. Full DOCX downloads are cached under
`downloads/` (gitignored).
