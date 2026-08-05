"""
An independent ablation on FinanceBench comparing three retrieval conditions:
C0 (fixed word-based chunking, baseline), C1 (semantic-boundary chunking),
and C6 (a hybrid pipeline combining structure-aware chunking, BM25/TF-IDF
fusion, metadata prefixes, HyDE-style query expansion, and lexical reranking).

Retrieval here uses TF-IDF and BM25 rather than neural embeddings and a
cross-encoder reranker, and Claude is used as the generation model for all
three conditions, so the comparison stays internally consistent. Sample size
is 14 questions (roughly stratified by question type) rather than the full
FinanceBench set, for tractability within this contribution.

See README.md in this folder for the full write-up and how to reproduce
the two independent runs.
"""
import json
import random
import re
from pathlib import Path

import pandas as pd
import pypdfium2 as pdfium
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

REPO = Path(__file__).parent
DATA_ROOT = REPO  # repo is self-contained: financebench_sample.csv and data/pdfs live alongside this file
PDF_DIR = DATA_ROOT / "data" / "pdfs"

MISSING = ['ADOBE_2015_10K','ADOBE_2016_10K','ADOBE_2017_10K','ADOBE_2022_10K',
           'JOHNSON_JOHNSON_2022_10K','JOHNSON_JOHNSON_2022Q4_EARNINGS',
           'JOHNSON_JOHNSON_2023_8K_dated-2023-08-30','JOHNSON_JOHNSON_2023Q2_EARNINGS',
           'MGMRESORTS_2022Q4_EARNINGS']


def load_sample(n_per_type=5, seed=42):
    df = pd.read_csv(DATA_ROOT / "financebench_sample.csv")
    df = df[~df["doc_name"].isin(MISSING)].reset_index(drop=True)
    rng = random.Random(seed)
    parts = []
    for qtype, group in df.groupby("question_type"):
        idx = list(group.index)
        rng.shuffle(idx)
        parts.append(group.loc[idx[:n_per_type]])
    sample = pd.concat(parts).reset_index(drop=True)
    return sample


def extract_pdf_text(doc_name):
    path = PDF_DIR / f"{doc_name}.pdf"
    try:
        pdf = pdfium.PdfDocument(str(path))
        pages = []
        for page in pdf:
            tp = page.get_textpage()
            pages.append(tp.get_text_range() or "")
        return pages
    except Exception as e:
        print(f"  [pdfium failed on {doc_name}: {e}; falling back to pypdf]")
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        return [p.extract_text() or "" for p in reader.pages]


def word_chunks(text, chunk_words=380, overlap_words=40):
    """Approximate 512-token/50-overlap chunking (fixed, C0)."""
    words = text.split()
    chunks = []
    step = max(1, chunk_words - overlap_words)
    for start in range(0, len(words), step):
        chunk = " ".join(words[start:start + chunk_words])
        if chunk.strip():
            chunks.append(chunk)
        if start + chunk_words >= len(words):
            break
    return chunks


def sentence_boundary_chunks(text, max_chars=1024):
    """Sentence/paragraph-boundary chunking, stand-in for semantic chunking (C1)."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks = []
    current = ""
    for para in paras:
        candidate = (current + " " + para).strip() if current else para
        if current and len(candidate) > max_chars:
            chunks.append(current)
            current = para
        else:
            current = candidate
    if current:
        chunks.append(current)
    if len(chunks) <= 1 and text.strip():
        sentences = re.split(r"(?<=[.!?]) +", text)
        chunks = []
        current = ""
        for s in sentences:
            candidate = (current + " " + s).strip() if current else s
            if current and len(candidate) > max_chars:
                chunks.append(current)
                current = s
            else:
                current = candidate
        if current:
            chunks.append(current)
    return chunks


def recursive_chunks(text, chunk_chars=2000, overlap_chars=200):
    """Recursive-ish chunking with structural separators (used for C6)."""
    seps = ["\n\n\n", "\n\n", "\n", ". ", " "]

    def split(t, sep_idx):
        if len(t) <= chunk_chars or sep_idx >= len(seps):
            return [t]
        sep = seps[sep_idx]
        parts = t.split(sep)
        out, current = [], ""
        for p in parts:
            candidate = (current + sep + p) if current else p
            if len(candidate) > chunk_chars:
                if current:
                    out.append(current)
                current = p
            else:
                current = candidate
        if current:
            out.append(current)
        result = []
        for o in out:
            if len(o) > chunk_chars:
                result.extend(split(o, sep_idx + 1))
            else:
                result.append(o)
        return result

    raw = split(text, 0)
    chunks = []
    for i, c in enumerate(raw):
        if i > 0 and overlap_chars > 0:
            prev_tail = raw[i - 1][-overlap_chars:]
            c = prev_tail + c
        chunks.append(c)
    return chunks


def tfidf_topk(query, chunks, k=10):
    if not chunks:
        return []
    vec = TfidfVectorizer(stop_words="english")
    mat = vec.fit_transform(chunks + [query])
    sims = cosine_similarity(mat[-1], mat[:-1]).flatten()
    top_idx = sims.argsort()[::-1][:k]
    return [(chunks[i], float(sims[i])) for i in top_idx]


def bm25_topk(query, chunks, k=10):
    if not chunks:
        return []
    tokenized = [c.lower().split() for c in chunks]
    bm25 = BM25Okapi(tokenized)
    scores = bm25.get_scores(query.lower().split())
    top_idx = scores.argsort()[::-1][:k]
    return [(chunks[i], float(scores[i])) for i in top_idx]


def lexical_overlap_score(query, chunk):
    q_tokens = set(re.findall(r"[a-z0-9]+", query.lower()))
    c_tokens = re.findall(r"[a-z0-9]+", chunk.lower())
    if not c_tokens:
        return 0.0
    c_set = set(c_tokens)
    overlap = len(q_tokens & c_set)
    return overlap / (len(q_tokens) + 1e-9)


def parse_doc_metadata(doc_name):
    parts = doc_name.split("_")
    company = parts[0]
    year = next((p for p in parts if p.isdigit() and len(p) == 4), "unknown")
    if "10K" in doc_name:
        doc_type = "10-K"
    elif "10Q" in doc_name:
        doc_type = "10-Q"
    elif "EARNINGS" in doc_name:
        doc_type = "earnings"
    elif "8K" in doc_name:
        doc_type = "8-K"
    else:
        doc_type = "unknown"
    return company, year, doc_type


def build_conditions_for_doc(doc_name):
    pages = extract_pdf_text(doc_name)
    full_text = "\n\n".join(pages)
    c0_chunks = word_chunks(full_text)
    c1_chunks = sentence_boundary_chunks(full_text)
    c6_raw_chunks = recursive_chunks(full_text)
    company, year, doc_type = parse_doc_metadata(doc_name)
    prefix = f"[Company: {company} | Year: {year} | Type: {doc_type}]\n"
    c6_chunks = [prefix + c for c in c6_raw_chunks]
    return c0_chunks, c1_chunks, c6_chunks


def hypothetical_answer(question):
    return f"A financial analyst would answer this by citing the exact figure or statement in the filing that addresses: {question}"


def retrieve_c6(question, chunks, doc_name):
    company, year, doc_type = parse_doc_metadata(doc_name)
    enriched_query = f"[Company: {company} | Year: {year} | Type: {doc_type}]\n{question}"
    hyde_query = enriched_query + " " + hypothetical_answer(question)

    bm25_res = bm25_topk(enriched_query, chunks, k=20)
    tfidf_res = tfidf_topk(hyde_query, chunks, k=20)

    scores = {}
    for rank, (chunk, _) in enumerate(bm25_res):
        scores[chunk] = scores.get(chunk, 0.0) + 0.5 * (1.0 / (rank + 1))
    for rank, (chunk, _) in enumerate(tfidf_res):
        scores[chunk] = scores.get(chunk, 0.0) + 0.5 * (1.0 / (rank + 1))
    merged = sorted(scores.items(), key=lambda x: -x[1])
    candidates = [c for c, _ in merged[:20]] or chunks[:20]

    reranked = sorted(candidates, key=lambda c: -lexical_overlap_score(enriched_query, c))
    return reranked[:5]


import pickle

CACHE_FILE = REPO / "prudence_doc_cache.pkl"


def main():
    sample = load_sample(n_per_type=5, seed=42)
    out = []
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "rb") as f:
            doc_cache = pickle.load(f)
    else:
        doc_cache = {}
    for _, row in sample.iterrows():
        doc_name = row["doc_name"]
        if doc_name not in doc_cache:
            print(f"Indexing {doc_name} ...")
            try:
                doc_cache[doc_name] = build_conditions_for_doc(doc_name)
            except Exception as e:
                print(f"  SKIPPING {doc_name}: {e}")
                doc_cache[doc_name] = None
            with open(CACHE_FILE, "wb") as f:
                pickle.dump(doc_cache, f)
        if doc_cache[doc_name] is None:
            continue
        c0_chunks, c1_chunks, c6_chunks = doc_cache[doc_name]

        c0_top = [c for c, _ in tfidf_topk(row["question"], c0_chunks, k=4)]
        c1_top = [c for c, _ in tfidf_topk(row["question"], c1_chunks, k=4)]
        c6_top = retrieve_c6(row["question"], c6_chunks, doc_name)

        out.append({
            "financebench_id": row["financebench_id"],
            "company": row["company"],
            "doc_name": doc_name,
            "question_type": row["question_type"],
            "question": row["question"],
            "gold_answer": str(row["answer"]),
            "context_C0": "\n\n".join(c0_top),
            "context_C1": "\n\n".join(c1_top),
            "context_C6": "\n\n".join(c6_top),
        })

    with open(REPO / "prudence_retrieved.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nWrote {len(out)} questions x 3 conditions to prudence_retrieved.json")


if __name__ == "__main__":
    main()
