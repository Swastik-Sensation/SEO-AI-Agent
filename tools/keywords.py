"""Lightweight keyword extraction (frequency-based). Swap for embeddings later."""
import re
from collections import Counter

STOP = set("""a an the and or but if of to in on for with at by from as is are was were be been it this that these
those you your we our they their i he she his her its not no yes can will just more most about into over than
then so such also all any each other some how what when where who why which get new one use make like out up
""".split())


def _tokens(text: str):
    return [w for w in re.findall(r"[a-z][a-z\-]{2,}", text.lower()) if w not in STOP]


def top_keywords(pages: list, n: int = 15) -> dict:
    uni, bi = Counter(), Counter()
    per_page = {}
    for p in pages:
        if not p.text_sample:
            continue
        # headings/title weighted higher than body text
        weighted = f"{p.title} {p.title} {' '.join(p.h1)} {' '.join(p.h1)} {p.text_sample}"
        toks = _tokens(weighted)
        uni.update(toks)
        bi.update(" ".join(pair) for pair in zip(toks, toks[1:]))
        per_page[p.url] = [w for w, _ in Counter(toks).most_common(5)]
    return {
        "top_terms": uni.most_common(n),
        "top_phrases": [(k, v) for k, v in bi.most_common(n * 2) if v > 2][:n],
        "per_page": per_page,
    }
