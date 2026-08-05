# Research-semanticchunking

> **Research question:** Do semantic-boundary chunking and a hybrid retrieval pipeline actually beat a plain fixed-chunking baseline on financial filings — and when a real retrieval failure shows up, does a targeted fix generalize to questions it wasn't built for?

*Ebuka Chidubem Prudence Uzoama, Anote AI Research Fellowship 2026*

## Overview

This repo benchmarks three retrieval conditions on [FinanceBench](https://arxiv.org/abs/2311.11944) — a fixed-chunking baseline, semantic-boundary chunking, and a hybrid pipeline combining structure-aware chunking, BM25/TF-IDF fusion, metadata prefixes, HyDE-style query expansion, and lexical reranking — measured with ROUGE-L F1 and Exact Match, and run twice independently to check the result holds up. It then diagnoses a specific retrieval failure found along the way (every condition scored 0.000 Exact Match on numeric questions), builds a targeted fix, and tests that fix on a held-out sample it was never tuned against.

## Ablation Design

| Condition | What it does | Run 1 F1 | Run 2 F1 |
|---|---|---|---|
| C0 — baseline | Fixed word-based chunking, plain TF-IDF | 0.152 | 0.145 |
| C1 — semantic | Paragraph/sentence-boundary chunking | 0.117 | 0.123 |
| C6 — hybrid | Structure-aware chunking + BM25/TF-IDF fusion + metadata + HyDE + reranking | 0.128 | 0.124 |

Neither enhancement beats the baseline in either run. C1's shortfall is significant in Run 1 (95% CI [-0.073, -0.002]) and just short of it in Run 2 ([-0.050, +0.001]) — same direction, right at the edge both times. C6's shortfall is smaller and not significant in either run.

## The Post-Hoc Fix (C7) and Held-Out Validation

Every condition scored **0.000 Exact Match** on metrics-generated (numeric) questions, in both runs. Diagnosis traced this to three causes — table-splitting chunking, cross-statement computed metrics, and domain abbreviations absent from the source text — and a targeted fix (`fixed_retrieval.py`, C7) recovered 4 of 5 originally-failing questions.

That number is diagnostic, not proof it generalizes: C7 was built with knowledge of exactly which questions had failed. `run_holdout.py` tests it on ten fresh metrics-generated questions from ten companies never used anywhere above, blind, with no per-question tuning:

| Condition | Held-out exact matches (10 questions) |
|---|---|
| C0 — baseline | 6 / 10 |
| C7 — fix | 5 / 10 |

C7 does not beat the baseline in aggregate on fresh data. It reliably solves the specific failure it was diagnosed from, but trades it for new misses elsewhere. Full discussion in `paper.pdf`, Section 6.

## Quickstart

```bash
pip install -r requirements.txt

python pipeline.py          # C0/C1/C6 retrieval → prudence_retrieved.json
python score.py run1        # scores run1_answers.py: means + paired bootstrap
python score.py run2        # scores run2_answers.py: means + paired bootstrap
python run_holdout.py       # C0 + C7 retrieval on the held-out sample, blind
```

`data/pdfs/` and `financebench_sample.csv` are bundled in this repo, so no external FinanceBench checkout is needed. Nine filings referenced in the full FinanceBench sample aren't included here (four Adobe 10-Ks, four Johnson & Johnson filings, one MGM Resorts earnings release) and are excluded from the sample pool; `AMD_2015_10K.pdf` is present but fails to parse with both available PDF extractors and is skipped when encountered in the main sample.

## Files

| File | What it is |
|---|---|
| `pipeline.py` | Builds C0/C1/C6 chunks and retrieves top candidates per question |
| `table_chunk.py` | Page-aware, table-preserving chunker used by C7 |
| `fixed_retrieval.py` | C7 — the generalized post-hoc fix |
| `run1_answers.py`, `run2_answers.py` | Two independently written answer sets per question/condition |
| `score.py` | ROUGE-L F1 scoring + paired bootstrap comparison (`python score.py run1`/`run2`) |
| `run_holdout.py` | Draws + retrieves the held-out sample for C0 and C7 |
| `holdout_sample.json` | The ten held-out questions, saved for reproducibility |
| `results/` | `results_run1.csv`, `results_run2.csv`, `results_heldout.csv` — per-question scored results |
| `data/` | `pdfs/` (21 filings), `financebench_open_source.jsonl` (full 150-question pool used for held-out sampling) |
| `financebench_sample.csv` | The stratified sample `pipeline.py` draws from |
| `paper.pdf` | Full write-up |
| `blog_post.md` | Public-facing version, ready to publish |
| `FinanceBench_Ablation_Deck.pptx` | Presentation deck |

## Limitations

Small-sample, single-model check: 14 questions in the main ablation, 10 in the held-out set — enough to catch a large effect, not fine distinctions. Retrieval throughout is TF-IDF/BM25 rather than neural embeddings and a cross-encoder reranker, and Claude is the sole generation model, so results are a conservative floor rather than a ceiling. C7 is a diagnostic fix, not a validated fourth ablation condition — full discussion, and the prioritized next steps (starting with swapping in neural embeddings), are in `paper.pdf`, Sections 7–8.

## Citation

```bibtex
@software{uzoama2026semanticchunking,
  title  = {Semantic Chunking and Hybrid Retrieval for Financial Document QA: An Ablation Study on FinanceBench},
  author = {Uzoama, Ebuka Chidubem Prudence},
  year   = {2026},
  url    = {https://github.com/anote-ai/Research-semanticchunking}
}
```
