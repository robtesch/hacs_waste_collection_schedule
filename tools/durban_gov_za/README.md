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

## Fork branch layout

This fork is split so upstream stays easy to sync while Durban-specific work
lives on dedicated branches.

| Branch | Purpose |
|---|---|
| `master` | Mirrors `mampfes/hacs_waste_collection_schedule:master` only — sync, do not develop here |
| `tooling/durban-updater` | **GitHub default branch.** Tooling, CI workflows, Durban updater Action |
| `data/durban-gov-za` | Hosted ICS calendars + `index.json` (orphan data branch) |
| `source/durban-gov-za-ics` | Clean upstream PR branches (always cut from `upstream/master`) |

### Why `tooling/durban-updater` is the default branch

GitHub only runs **scheduled** workflow cron jobs from the repository's **default
branch**. The Durban calendar updater needs a weekly schedule, but we also want
`master` to remain a clean mirror of upstream (no fork-only commits to re-apply
after every sync).

Making `tooling/durban-updater` the default branch gives us both:

- `master` stays identical to upstream — easy to reset/merge when upstream moves
- The updater workflow (`.github/workflows/update-durban-gov-za.yml`) runs on its
  Monday 06:00 UTC schedule without adding fork-only files to `master`

The trade-off is that `git clone` and the fork's GitHub landing page open on the
tooling branch rather than `master`. That is fine for a personal infrastructure
fork with a single maintainer.

**Default branch setting:** `tooling/durban-updater` (verify under GitHub →
Settings → General → Default branch).

### Keeping `master` in sync with upstream

From your local clone:

```bash
git fetch upstream
git checkout master
git reset --hard upstream/master
git push origin master
```

Do not merge `tooling/durban-updater` into `master`. Upstream PRs are prepared
from `upstream/master` via a worktree (see below), not from fork `master`.

## Automated weekly update

A GitHub Actions workflow (`.github/workflows/update-durban-gov-za.yml`) lives on
`tooling/durban-updater` (the fork default branch) and watches for changes in
the council's published DOCX schedules. Do **not** include it in upstream PRs.

The workflow uses plain `git`/`pip` shell steps for compatibility. If you prefer,
you can switch to `actions/checkout` and `actions/setup-python`.

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
