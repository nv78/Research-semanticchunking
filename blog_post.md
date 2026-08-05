# Does Retrieval Complexity Actually Pay Off? I Ran the Same Test Twice, Then Chased Down the Zero.

*Ebuka Chidubem Prudence Uzoama, Anote AI Research Fellowship 2026*

---

If you've spent any time building a RAG pipeline, you've probably added semantic chunking at some point. It sounds obviously better than chopping documents into fixed-size blocks: split on paragraph or sentence boundaries instead of a rigid token count, and the model gets cleaner, more coherent context. Add a hybrid retrieval setup on top, combining structure-aware chunking, lexical fusion, metadata tags, and query expansion, and it should be even better.

I wanted to check whether that's actually true on financial filings, where the text is dense, table-heavy, and full of numbers that don't tolerate a chunk boundary landing in the wrong place. So I ran a small, controlled ablation on FinanceBench, ran the entire thing a second time independently to see if it held up, then chased down a strange zero I found along the way. That last part turned into the more interesting story.

---

## The setup

I compared three conditions on a 14-question sample of FinanceBench, stratified across the benchmark's question types:

| Condition | What it does |
|---|---|
| Baseline | Fixed word-based chunking, plain TF-IDF retrieval |
| Semantic | Chunks split on paragraph and sentence boundaries instead of a fixed word count |
| Hybrid | Structure-aware recursive chunking, BM25 and TF-IDF fusion, metadata prefixes, HyDE-style query expansion, and a lexical reranking pass |

Retrieval here runs on TF-IDF and BM25 rather than neural embeddings and a cross-encoder reranker, and Claude generated every answer across all three conditions, so the comparison stays apples-to-apples. Each answer was scored with ROUGE-L F1 and Exact Match against the gold answer.

To keep myself honest, I didn't just run this once and call it a finding. I rebuilt the pipeline and wrote a second, independent set of answers from scratch, then compared the two runs side by side with a paired bootstrap significance test.

---

## The headline result: the baseline won, twice

| Condition | Run 1 mean | Run 2 mean |
|---|---|---|
| Baseline | 0.152 | 0.145 |
| Semantic | 0.117 | 0.123 |
| Hybrid | 0.128 | 0.124 |

In both runs, the baseline won. Not by a landslide, but consistently.

Semantic chunking came in lowest in Run 1, with a large enough gap to be statistically significant: a drop of 0.035 versus baseline, 95% CI [-0.072, -0.002]. In Run 2 the gap was smaller, 0.023, and just barely misses significance at [-0.049, +0.001]. Same direction both times, sitting right at the edge of meaningful in one run and just inside it in the other.

The hybrid pipeline also underperformed the baseline in both runs, by 0.024 and 0.021 respectively, despite combining every enhancement tested here at once. Neither gap was statistically significant. More noise, less signal, even with four extra techniques thrown at the problem.

---

## Then I found a wall of zeros

When I broke the results down by question type, something jumped out: every single condition scored **0.000 Exact Match** on the metrics-generated questions, the ones asking for a specific number, like a capital expenditure figure or an EBITDA margin. Not lower than the others. Zero, in every condition, in both independent runs.

My first instinct was to bury that in a footnote. My second, better instinct was to go find out why.

I went back to the four questions that failed and looked at what retrieval had actually surfaced for each one against the source filing. Three distinct causes showed up, not one:

1. **Table-splitting chunking.** All three conditions chunk by word count, sentence boundary, or recursive character splitting: none of them are aware of page or table structure. A fixed-length window can start or end mid-table, separating a number from the row label that says what it means. 3M's capital expenditure figure, for example, got chunked away from its own line label in every condition, and retrieval returned an unrelated debt schedule instead.
2. **Cross-statement computed metrics.** Some questions define a metric as a combination of line items from two different financial statements: PepsiCo's unadjusted EBITDA needs operating income from the income statement *and* depreciation from the cash flow statement. A single top-k retrieval ranked by similarity tends to return several passages from whichever one statement scores highest, not a balanced set across both.
3. **Domain abbreviations absent from the source text.** One question asks for "net PPNE," an abbreviation that never appears in the filing itself, which spells out "property, plant and equipment" instead. Lexical retrieval has no way to bridge a query term that simply doesn't occur in the document.

I built a targeted fix for all three (page-aware table chunking, statement-type-diversified retrieval, and an abbreviation-expansion dictionary) and reran it on the five numeric questions that had failed (the original four plus one more that had been dropped from the main sample for a parsing issue). Four of five came back exactly right. The fifth was correct in substance but sensitive to a rounding convention.

That felt like a real result. It also felt too good, because I'd built the fix with full knowledge of exactly which questions had failed and why. That's diagnosis, not proof it generalizes.

---

## The part I almost didn't do: testing it on questions it had never seen

So I sampled ten brand-new metrics-generated questions from ten companies that never appeared anywhere in the main ablation or in building the fix (General Mills, Lockheed Martin, Coca-Cola, Amcor, Nike, PepsiCo, Block, Adobe, Costco, and American Water Works), pulled their real filings, and ran the plain baseline and the fix against them blind, with zero per-question tuning.

The honest result: **baseline got 6 of 10 exactly right. The fix got 5 of 10.**

The fix didn't beat the baseline overall. What it did do reliably is solve the exact problem it was built for: PepsiCo's EBITDA margin needed a cash-flow figure combined with an income-statement figure, and the fix's statement-aware retrieval caught both while the baseline only found one. But the fix's more aggressive chunking also introduced two new misses (Coca-Cola, Amcor) on questions where the baseline's plain approach already happened to work, and it left the two hardest questions in the sample unsolved by either condition.

I could have left this part out and just published the 4-of-5 number. I think that would have been the less useful paper. What the held-out test actually shows is more valuable than a clean "solved it" headline: it tells you precisely which failure mode a targeted fix generalizes to, and which it doesn't, and that fixing a diagnosed problem is a different claim from fixing the general one.

---

## Why the baseline keeps winning

None of this means semantic chunking, hybrid retrieval, or the post-hoc fix are bad ideas in general. A few things about financial filings specifically might explain the pattern.

Fixed-size chunking is dumb in a useful way. It doesn't try to be clever about where a number or a table row lives: it just grabs a fixed window and moves on, so it never accidentally splits a coherent block of text based on a bad guess about where the "meaning boundary" is. Semantic chunking depends on the document having clean paragraph or sentence structure to split on, and SEC filings are full of tables, footnotes, and formatting that doesn't map onto sentence boundaries at all. The hybrid pipeline stacks four changes at once, each plausible alone, but combined they add more surface area for something to go slightly wrong, without the headroom that real neural embeddings and a cross-encoder reranker would provide.

That last point is the honest limitation of this whole study: every condition here, including the fix, runs on TF-IDF and BM25, which match words, not meaning. A neural embedding model might close gaps that no amount of chunking cleverness can. I didn't get to test that, since the sandboxed environment I built this in has no network access to a model hub, so it's the first thing on my list to try next, somewhere that does.

---

## The honest caveats

This is a small, single-model check, not a definitive verdict on retrieval strategy for financial RAG. Fourteen questions is enough to catch a large effect and not much more, and the ten-question held-out set is a first look, not a final word. Lexical retrieval substitutes for neural embeddings and cross-encoder reranking, and a single generation model, are real departures from a full-scale setup. What I'd say instead: under this setup, twice, added complexity didn't pay for itself, a real numeric-retrieval failure turned out to have identifiable, partly-fixable causes, and a diagnostic fix built around known failures needs an honest held-out test before anyone calls it solved, because mine, when I ran that test, only tied the baseline.

The full write-up, with methodology, per-question breakdowns, the held-out validation table, and code to reproduce both runs, is linked below.
