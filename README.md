# Autopsy of a Startup Idea

Reproducible figures and aggregate evidence for **Applied Overthinking**, reflecting on the development and evaluation of Even, a prototype for exploring triathlon performances and finding potential training partners.

This repository contains the code and public inputs behind the article's five figures. The application itself is maintained separately.

## Figures

| Article figure | Preview | Vector PDF |
| --- | --- | --- |
| Race entries in the data by year | [PNG](figures/01-race-results-by-year.png) | [PDF](figures/01-race-results-by-year.pdf) |
| Recorded activity over time | [PNG](figures/02-cumulative-recorded-events.png) | [PDF](figures/02-cumulative-recorded-events.pdf) |
| Daily session starts | [PNG](figures/03-daily-sessions.png) | [PDF](figures/03-daily-sessions.pdf) |
| How weekly session cohorts progressed | [PNG](figures/04-weekly-session-cohorts.png) | [PDF](figures/04-weekly-session-cohorts.pdf) |
| What five triathletes told me: Learnings from user correspondences | [PNG](figures/05-qualitative-feedback.png) | [PDF](figures/05-qualitative-feedback.pdf) |

[Download all figures](figures/article-figures.zip). PNGs are rendered at 300 dpi. PDFs contain vector text and graphics. A local preview gallery is included as `figures/index.html`.

## Reproduce the figures

Use Python 3.10 and the pinned plotting dependencies:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/export_figures.py
```

This rebuilds all five figures, the preview gallery and the ZIP using the included public data. No private database, original messages, account credentials or network access are needed after dependencies are installed.

To write figures elsewhere:

```sh
python scripts/export_figures.py --out /tmp/even-figures
```

The qualitative table can also be exported independently:

```sh
python scripts/export_feedback_table.py --out /tmp/feedback-table.pdf
```

## Public inputs

- [`data/aggregate-report.json`](data/aggregate-report.json): daily usage totals, weekly session cohorts, action counts, funnel counts and summary timing statistics, together with archive totals.
- [`data/archive-summary.json`](data/archive-summary.json): yearly race-entry counts and coverage, completion status totals, and counts of nonempty source fields. No athlete-level rows are included.
- [`data/qualitative-coding.json`](data/qualitative-coding.json): only anonymous labels P01–P05 and the approved learning/participant/takeaway matrix.
- [`data/development.json`](data/development.json): codebase snapshots, per-commit source additions/removals and the definitions used to compute them. Author identities and email addresses are not included.

The usage evidence is a fixed snapshot exported on **October 31, 2026**. It contains **1,004 recorded events across 60 observed browser-tab session IDs**. Of the events, **429 are engagement heartbeats** and **575 are other events**, including page views and product actions. Twenty-seven sessions contain searches, 25 reach matches and 12 load comparisons. The race archive contains **1,495,743 entries across 897 race editions**.

## Interpretation and limitations

- Session IDs do not identify unique people. Some span multiple receipt dates. Daily starts count the date an identifier was first observed; they are not daily active people or retention measurements.
- Creator/testing activity is included. Browser privacy settings, opt-out and failed delivery can hide activity. Only selected product actions were recorded; the collector did not capture every click or scroll.
- Weekly cohorts use Monday start dates in Pacific time. Outcome counts reflect session-level reach, not an ordered funnel. First and last weeks are partial.
- Cumulative events include engagement heartbeats. A rising cumulative curve establishes recorded activity, not sustained demand. Exact receipt times and raw event records are not published.
- Shares measure clicks and device handoff, not confirmed delivery or a growth loop. Historical race entries are not participating members.
- The qualitative matrix is manually reviewed exploratory coding of five correspondence extracts. The respondents were a convenience sample, not a survey. All expressed positivity; the extract for P05 contains an intention to try rather than specific post-trial observations. P01 and P02 describe one off-site referral chain.
- Original correspondence, verbatim excerpts, names, contact details, respondent background/relationship notes and identity mappings are excluded. Anonymous labels are not linked to usage sessions.
- Archive coverage varies by year; the 2026 archive is a partial-year snapshot. Race entries are not unique athletes, and nonempty fields are not necessarily accurate.
- Source churn is **2,278 added and 130 removed lines**, including tests, across 13 product commits. The first product diff uses the inspected inherited baseline; later diffs use the preceding product snapshot. Code size includes comments and blank lines. Commits do not establish hours worked or distinguish agent-authored from human-authored edits.

## Aggregate new private inputs locally

These optional tools are for someone who already has authorized access to the source inputs. Keep those inputs outside this repository; publish only reviewed aggregates.

```sh
python scripts/aggregate_usage.py \
  --input /path/to/private-export.json \
  --out /tmp/aggregate-report.json

python scripts/aggregate_races.py \
  --results /path/to/race-csvs \
  --out /tmp/archive-summary.json

python scripts/git_metrics.py \
  --repo /path/to/application-checkout \
  --out /tmp/development.json
```

The usage aggregator explicitly constructs its output fields. It never reads feedback, heart-recipient or withdrawal tables, and never emits individual event records or session/page identifiers. The code-metrics script requires the historical commits listed in the included manifest; their aggregate measurements are included so readers do not need access to the application checkout.

## Verification and publication checks

```sh
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests
python scripts/audit_publication.py
```

The audit checks the release tree, JSON field structure, PDF text/metadata, PNG metadata and files inside the figure ZIP. It rejects email addresses, UUIDs, local home-directory paths and private data fields. An optional `--private-reference` argument can check respondent names from an unpublished coding file; that input is never copied into the release.

The tests verify the published totals and ensure that synthetic private messages, recipient information and session identifiers cannot leave the aggregation function. GitHub Actions also regenerates the figures and runs the publication audit.

## License

Code and figure designs are available under the [MIT License](LICENSE). Published aggregate statistics and the anonymous coding matrix accompany the article for inspection and reproduction. The license does not grant rights to original correspondence or underlying athlete-level race records, neither of which is included here.
