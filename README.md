# LLM4Rail — How Much Can LLMs Help Solve Railway Optimization Problems?

**English** | [简体中文](README.zh-CN.md)

Research website for LLM4Rail. A static site for GitHub Pages: no build step and no dependencies.

## Structure

- `index.html` — overview (English): the question, problem library, gap chart, method, verification, roadmap, citation
- `instances/` — searchable catalogue of 166 instances (English)
- `zh/index.html`, `zh/instances/` — the same two pages in Chinese
- `assets/js/i18n.js` — Chinese and English labels for the table and chart (sets, statuses, units)
- `data/instances.json`, `data/instances.csv` — catalogue data for download
- `assets/js/data.js` — the same data, loaded by the pages (works from `file://` too)
- `assets/css/site.css` — all styles; brand colours are CSS variables at the top
- `assets/img/` — logo files; `favicon.*` and `apple-touch-icon.png` at the root

## Deploy

1. The intended public site is [LLM4Rail on GitHub Pages](https://llm4rail.github.io/), published from `LLM4Rail/llm4rail.github.io`. A private organisation repository requires a GitHub plan that supports Pages on private repositories.
2. In Settings → Pages, choose "Deploy from a branch", branch `main`, folder `/ (root)`.
3. Push the site files to `main`.

## Before publishing

Replace these placeholders:

- Affiliations are intentionally left empty; if needed, add them to the hero line in `index.html` and `zh/index.html` (authors are filled in)
- `https://github.com/LLM4Rail/llm4rail.github.io` if the repository lives elsewhere
- The roadmap dates in section 06, if the plan changes
- The news item date (both languages)

Static text lives in the HTML of each language; keep `index.html` and `zh/index.html` in step when you edit one of them.

## Updating data

Edit `data/instances.json`, then regenerate the CSV download and the site's JavaScript data together.

```sh
python3 scripts/export_instances.py
python3 scripts/validate_results.py   # add --evidence-root DIR to check evidence bundles
```

The validator checks the baseline fields (gap, status, bound order), every LLM4Rail result, the bilingual labels, and that the CSV and JavaScript data are up to date. It exits non-zero on any error. Its tests run with `python3 -m unittest discover -s scripts -p 'test_*.py'`.

- `library` and `instance` together identify a catalogue entry. A shared `family` marks confirmed related models, which count as separate entries.
- `n1` and `n2` give the size in events and activities (`ev_act`), trains and operations (`tr_op`), or variables and constraints (`var_con`).
- `record`, `source`, and `upper_evidence` describe `best_known`. `bound_record`, `bound_source`, and `bound_evidence` describe `best_bound`.
- `gap` is the difference between the bounds divided by the absolute upper bound. Equal bounds give zero gap. Status codes are `open`, `optimal`, and `no_bound`. The table labels for sets, statuses, and evidence codes are in `assets/js/i18n.js`.

When a new result is verified, update the affected value and its evidence fields, then reconcile `gap`, `status`, and the totals in both languages. Set `llm4rail` and add its bilingual labels to `i18n.js` when publishing a project result.

A project result (`llm4rail` other than `pending`) also carries `llm4rail_primal` and/or `llm4rail_dual`, `primal_gain` / `dual_gain`, `primal_evidence` / `dual_evidence` (E1–E4), `baseline_date`, `result_date`, `model_sha256`, `solution_sha256`, `llm`, `solver`, `hardware`, `wall_seconds`, `tokens`, `skill`, `library_record`, and `evidence_url`. Gains are measured against the frozen snapshot `data/baselines/<baseline_date>.json`, not against the live `best_known` and `best_bound`. Never edit a snapshot; add a new dated one instead.

## Data sources

- PESPlib records table: https://timpasslib.aalto.fi/pesplib.html (read 2026-11-11)
  - Activity counts (`n2`) are taken from the instance files in set-01. The records table lists more: one more for 15 instances and twenty more for R4L2 (checked 2026-11-16). Event counts agree.
- MIPLIB 2017 Easy and Hard tags and solution file v37: https://miplib.zib.de/download.html
- TimPassLib solutions page: https://timpasslib.aalto.fi/solutions.html (read 2026-11-11)
- DISPLIB: https://displib.github.io/ (repository github.com/displib/displib.github.io, last updated 2025-09-18)
- DISPLIB paper results: [Fuchs et al., Appendix B](https://doi.org/10.1016/j.jrtpm.2026.100600) and [Stärk et al., Appendix A](https://doi.org/10.4230/OASIcs.ATMOS.2026.6)
