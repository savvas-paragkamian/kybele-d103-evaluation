"""
Trophic-guild scoring for the KYBELE D10.3 trophic benchmark.

Reads each QA response the way the KYBELE trait pipeline does (the answer with the highest
answer_score across collections, as in collembola_trophic_batch.py) and scores it three ways:

  guild (pipeline)   guilds found by trait_extraction_v3 with its own keyword vocabulary
                     overlap the gold guilds (Potapov et al. 2022 scheme)
  guild (extended)   the same extractor, with its vocabulary extended by terms it misses
                     (litter, roots, fungal and bacterial genus names, invertebrates ...);
                     this separates the QA service's answers from the extractor's vocabulary
  food match         a gold food item (any alternative) appears verbatim in the answer

Outcomes: correct, wrong (guilds found but none matches), no_answer (no guild found, or the
answer says the diet is not stated). Gold guilds are per question for the gold-document
configurations and the union over the taxon's questions for end-to-end configurations.

Usage: python3 score_trophic.py benchmark_trophic.csv runs.jsonl out_dir
"""

import csv
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
try:
    import trait_extraction_v3 as tx  # noqa: E402  (github.com/ecsltae/collembola-trait-mining)
except ImportError:
    sys.exit("trait_extraction_v3.py is missing: see the README for the pinned download command.")

# Terms trait_extraction_v3 misses (found by running it on the gold answers). Scorer-side only.
EXTRA = {
    "detritivore": [r"\blitter\b", r"\bdebris\b", r"scaveng", r"\bdung\b", r"faec", r"\bfeces\b", r"fertili[sz]er",
                    r"compost", r"saprophag", r"dead organic"],
    "herbivore": [r"\broots?\b", r"\bseedlings?\b", r"macrophyte", r"\bplant (?:particles|material|tissue|sap|matter)",
                  r"\bleaves\b", r"\b(?:wheat|maize|crop) plants?\b", r"\bpepino\b", r"\bSolanum\b", r"\bherbivor", r"phytophag"],
    "fungivore": [r"\bFusarium\b", r"\bTrichoderma\b", r"\bT\. virens\b", r"\bCladosporium\b", r"\bC\. cladosporioides\b",
                  r"\bAspergillus\b", r"\bA\. nidulans\b", r"\bPenicillium\b", r"\bMortierella\b", r"\bUmbelopsis\b",
                  r"\bU\. isabellina\b", r"\bAlternaria\b", r"\bPhanerochaete\b", r"\bAgrocybe\b", r"\bZymoseptoria\b",
                  r"\bZ\. tritici\b", r"\bRhizoctonia\b", r"\bBotrytis\b", r"\bMucor\b", r"\bVerticillium\b",
                  r"\bBeauveria\b", r"\bMetarhizium\b", r"\bLaccaria\b", r"\bPiloderma\b", r"\bPaxillus\b",
                  r"\bGlomus\b", r"\bRhizophagus\b", r"\bAMF\b", r"conidia", r"slime mou?ld", r"myxomycete",
                  r"\bPhysarum\b", r"\bP\. polycephalum\b", r"\bfungivor", r"\bmolds?\b"],
    "bacterivore": [r"\bStreptomyces\b", r"actinobacteri", r"actinomycete"],
    "predator": [r"invertebrates", r"\bmites?\b", r"\binsect eggs\b", r"carnivor", r"first order predator",
                 r"trophic level III"],
    "algivore": [r"\bPleurococcus\b", r"\bDesmococcus\b", r"phycophag"],
    "microbivore": [r"\bmicrobial\b"],
    "omnivore": [r"variety of food", r"wide range of food"],
}
DENIAL = re.compile(r"not (?:explicitly |specifically |directly )?(?:mentioned|stated|specified|given|provided|available|"
                    r"reported|described|discussed)|no (?:specific |explicit |direct )?(?:mention|information|data)|"
                    r"does not (?:mention|specify|state|provide|describe)", re.I)

_BASE = {g: list(p) for g, p in tx._GUILD_PAT.items()}
_EXT = {g: _BASE.get(g, []) + [re.compile(k, re.I) for k in EXTRA.get(g, [])] for g in set(_BASE) | set(EXTRA)}


def guilds(text, taxon, extended, split=False):
    tx._GUILD_PAT = _EXT if extended else _BASE
    try:
        r = tx.extract_trophic(text or "", taxon)
    finally:
        tx._GUILD_PAT = _BASE
    prim, ind = set(r.get("guilds") or []), set(r.get("guilds_indirect") or [])
    for g in (prim, ind):
        if "microbivore" in g:
            g |= {"fungivore", "bacterivore"}
    return (prim, ind) if split else prim | ind


def expand(gold):
    return gold | {"fungivore", "bacterivore"} if "microbivore" in gold else gold


def outcome(answer, taxon, gold, extended):
    """An answer that says the diet is not stated counts as no_answer unless it still states a guild
    directly (the extractor's primary guilds); guilds it only infers (indirect) are not enough."""
    if not (answer or "").strip():
        return "no_answer"
    prim, ind = guilds(answer, taxon, extended, split=True)
    got = prim if DENIAL.search(answer) else prim | ind
    if not got:
        return "no_answer"
    return "correct" if got & expand(gold) else "wrong"


def norm(s):
    return " ".join(re.sub(r"[^\w\s]", " ", (s or "").lower()).split())


def food_match(answer, gold):
    a = norm(answer)
    return int(any(norm(g) and norm(g) in a for g in gold.split("||")))


def is_server_error(resp):
    return not resp.get("collection_results") and not resp.get("model") and resp.get("pipeline_time") is None


def pipeline_answer(resp):
    """Highest answer_score across collections, as in collembola_trophic_batch.parse_biomoqa_response."""
    best, best_score, best_col, ids = "", -1.0, "", set()
    for cr in resp.get("collection_results") or []:
        answers = cr.get("answers") or []
        for a in answers:
            for d in a.get("docs") or []:
                if d.get("docid"):
                    ids.add(str(d["docid"]))
        if not answers:
            continue
        text = answers[0].get("answer") or ""
        score = answers[0].get("answer_score") or 0.0
        if text and score > best_score:
            best, best_score, best_col = text, score, cr.get("collection", "")
    return best, best_col, ids


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(c - h, 3), round(c + h, 3))


def main(bench_path, runs_path, out_dir="."):
    bench = {r["qid"]: r for r in csv.DictReader(open(bench_path, encoding="utf-8"))}
    latest = {}
    for line in open(runs_path, encoding="utf-8"):
        if not line.strip():
            continue
        run = json.loads(line)
        if run["qid"] not in bench or run.get("error") or is_server_error(run.get("response") or {}):
            continue
        latest[(run["qid"], run["config"])] = run

    item_g, taxon_g = {}, defaultdict(set)
    for qid, b in bench.items():
        item_g[qid] = set(filter(None, b["gold_guilds"].split("|")))
        taxon_g[b["taxon"]] |= item_g[qid]

    rows = []
    for (qid, cfg), run in sorted(latest.items()):
        b = bench[qid]
        ans, col, ids = pipeline_answer(run["response"])
        gold_g = item_g[qid] if cfg.startswith("doc") else taxon_g[b["taxon"]]
        rows.append({"qid": qid, "config": cfg, "taxon": b["taxon"], "rank": b.get("taxon_rank", "species"),
                     "evidence": b["evidence"], "hedged": int(b["hedged"]), "collection": b["collection"],
                     "gold_guilds": "|".join(sorted(gold_g)), "gold_answer": b["gold_answer"],
                     "answer": ans, "answer_collection": col,
                     "guilds_pipeline": "|".join(sorted(guilds(ans, b["taxon"], False))),
                     "guilds_extended": "|".join(sorted(guilds(ans, b["taxon"], True))),
                     "pipeline": outcome(ans, b["taxon"], gold_g, False),
                     "extended": outcome(ans, b["taxon"], gold_g, True),
                     "food_match": food_match(ans, b["gold_answer"]),
                     "gold_retrieved": int(str(b["docid"]) in ids),
                     "doc_ref_hit_gold": run.get("doc_ref_hit_gold"), "wall_s": run.get("wall_s")})

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "scored_trophic.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    def summarise(rs):
        n = len(rs)
        s = {"n": n}
        for mode in ("pipeline", "extended"):
            c = Counter(r[mode] for r in rs)
            s[mode] = {k: round(c[k] / n, 3) for k in ("correct", "wrong", "no_answer")}
            s[mode]["correct_ci95"] = wilson(c["correct"], n)
        s["food_match"] = round(sum(r["food_match"] for r in rs) / n, 3)
        s["gold_retrieved"] = round(sum(r["gold_retrieved"] for r in rs) / n, 3)
        s["mean_wall_s"] = round(sum(r["wall_s"] or 0 for r in rs) / n, 2)
        return s

    summ = {}
    for cfg in sorted({r["config"] for r in rows}):
        rs = [r for r in rows if r["config"] == cfg]
        summ[cfg] = {"all": summarise(rs)}
        for key, vals in (("rank", ("species", "genus")), ("hedged", (0, 1)),
                          ("evidence", ("lab", "literature", "isotope", "gut", "field")),
                          ("collection", ("pmc", "medline", "plazi"))):
            for v in vals:
                sub = [r for r in rs if r[key] == v]
                if sub:
                    summ[cfg][f"{key}={v}"] = summarise(sub)
    json.dump(summ, open(out / "summary_trophic.json", "w"), indent=2)
    for cfg, d in summ.items():
        s = d["all"]
        print(f"{cfg:22} n={s['n']:3}  pipeline correct={s['pipeline']['correct']:.2f} wrong={s['pipeline']['wrong']:.2f}  "
              f"extended correct={s['extended']['correct']:.2f} {s['extended']['correct_ci95']} wrong={s['extended']['wrong']:.2f} "
              f"no_answer={s['extended']['no_answer']:.2f}  food={s['food_match']:.2f}  gold_ret={s['gold_retrieved']:.2f}")


if __name__ == "__main__":
    main(*sys.argv[1:])
