"""
Score KYBELE D10.3 evaluation runs against the Collembola taxonomic-treatment benchmark.

Metric definitions mirror SIB's BioMoQA-RAG eval/evaluate_bioasq_qa.py (D10.2) so that
results are comparable: Exact Match, Answer Contains, SQuAD F1, ROUGE-L, answered rate,
and the lexical faithfulness proxy (TREC AIS style). Added for D10.3: gold-treatment
retrieval hit and rank in the Plazi collection, and latency.

Inputs
  benchmark.csv  qid, docid, taxon, family, question_type, question, gold_answer, gold_context
  runs.jsonl     one line per (qid, config): {"qid", "config", "wall_s", "response": {...}}

Outputs
  scored.csv, summary.json
"""

import csv
import json
import random
import re
import string
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

NO_ANSWER_MARKERS = [
    "no relevant answer found", "cannot be fully answered",
    "not found", "no answer", "insufficient",
    "no information", "does not provide", "do not provide", "not mentioned",
    "no direct information", "not specified", "does not specify",
]


def _normalize(text: str) -> str:
    text = (text or "").lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    return " ".join(text.split())


def exact_match(pred, gold):
    return float(_normalize(pred) == _normalize(gold))


def answer_contains(pred, gold):
    g = _normalize(gold)
    return float(bool(g) and g in _normalize(pred))


def squad_f1(pred, gold):
    p, g = _normalize(pred).split(), _normalize(gold).split()
    if not p or not g:
        return 0.0
    common = Counter(p) & Counter(g)
    n = sum(common.values())
    if n == 0:
        return 0.0
    prec, rec = n / len(p), n / len(g)
    return 2 * prec * rec / (prec + rec)


def _rouge_tokens(text):
    # rouge_score's default tokenisation (lowercase, non-alphanumerics to spaces);
    # the Porter stemmer is not applied, so scores can be marginally lower than SIB's.
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).split()


def rouge_l(pred, gold):
    p, g = _rouge_tokens(pred), _rouge_tokens(gold)
    if not p or not g:
        return 0.0
    prev = [0] * (len(p) + 1)
    for gt in g:
        cur = [0] * (len(p) + 1)
        for j, pt in enumerate(p, 1):
            cur[j] = prev[j - 1] + 1 if gt == pt else max(prev[j], cur[j - 1])
        prev = cur
    lcs = prev[-1]
    if lcs == 0:
        return 0.0
    prec, rec = lcs / len(p), lcs / len(g)
    return 2 * prec * rec / (prec + rec)


def is_answered(text):
    if not text or not text.strip():
        return False
    lo = text.lower()
    return not any(m in lo for m in NO_ANSWER_MARKERS)


def faithfulness(pred, context):
    """Mean over answer sentences of token recall against the cited context."""
    if not (pred or "").strip() or not (context or "").strip():
        return None
    pred_clean = re.sub(r"^Based on the provided documents?,?\s*", "", pred, flags=re.I)
    sents = [s.strip() for s in re.split(r"[.!?]", pred_clean)
             if s.strip() and len(s.strip().split()) >= 3]
    if not sents:
        return None
    ctx = Counter(_normalize(context).split())
    rec = []
    for s in sents:
        toks = _normalize(s).split()
        if toks:
            rec.append(sum((Counter(toks) & ctx).values()) / len(toks))
    return mean(rec) if rec else None


def _same_doc(a, b):
    return bool(a) and bool(b) and str(a).strip() == str(b).strip()


def extract(response, gold_docid):
    """Pull the Plazi answer, the top-ranked answer and retrieval info from a /qa/multi response."""
    out = {
        "plazi_answer": "", "plazi_context": "", "top_answer": "", "top_collection": "",
        "top_context": "", "plazi_rank": None, "gold_retrieved": 0, "gold_doc_rank": None,
        "gold_answer_doc": 0, "n_plazi_docs": 0, "pipeline_time": response.get("pipeline_time"),
        "unresolved": bool(response.get("unresolved_refs")),
    }
    cols = sorted(response.get("collection_results") or [], key=lambda c: c.get("rank", 99))
    for c in cols:
        answers = c.get("answers") or []
        if not answers:
            continue
        a0 = answers[0]
        ctx = "\n".join((d.get("doc_text") or "") for d in (a0.get("docs") or []))
        if not out["top_answer"]:
            out.update(top_answer=a0.get("answer") or "", top_collection=c.get("collection"),
                       top_context=ctx)
        if c.get("collection") == "plazi":
            out.update(plazi_answer=a0.get("answer") or "", plazi_context=ctx,
                       plazi_rank=c.get("rank"))
            seen = []
            for a in answers:
                for d in a.get("docs") or []:
                    if d.get("docid") not in seen:
                        seen.append(d.get("docid"))
            out["n_plazi_docs"] = len(seen)
            for i, did in enumerate(seen, 1):
                if _same_doc(did, gold_docid):
                    out["gold_retrieved"], out["gold_doc_rank"] = 1, i
                    break
            out["gold_answer_doc"] = int(any(_same_doc(d.get("docid"), gold_docid)
                                             for d in (a0.get("docs") or [])))
    return out


def bootstrap_ci(values, n=2000, seed=7):
    vals = [v for v in values if v is not None]
    if len(vals) < 2:
        return (None, None)
    rnd = random.Random(seed)
    means = sorted(mean(rnd.choices(vals, k=len(vals))) for _ in range(n))
    return (means[int(0.025 * n)], means[int(0.975 * n) - 1])


def main(bench_path="benchmark.csv", runs_path="runs.jsonl", out_dir="."):
    out_dir = Path(out_dir)
    bench = {r["qid"]: r for r in csv.DictReader(open(bench_path, encoding="utf-8"))}
    rows = []
    latest = {}
    for line in open(runs_path, encoding="utf-8"):
        if not line.strip():
            continue
        run = json.loads(line)
        resp = run.get("response") or {}
        if run.get("error") or (not resp.get("collection_results") and not resp.get("model")
                                and resp.get("pipeline_time") is None):
            continue  # failed request or silent server error: not an answer
        latest[(run["qid"], run["config"])] = run  # last valid answer wins
    for run in latest.values():
        b = bench.get(run["qid"])
        if b is None:
            continue
        ex = extract(run.get("response") or {}, b["docid"])
        gold = b["gold_answer"]
        golds = [g.strip() for g in gold.split("||") if g.strip()]

        def best(fn, pred):
            return max(fn(pred, g) for g in golds) if golds else 0.0

        row = {"qid": run["qid"], "config": run["config"], "question_type": b["question_type"],
               "family": b.get("family", ""), "question": b["question"], "gold_answer": gold,
               "answer_offset": int(b.get("answer_offset") or -1),
               "doc_ref": run.get("doc_ref"), "doc_ref_hit_gold": run.get("doc_ref_hit_gold"),
               "wall_s": run.get("wall_s"), "error": run.get("error", "")}
        row.update({k: v for k, v in ex.items() if not k.endswith("_context")})
        for pref, ans, ctx in (("plazi", ex["plazi_answer"], ex["plazi_context"]),
                               ("top", ex["top_answer"], ex["top_context"])):
            row[f"{pref}_answered"] = float(is_answered(ans))
            row[f"{pref}_em"] = best(exact_match, ans)
            row[f"{pref}_contains"] = best(answer_contains, ans)
            row[f"{pref}_f1"] = best(squad_f1, ans)
            row[f"{pref}_rougeL"] = best(rouge_l, ans)
            row[f"{pref}_faith"] = faithfulness(ans, ctx) if "generative" in run["config"] else None
        rows.append(row)

    fields = list(rows[0].keys()) if rows else []
    with open(out_dir / "scored.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    by_cfg = defaultdict(list)
    for r in rows:
        by_cfg[r["config"]].append(r)
    summary = {}
    for cfg, rs in sorted(by_cfg.items()):
        s = {"n": len(rs), "errors": sum(1 for r in rs if r["error"])}
        for m in ("plazi_answered", "plazi_em", "plazi_contains", "plazi_f1", "plazi_rougeL",
                  "plazi_faith", "top_em", "top_contains", "top_f1", "gold_retrieved",
                  "gold_answer_doc"):
            vals = [r[m] for r in rs if r[m] is not None]
            s[m] = mean(vals) if vals else None
            if m in ("plazi_em", "plazi_contains", "plazi_f1", "gold_retrieved"):
                s[m + "_ci95"] = bootstrap_ci([r[m] for r in rs])
        s["top_is_plazi"] = mean(1.0 if r["top_collection"] == "plazi" else 0.0 for r in rs)
        pts = [r["pipeline_time"] for r in rs if r["pipeline_time"] is not None]
        s["mean_pipeline_time_s"] = mean(pts) if pts else None
        wts = [r["wall_s"] for r in rs if r["wall_s"] is not None]
        s["mean_wall_s"] = mean(wts) if wts else None
        by_type = defaultdict(list)
        for r in rs:
            by_type[r["question_type"]].append(r)
        s["by_question_type"] = {
            t: {"n": len(v), "plazi_em": mean(x["plazi_em"] for x in v),
                "plazi_contains": mean(x["plazi_contains"] for x in v),
                "plazi_f1": mean(x["plazi_f1"] for x in v),
                "gold_retrieved": mean(x["gold_retrieved"] for x in v)}
            for t, v in sorted(by_type.items())}
        summary[cfg] = s
    json.dump(summary, open(out_dir / "summary.json", "w"), indent=2)
    print(json.dumps({k: {m: v for m, v in s.items() if m != "by_question_type"}
                      for k, s in summary.items()}, indent=2))


if __name__ == "__main__":
    main(*sys.argv[1:])
