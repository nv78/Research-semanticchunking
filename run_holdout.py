"""
Retrieve context under Baseline (C0) and Fixed (C7) conditions for the
10-question held-out metrics-generated sample, and write BLIND context
files (question + retrieved context only, no gold answer) so answers can
be generated without seeing the gold answer -- matching the blind-scoring
methodology used for the main ablation's independent rerun.
"""
import json
from pathlib import Path

import pipeline as P
from fixed_retrieval import retrieve_fixed

HERE = Path(__file__).parent
PDF_DIR = HERE / "data" / "pdfs"  # held-out filings are merged into the same data/pdfs/ as the main sample
BLIND_DIR = HERE / "holdout_blind"
BLIND_DIR.mkdir(exist_ok=True)

with open(HERE / "holdout_sample.json") as f:
    sample = json.load(f)

manifest = []
for row in sample:
    doc_name = row["doc_name"]
    fid = row["financebench_id"]
    q = row["question"]
    pdf_path = PDF_DIR / f"{doc_name}.pdf"
    if not pdf_path.exists():
        print(f"MISSING PDF for {doc_name}, skipping {fid}")
        continue

    print(f"Indexing {doc_name} for {fid} ...")
    orig_pdf_dir = P.PDF_DIR
    P.PDF_DIR = PDF_DIR
    try:
        pages = P.extract_pdf_text(doc_name)
    finally:
        P.PDF_DIR = orig_pdf_dir

    full_text = "\n\n".join(pages)
    c0_chunks = P.word_chunks(full_text)
    c0_top = [c for c, _ in P.tfidf_topk(q, c0_chunks, k=4)]

    fixed_top = retrieve_fixed(q, pages, P.tfidf_topk, k_base=6, k_per_statement=2)

    for cond, ctx_chunks in [("baseline", c0_top), ("fixed", fixed_top)]:
        ctx = "\n\n---\n\n".join(ctx_chunks)
        blind_path = BLIND_DIR / f"{fid}_{cond}.txt"
        with open(blind_path, "w") as f:
            f.write(f"QUESTION:\n{q}\n\nRETRIEVED CONTEXT ({cond}):\n\n{ctx}\n")
        manifest.append({
            "financebench_id": fid, "doc_name": doc_name, "condition": cond,
            "question": q, "gold_answer": row["answer"],
            "blind_file": str(blind_path), "n_chunks": len(ctx_chunks),
            "ctx_chars": len(ctx),
        })

with open(HERE / "holdout_manifest.json", "w") as f:
    json.dump(manifest, f, indent=2)

print(f"\nWrote {len(manifest)} blind context files to {BLIND_DIR}")
for m in manifest:
    print(f"  {m['financebench_id']:28s} {m['condition']:9s} {m['n_chunks']} chunks, {m['ctx_chars']} chars")
