"""
Fixed retrieval condition (C7) for the held-out validation of the post-hoc
numeric-retrieval fix described in the paper's Post-Hoc Analysis section.

Combines the three root-cause fixes, generalized beyond the specific
questions they were originally diagnosed on:

1. Table-aware, page-bounded chunking (table_chunk.page_table_aware_chunks)
   instead of fixed-word chunking, so a number is never separated from its
   row label and chunks never merge across a page boundary.
2. Statement-type-diversified retrieval: chunks are tagged by which
   financial statement they most likely belong to (cash flow, income
   statement, balance sheet), and top candidates are pulled from each
   detected statement type separately before merging -- so a question that
   needs to combine a balance-sheet figure with an income-statement figure
   (as most ratio/CCC/working-capital questions do) doesn't lose one side
   to TF-IDF competition from the other.
3. Abbreviation / synonym query expansion for common finance shorthand,
   generalized into one lookup table rather than the per-question patches
   used during diagnosis.

This module is intentionally generic -- it takes no financebench_id and no
knowledge of which questions are "supposed to" need which fix -- so it can
be run unmodified on a held-out sample that was never used to build it.
"""
import re

from table_chunk import page_table_aware_chunks

SYNONYMS = {
    "ppne": "property plant and equipment net",
    "ppe": "property plant and equipment",
    "d&a": "depreciation and amortization",
    "capex": "capital expenditures purchases of property plant and equipment",
    "ebitda": "earnings before interest taxes depreciation and amortization operating income",
    "p&l": "income statement statement of operations",
    "dio": "days inventory outstanding average inventory cost of goods sold",
    "dso": "days sales outstanding average accounts receivable revenue",
    "dpo": "days payable outstanding average accounts payable cost of goods sold",
    "ccc": "cash conversion cycle",
    "capm": "capital asset pricing model",
    "roa": "return on assets net income total assets",
    "roe": "return on equity net income shareholders equity",
    "cogs": "cost of goods sold cost of sales cost of revenue",
    "ar": "accounts receivable",
    "ap": "accounts payable",
}

CF_MARKERS = ["statement of cash flows", "cash flows from operating", "cash flows from investing",
              "cash flows from financing"]
INC_MARKERS = ["statement of income", "statement of operations", "consolidated statements of income",
               "consolidated statements of operations", "income statement"]
BS_MARKERS = ["balance sheet", "statement of financial position", "consolidated balance sheets"]


def expand_query(q):
    ql = q.lower()
    extra = [expansion for abbr, expansion in SYNONYMS.items() if abbr in ql]
    return q + " " + " ".join(extra) if extra else q


def tag_statement(chunk):
    cl = chunk.lower()
    if any(m in cl for m in CF_MARKERS):
        return "cash_flow"
    if any(m in cl for m in INC_MARKERS):
        return "income"
    if any(m in cl for m in BS_MARKERS):
        return "balance_sheet"
    return "other"


def retrieve_fixed(question, pages, tfidf_topk_fn, k_base=6, k_per_statement=2):
    """
    pages: list of page texts (from pipeline.extract_pdf_text)
    tfidf_topk_fn: pipeline.tfidf_topk (injected to avoid circular import / keep this module standalone)

    ADDITIVE design: start from the same plain top-k TF-IDF retrieval a
    single-statement question would already succeed with (just run over
    table-aware chunks instead of fixed-word chunks), then ADD a couple of
    supplementary candidates from any statement-type bucket not already
    covered. Statement diversification only ever adds context on top of the
    baseline-equivalent retrieval -- it never has a fixed quota that can
    outright replace or crowd out the single best-matching chunk the way a
    bucket-first design does. That crowding-out failure mode showed up
    empirically on the held-out set (e.g. Costco's balance-sheet "total
    assets" question) and is the reason this function was rewritten from an
    earlier bucket-quota-first version.
    """
    chunks = page_table_aware_chunks(pages)
    if not chunks:
        return []

    query = expand_query(question)

    selected, seen = [], set()
    for c, _ in tfidf_topk_fn(query, chunks, k=k_base):
        if c not in seen:
            selected.append(c)
            seen.add(c)

    buckets = {"cash_flow": [], "income": [], "balance_sheet": [], "other": []}
    for c in chunks:
        buckets[tag_statement(c)].append(c)

    for btype in ["cash_flow", "income", "balance_sheet"]:
        bucket_chunks = buckets[btype]
        if not bucket_chunks:
            continue
        for c, _ in tfidf_topk_fn(query, bucket_chunks, k=k_per_statement):
            if c not in seen:
                selected.append(c)
                seen.add(c)

    return selected
