[![ORGAN-V: Logos](https://img.shields.io/badge/ORGAN--V-Logos-0d47a1?style=flat-square)](https://github.com/organvm-v-logos) [![CI](https://github.com/organvm-v-logos/reading-observatory/actions/workflows/ci.yml/badge.svg)](https://github.com/organvm-v-logos/reading-observatory/actions/workflows/ci.yml) [![Tier: Standard](https://img.shields.io/badge/tier-standard-4fc3f7?style=flat-square)](#how-it-fits-the-system) [![Status: Shipped](https://img.shields.io/badge/status-shipped-brightgreen?style=flat-square)](https://github.com/organvm-v-logos/reading-observatory/releases)

# reading-observatory

_Curated reading lists, bibliography management, and RSS aggregation for the ORGAN-V discourse layer_

---

> **Status: SHIPPED**
>
> reading-observatory is deployed and active with published release artifacts, CLI entrypoints (`observatory-aggregate`, `observatory-validate`, `observatory-newsletter`), 80 tests, 4 curated bibliography collections, 13 RSS feed subscriptions, automated release workflows, and a weekly aggregation pipeline.

---

## Current State

As of 2026-02-24, this repository contains:

- `src/` — 4 Python modules: config, bibliographies, feeds, matcher, aggregator
- `tests/` — 67 tests across 5 test modules with fixtures
- `bibliographies/` — 4 curated YAML collections (17 entries)
- `feeds/subscriptions.opml` — 13 RSS/Atom feed subscriptions
- `feeds/seen.json`, `feeds/surfaced.json` — Pipeline state files
- `config/scoring.yaml` — Scoring parameters
- `.github/workflows/ci.yml` — Full CI (ruff + pytest + bibliography validation)
- `.github/workflows/weekly-feeds.yml` — Monday 06:00 UTC cron aggregation
- `seed.yaml` — `implementation_status: CANDIDATE`
- `docs/adr/` — Architecture decision records
- `README.md`, `CHANGELOG.md`, `LICENSE`

Both produce edges are fulfilled:
- `curated-reading-lists` → `bibliographies/*.yaml`
- `relevant-articles` → `feeds/surfaced.json`

---

## Architecture

### Overview

reading-observatory is the intellectual intake system for ORGAN-V: Logos. It performs three interconnected functions: it curates bibliographies of works that inform the eight-organ system's conceptual foundations, it monitors external RSS feeds for articles and essays relevant to the system's active themes, and it surfaces discovered material as potential inputs to the essay-writing pipeline that powers the public-process discourse layer.

The repository is not a link-dump or a bookmarks folder. Each bibliography entry carries structured metadata describing not just what a source is but why it matters to a specific theme within the system. Each feed subscription is justified by its relevance to at least one of the four core collections. Each surfaced article is matched against the current set of essay tags, so the pipeline receives not just "here is something interesting" but "here is something interesting that connects to work you are already doing."

The observatory metaphor is deliberate. An observatory does not create the phenomena it studies. It provides instruments for careful, sustained observation. reading-observatory provides instruments for careful, sustained observation of the intellectual landscape that surrounds and informs the eight-organ creative-institutional system.

## Why an Observatory

The word "observatory" carries connotations that matter here. An observatory is a place built specifically for watching. It implies patience, regularity, and the use of calibrated instruments. It implies that what you are watching is larger than you, that you cannot control it, and that your job is to notice patterns in what arrives.

The eight-organ system generates a great deal of internal writing, design documentation, and process essays. That internal production can become self-referential if it is not regularly confronted with external thought. reading-observatory exists to prevent that insularity. It watches the broader landscape of systems thinking, creative practice, institutional design, and AI-human collaboration, and it routes relevant discoveries back into the system's essay pipeline.

The observatory metaphor also implies selectivity. An astronomical observatory does not try to photograph every star. It has research programs, pointing strategies, and criteria for what counts as a discovery worth reporting. Similarly, reading-observatory does not aggregate every RSS feed on the internet. It maintains a curated OPML file of feeds chosen for their relevance, and it applies keyword matching to filter the resulting stream down to items that connect to the system's active concerns.

This is not a recommendation engine. It does not try to predict what the human operator will find interesting. It tries to surface what is relevant to the work the system is currently doing, as expressed by the tags attached to published essays and active bibliography collections.

## Collections

reading-observatory maintains four bibliography collections, each corresponding to a major thematic axis of the eight-organ system. These collections are not mutually exclusive. A single source can appear in multiple collections if it is relevant to more than one theme. The collections are stored as YAML files in the `bibliographies/` directory.

### systems-thinking

Works on cybernetics, complexity theory, feedback loops, emergence, and the design of systems that exhibit coherent behavior at multiple scales. This collection directly informs the architectural decisions behind the eight-organ structure itself: the principle that organs should be loosely coupled, that governance should be distributed, that the system should be observable from the inside. Key authors include Stafford Beer, Donella Meadows, W. Ross Ashby, and Niklas Luhmann, but the collection extends to contemporary writing on organizational design, software architecture patterns (especially those that borrow from biological or ecological models), and the mathematics of networks and hierarchies.

### creative-practice

Works on artistic process, the relationship between constraints and creativity, generative systems in art and music, and the philosophy of making. This collection feeds primarily into ORGAN-II (Poiesis) but also informs the essay pipeline's treatment of creative-institutional synthesis. It includes writing on computational art, live coding, modular synthesis philosophy, choreographic notation, theatre improvisation structures, and the broader question of what it means to build systems that produce aesthetic output. The emphasis is on practice, not theory alone: books and essays that describe how people actually make things, what decisions they face, and what structures they build to support sustained creative work.

### institutional-design

Works on governance, organizational theory, commons management, cooperative structures, and the design of institutions that serve their members without ossifying into bureaucracy. This collection is particularly relevant to ORGAN-IV (Taxis) and ORGAN-VI (Koinonia), which handle orchestration and community governance respectively. It includes classic works on institutional economics (Elinor Ostrom), contemporary writing on platform cooperativism and decentralized governance, and practical guides to running organizations that need to balance autonomy with coordination. The collection also covers documentation culture, knowledge management, and the design of processes that remain legible over time.

### ai-human-collaboration

Works on the practical, philosophical, and ethical dimensions of building systems where humans and AI agents work together. This collection is the most rapidly evolving of the four, because the landscape it observes is changing faster than any of the others. It includes writing on prompt engineering, AI-assisted creative practice, the design of human-in-the-loop systems, alignment research (at the practical rather than theoretical level), and the emerging conventions around AI co-authorship, attribution, and tool use. The collection is particularly interested in sources that treat AI collaboration not as a futuristic speculation but as a current working practice with real design decisions to be made.

## Feed Aggregation

reading-observatory monitors external RSS and Atom feeds for articles relevant to the four collections. The feed list is stored in `feeds/subscriptions.opml`, using the standard OPML format so it can be imported into any feed reader for manual browsing.

The aggregation pipeline runs weekly (Monday mornings, 06:00 UTC) via scheduled workflow. It performs the following steps:

1. **Fetch**: Download new items from all subscribed feeds since the last run.
2. **Deduplicate**: Skip items already seen (tracked by URL hash in `feeds/seen.json`).
3. **Extract**: Pull title, author, publication date, URL, and a text summary from each new item.
4. **Match**: Compare each item's title and summary text against the current keyword set, which is derived from the tags attached to published essays in public-process and from the tags in all four bibliography collections.
5. **Score**: Assign a relevance score based on keyword density and collection affinity.
6. **Output**: Write matched items (score above threshold) to `feeds/surfaced.json`, which the essay pipeline can consume.

Items that score below the threshold are silently discarded. Items that score above the threshold but are not acted upon within 30 days are moved to `feeds/archive/`. The pipeline is intentionally conservative: it is better to miss a relevant article than to flood the essay pipeline with noise.

The surfaced-item schema is documented in [`docs/data-contract-surfaced-items.md`](docs/data-contract-surfaced-items.md) and is synchronized with `essay-pipeline`'s consumer contract.

The OPML file is organized into four outline groups matching the four collections. A feed can appear in multiple groups if it publishes content relevant to more than one collection. Adding a new feed requires editing the OPML file directly and committing the change; there is no web interface or API for feed management. This is intentional. Adding a feed is a curatorial decision that should be made deliberately, not impulsively.

## Architecture

The core of reading-observatory is a modular Python package in `src/` implementing the fetch-deduplicate-extract-match-score-output pipeline. The pipeline is stateless between runs except for `feeds/seen.json` (tracks already-processed URLs) and `feeds/surfaced.json` (items above the scoring threshold). It reads the OPML subscription list, fetches feeds using `feedparser`, performs keyword matching using simple TF-IDF scoring (no external ML models or APIs per ADR-001), and writes results to JSON.

```
reading-observatory/
  pyproject.toml              # Package definition (feedparser + pyyaml)
  src/
    config.py                 # ScoringConfig, PathsConfig, ObservatoryConfig
    bibliographies.py         # Load, validate, extract tags from YAML
    feeds.py                  # OPML parse, fetch feeds, deduplicate
    matcher.py                # Vocabulary building, TF-IDF scoring
    aggregator.py             # Pipeline orchestration + CLI
  tests/                      # 67 tests across 5 modules
    fixtures/                 # YAML, XML, JSON test fixtures
  config/
    scoring.yaml              # min_score, expiry_days, max_surfaced
  feeds/
    subscriptions.opml        # 13 curated feeds in 4 groups (OPML)
    seen.json                 # URL hashes of already-processed items
    surfaced.json             # Items that passed keyword matching
    archive/                  # Expired surfaced items (>30 days)
  bibliographies/
    systems-thinking.yaml     # 5 entries
    creative-practice.yaml    # 4 entries
    institutional-design.yaml # 4 entries
    ai-human-collaboration.yaml # 4 entries
  docs/adr/
    001-initial-architecture.md
    002-curation-philosophy.md
  .github/workflows/
    ci.yml                    # ruff + pytest + bibliography validation
    weekly-feeds.yml          # Monday 06:00 UTC cron
```

The architecture is deliberately simple. There is no database, no web server, no user interface. The bibliographies are YAML files edited by hand. The feed list is an OPML file edited by hand. The aggregator is a script that runs on a schedule. Everything is version-controlled and reviewable through normal git workflows.

This simplicity is a design choice, not a limitation. The observatory's value comes from the quality of its curation, not the sophistication of its infrastructure. A complex system for managing reading lists would add maintenance burden without improving the quality of the reading lists themselves.

## How Bibliographies Are Structured

Each bibliography entry is a YAML document with the following fields:

```yaml
- title: "Thinking in Systems: A Primer"
  author: "Donella H. Meadows"
  year: 2008
  url: "https://www.chelseagreen.com/product/thinking-in-systems/"
  relevance: >
    Foundational text on feedback loops, stocks and flows, and system
    archetypes. Directly informs the eight-organ architecture's approach
    to loose coupling and distributed governance.
  tags:
    - systems-thinking
    - feedback-loops
    - emergence
    - governance
  notes: >
    Chapter 6 on leverage points is particularly relevant to the
    orchestration layer (ORGAN-IV). The hierarchy discussion in
    Chapter 3 maps onto the organ/repo/file layering.
  collections:
    - systems-thinking
    - institutional-design
```

**Required fields**: `title`, `author`, `year`, `relevance`, `tags`, `collections`.

**Optional fields**: `url`, `notes`, `isbn`, `doi`, `edition`, `publisher`.

The `relevance` field is the most important. It does not describe the book in general terms. It describes specifically why this source matters to the eight-organ system. A bibliography entry without a meaningful `relevance` field is incomplete and should not be merged.

The `tags` field serves double duty. Tags are used for organizing entries within and across collections, and they are also used as the keyword set that the feed aggregator matches against. When a new bibliography entry adds a tag that did not previously exist, the feed aggregator's matching vocabulary expands automatically on its next run.

The `collections` field lists which of the four bibliography collections this entry belongs to. An entry must belong to at least one collection.

## Integration with the Essay Pipeline

reading-observatory does not exist in isolation. It is one input to the broader ORGAN-V essay pipeline. The integration works through two mechanisms:

**Topic suggestions**: When the feed aggregator surfaces an article with a high relevance score, the item appears in `feeds/surfaced.json` with its matched tags and score. The essay-pipeline repository (when active) can read this file to generate topic suggestions. A surfaced article about, say, "cooperative governance in open-source projects" that matches tags from both the institutional-design and ai-human-collaboration collections might suggest an essay exploring the intersection of those themes.

**Tag expansion**: When a new essay is published in public-process with new tags, those tags propagate back to the observatory's keyword matching vocabulary. This creates a feedback loop: writing about a topic makes the observatory more sensitive to related material, which surfaces more potential inputs, which may inspire further writing. The loop is bounded by the conservative scoring threshold and the requirement for human review, so it converges rather than exploding.

**Bibliography citations**: Essays published through the public-process pipeline can reference bibliography entries directly. The structured YAML format makes it straightforward to generate citation lists, further reading sections, and cross-references between essays and their source material.

## Development

### Prerequisites

- Python 3.10+
- `feedparser` library (`pip install feedparser`)
- `pyyaml` library (`pip install pyyaml`)

### Setup

```bash
git clone https://github.com/organvm-v-logos/reading-observatory.git
cd reading-observatory
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

No database setup is required. No environment variables need to be configured. The repository is self-contained: all state lives in flat files (YAML, JSON, OPML) that are version-controlled alongside the code.

### Package Entrypoints & CLI Commands

`reading-observatory` exposes three primary CLI entrypoints:

```bash
# 1. Run feed aggregation (or smoke test dry-run)
observatory-aggregate --dry-run
observatory-aggregate --essays-index ../public-process/data/essays-index.json

# 2. Validate bibliographies YAML schema
observatory-validate bibliographies/

# 3. Generate curated reading list newsletter
observatory-newsletter --surfaced feeds/surfaced.json --output docs/newsletter.md
```

### Running the Feed Aggregator

```bash
observatory-aggregate
# or via module:
python -m src.aggregator
```

The pipeline reads `feeds/subscriptions.opml`, fetches all subscribed feeds, applies keyword matching against the vocabulary built from bibliography tags and essay tags, and writes results to `feeds/surfaced.json`. Run it manually during development or let the scheduled workflow handle it in production.

To run a dry run that loads vocabularies without fetching feeds:

```bash
observatory-aggregate --dry-run
```

To point at a specific essays-index.json:

```bash
observatory-aggregate --essays-index ../public-process/data/essays-index.json
```

### Running Tests

```bash
pytest tests/ -v
ruff check src/ tests/
```

### Validating Bibliographies

```bash
observatory-validate bibliographies/
# or via module:
python -m src.bibliographies --validate bibliographies/
```

### Release Pipeline

Releases are published automatically via `.github/workflows/release.yml` when a version tag (e.g. `v0.2.0`) is pushed to the repository. The workflow builds Python wheel and source distribution packages and publishes them to GitHub Releases.

### Adding a New Feed

1. Open `feeds/subscriptions.opml` in a text editor.
2. Add a new `<outline>` element inside the appropriate collection group.
3. Include the feed title, XML URL, and HTML URL.
4. Commit the change with a message explaining why this feed is relevant.

Adding a feed is a curatorial decision. Before adding, consider: Does this source publish regularly? Is its content substantive enough to warrant monitoring? Does it cover themes that are not already well-represented by existing feeds? A feed that duplicates coverage you already have adds noise without adding signal.

### Adding a Bibliography Entry

1. Open the appropriate bibliography YAML file in `bibliographies/`.
2. Add a new entry following the schema described above.
3. Ensure the `relevance` field explains specifically why this source matters to the eight-organ system, not just what the source is about in general.
4. Ensure the `tags` field includes terms that are specific enough to be useful for keyword matching but broad enough to connect to other entries.
5. Ensure the `collections` field lists at least one collection.
6. Commit the change with a message that names the source and the collection(s).

### Validating YAML

The CI pipeline validates all YAML files on every push. You can also validate locally:

```bash
python -c "import yaml, glob; [yaml.safe_load(open(f)) for f in glob.glob('**/*.yaml', recursive=True)]"
```

This checks that all YAML files parse without errors. It does not validate the schema of bibliography entries (required fields, valid collection names). Schema validation is planned for a future iteration.

## How It Fits the System

reading-observatory is part of **ORGAN-V: Logos**, the public-process and discourse layer of the eight-organ creative-institutional system.

| Organ | Name | Domain | Relationship |
|-------|------|--------|-------------|
| I | Theoria | Foundational theory & recursive engines | Sources for systems-thinking collection |
| II | Poiesis | Creative production & synthesis | Sources for creative-practice collection |
| III | Ergon | Commercial applications & tools | Indirect (tooling references) |
| IV | Taxis | Orchestration & governance | Sources for institutional-design collection |
| **V** | **Logos** | **Public process & discourse** | **reading-observatory lives here** |
| VI | Koinonia | Community & collaboration | Sources for ai-human-collaboration collection |
| VII | Kerygma | Outreach & communication | Consumes surfaced reading for content |
| META | meta-organvm | System-wide coordination | Observatory serves all organs |

reading-observatory produces curated reading lists and surfaced articles. These outputs flow into the essay-pipeline (ORGAN-V) as topic suggestions and citation material. The four bibliography collections are aligned with the system's major thematic axes, ensuring that the observatory's coverage maps onto the system's actual concerns rather than drifting into general-purpose bookmarking.

## Contributing

Contributions to reading-observatory take two primary forms:

**Bibliography contributions**: Suggest a new entry for one of the four collections. Open a pull request with the YAML entry added to the appropriate bibliography file. The most important part of your contribution is the `relevance` field: it must explain specifically how and why this source connects to the eight-organ system's concerns, not just summarize the source in general terms. Entries without a specific, substantive relevance statement will be returned for revision. If you are unsure which collection a source belongs to, include it in the pull request description and we will discuss placement during review.

**Feed suggestions**: Suggest a new RSS/Atom feed to monitor. Open an issue describing the feed, which collection(s) it relates to, and why it is worth monitoring. Include a sample of recent posts from the feed to illustrate its relevance. If accepted, the OPML file will be updated. Feeds that go dormant (no new posts in 6 months) are periodically reviewed and may be removed.

**Bug reports and feature requests**: If you encounter issues with the feed aggregator or have suggestions for improving the matching pipeline, open an issue with a clear description of the problem or proposal. Include concrete examples where possible.

For general contribution guidelines, see the [ORGAN-V contributing guide](https://github.com/organvm-v-logos/.github/blob/main/CONTRIBUTING.md).

## License

[MIT](LICENSE) -- 2026 [@4444J99](https://github.com/4444J99)

---

<sub>reading-observatory -- ORGAN V: Logos -- part of the eight-organ creative-institutional system -- [@4444j99](https://github.com/4444j99) -- LOGOS Sprint 2026-02-17</sub>
