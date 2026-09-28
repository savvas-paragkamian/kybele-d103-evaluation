"""Build the KYBELE trophic-guild benchmark (benchmark_trophic.csv) and the runner's candidates.csv
from the curated harvest rounds. Run from data/curation/trophic: python3 build_trophic.py"""
import csv
import json
import os

T, T2, T3, TG = {}, {}, {}, {}
exec(open("curation_t1.py").read())
exec(open("curation_t2.py").read())
if os.path.exists("curation_t3.py"):
    exec(open("curation_t3.py").read())
if os.path.exists("curation_g.py"):
    exec(open("curation_g.py").read())

R = {}
for f in ["review1.json", "review2.json", "review3.json", "review4.json"]:
    if os.path.exists(f):
        for r in json.load(open(f)):
            R[r["tid"]] = r

EXPERT = [  # from the trait-mining expert review (collembola-trait-mining, September 2026)
    dict(tid="X001", species="Folsomia fimetarioides", doc_id="28313106", collection="medline",
         title="(trait-mining source)", gold="metal-tolerant fungi || fungi", guilds="fungivore",
         evidence="lab", hedged=False, note="expert review: fungal preference under experimental conditions (keep with note)",
         context=""),
]

rows = []
for decisions in (T, T2, T3):
    for tid, v in decisions.items():
        if v["action"] != "keep":
            continue
        r = R[tid]
        rows.append(dict(tid=tid, species=v.get("species") or r["species"], doc_id=r["doc_id"],
                         collection=r["collection"], title=r.get("title", ""), gold=v["gold"],
                         guilds=v["guilds"], evidence=v["evidence"], hedged=v.get("hedged", False),
                         note=v.get("note", ""), context=r["context"]))
RG = {r["tid"]: r for r in json.load(open("review_g.json"))} if os.path.exists("review_g.json") else {}
for tid, v in TG.items():
    if v["action"] != "keep":
        continue
    r = RG[tid]
    rows.append(dict(tid=tid, species=r["genus"], rank="genus", doc_id=r["doc_id"], collection=r["collection"],
                     title=r.get("title", ""), gold=v["gold"], guilds=v["guilds"], evidence=v["evidence"],
                     hedged=v.get("hedged", False), note=v.get("note", ""), context=r["contexts"][v.get("sent", 0)]))
rows += EXPERT
rows.sort(key=lambda x: (x.get("rank", "species") == "genus", x["species"], x["tid"]))

bench, cand = [], []
for i, x in enumerate(rows, 1):
    qid = f"P{i:03d}"
    q = f"What does {x['species']} feed on?"
    bench.append({"qid": qid, "docid": x["doc_id"], "taxon": x["species"], "taxon_rank": x.get("rank", "species"),
                  "family": "", "question_type": "trophic_guild",
                  "question": q, "gold_answer": x["gold"], "gold_guilds": x["guilds"], "evidence": x["evidence"],
                  "hedged": int(bool(x["hedged"])), "collection": x["collection"], "source_title": x["title"],
                  "gold_context": x["context"][:2500], "answer_offset": -1, "text_length": -1,
                  "curation_ref": x["tid"], "curation_note": x["note"]})
    cand.append({"qid": qid, "docid": x["doc_id"], "species": x["species"], "treatment_title": x["title"],
                 "family": "", "article_title": x["title"], "doi": "", "treatment_uri": "", "question_type": "trophic_guild",
                 "question": q, "candidate_answer": x["gold"].split("||")[0].strip(), "gold_context": x["context"][:2500],
                 "answer_offset": -1, "text_length": -1, "gold_answer": x["gold"], "curation": x["tid"],
                 "curation_note": x["note"]})

for path, data in (("../../benchmark_trophic.csv", bench),):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(data[0].keys()))
        w.writeheader()
        w.writerows(data)

from collections import Counter
print(len(bench), "questions |", len({b["taxon"] for b in bench}), "taxa |", len({b["docid"] for b in bench}), "documents")
print("evidence:", dict(Counter(b["evidence"] for b in bench)), "| hedged:", sum(b["hedged"] for b in bench))
print("collections:", dict(Counter(b["collection"] for b in bench)))
print("top taxa:", Counter(b["taxon"] for b in bench).most_common(6))
print("rank:", dict(Counter(b["taxon_rank"] for b in bench)), "| taxa:", len({b["taxon"] for b in bench}))
per_doc = Counter(b["docid"] for b in bench)
print("documents with >4 questions:", {d: n for d, n in per_doc.items() if n > 4} or "none")
dup = Counter((b["taxon"], b["docid"]) for b in bench)
print("duplicate (taxon, document):", [k for k, n in dup.items() if n > 1] or "none")
per_taxon = Counter(b["taxon"] for b in bench)
print("taxa over cap:", {t: n for t, n in per_taxon.items() if n > (15 if t == "Folsomia candida" else 6)} or "none")
