"""
Table-aware chunking for financial PDF text.

The word/paragraph/char chunkers in pipeline.py operate on the whole
document as one bag of text, with no notion of page or table boundaries.
That causes two concrete failures for numeric financial questions:

1. A fixed word-count window can start or end mid-table, splitting a
   number away from its row label (or merging two unrelated tables
   together), so the retriever sees numbers without the label that
   identifies what they mean.
2. Even when a table survives intact, it competes for TF-IDF/BM25 rank
   against many other tables that reuse the same recurring numbers
   (five-year summaries, segment breakdowns, etc. often repeat the same
   figures across a document), so the retriever can't tell which table
   is the one the question is actually asking about.

This module fixes both by working page-by-page (never merging text across
a page boundary into one chunk) and by detecting table-like runs of lines
(multiple numeric tokens per line) and keeping each table as a single
chunk, tagged with the heading/caption line(s) that immediately precede
it (e.g. "Cash Flows from Investing Activities:" or "Consolidated
Statement of Cash Flows"). That heading text gives the retriever a
lexical anchor for which table is which, and keeping the table intact
means a number is never separated from its row label.

The heading lines are folded INTO the table chunk only -- they are not
also emitted as their own short standalone chunk. A short heading-only
chunk (e.g. "Consolidated Statement of Cash Flows") is nearly pure
keyword match with no diluting numeric content, so under cosine
similarity it can outrank the real, number-bearing table chunk for the
exact same query. Keeping the heading only inside the table block avoids
that failure mode.
"""
import re

NUM_RE = re.compile(r"\(?\$?-?\d[\d,]*(?:\.\d+)?\)?%?")


def _numeric_token_count(line):
    return len(NUM_RE.findall(line))


def _is_table_line(line):
    line = line.strip()
    if not line:
        return False
    return _numeric_token_count(line) >= 2


def _is_heading_line(line):
    """A short, non-numeric line likely to be a table title or section header."""
    line = line.strip()
    if not line or len(line) > 100:
        return False
    if _numeric_token_count(line) >= 2:
        return False
    return True


def page_table_aware_chunks(pages, max_prose_chars=1024, heading_lookback=2):
    """
    Chunk a document page-by-page. On each page, contiguous runs of
    table-like lines (>=2 numeric tokens) are grouped into one chunk each,
    prefixed with up to `heading_lookback` preceding non-table lines as
    caption/heading context (removed from the prose stream so they are
    not also emitted as a separate, misleadingly-short chunk). Remaining
    prose is chunked by paragraph, same as sentence_boundary_chunks, but
    never crosses a page boundary.
    """
    chunks = []
    for page_text in pages:
        lines = page_text.split("\n")
        lines = [l.rstrip("\r") for l in lines]

        i = 0
        n = len(lines)
        prose_buffer = []

        def flush_prose():
            text = "\n".join(prose_buffer).strip()
            prose_buffer.clear()
            if not text:
                return
            paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
            if not paras:
                paras = [text]
            current = ""
            for para in paras:
                candidate = (current + " " + para).strip() if current else para
                if current and len(candidate) > max_prose_chars:
                    chunks.append(current)
                    current = para
                else:
                    current = candidate
            if current:
                chunks.append(current)

        while i < n:
            if _is_table_line(lines[i]):
                # pull heading lines OUT of prose_buffer (not just read them)
                # so they aren't double-emitted as their own short chunk
                heading = []
                while prose_buffer and len(heading) < heading_lookback:
                    last = prose_buffer[-1]
                    if last.strip() and _is_heading_line(last):
                        heading.insert(0, prose_buffer.pop().strip())
                    elif not last.strip():
                        prose_buffer.pop()  # drop blank separator, keep looking
                    else:
                        break
                flush_prose()

                table_lines = []
                blank_run = 0
                j = i
                while j < n:
                    if _is_table_line(lines[j]):
                        table_lines.append(lines[j].strip())
                        blank_run = 0
                    elif lines[j].strip() == "":
                        blank_run += 1
                        if blank_run > 1:
                            break
                    else:
                        if len(lines[j].strip()) < 80:
                            table_lines.append(lines[j].strip())
                        else:
                            break
                    j += 1
                block = "\n".join(heading + table_lines)
                chunks.append(block)
                i = j
            else:
                prose_buffer.append(lines[i])
                i += 1
        flush_prose()

    return [c for c in chunks if c.strip()]
