#!/usr/bin/env python3
"""
KYBELE D10.3 trophic-guild harvest, GENUS level (Collembola diet statements from SIBiLS)
======================================================================================

Collects candidate diet statements about springtail GENERA (e.g. "Protaphorura species feed on
fungi") from the SIBiLS collections the KYBELE QA service searches (Medline, PMC, Plazi):

  1. The general and food-specific Collembola feeding queries in Medline, PMC and Plazi.
  2. One query per genus (the 102 genera of the KYBELE trait-mining sample first, then the other
     genera of the species list) in Medline, PMC and Plazi.

Only sentences that name a springtail genus on its own (not as part of a binomial) AND contain a
feeding cue are kept, with one sentence of context on each side. Medline/PMC documents must also
mention Collembola or springtails. Everything ends up in kybele_trophic_genus.zip.

Requirements: Python 3.8+, standard library only.
Usage:
    python3 kybele_trophic_genus.py --probe     # 1-minute check
    python3 kybele_trophic_genus.py             # full run, about 20-30 min, resumable
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

SEARCH_URL = "https://biodiversitypmc.sibils.org/api/search"
UA = "KYBELE-D10.3-trophic-harvest/1.1-genus (ELIXIR KYBELE project)"

GENERAL_QUERIES = [
    "Collembola feeding", "Collembola diet", "Collembola gut content", "springtail feeding",
    "springtail diet", "Collembola fungal feeding", "Collembola food preference", "Collembola stable isotope",
    "Collembola trophic niche", "Collembola mycophagy", "Collembola grazing fungi", "Collembola nematode predation",
    "Collembola pollen feeding", "Collembola bacteria feeding", "Collembola algae feeding",
    "Collembola feeding behaviour", "Collembola food choice", "Collembola feeding preference fungi",
    "Collembola microbial feeding", "Collembola fatty acid diet",
]
GENERAL_N = {"medline": 100, "pmc": 30, "plazi": 100}
FOOD_QUERIES = [
    "Collembola mycorrhizal fungi", "Collembola arbuscular mycorrhiza", "Collembola nematodes", "Collembola cyanobacteria",
    "Collembola leaf litter consumption", "Collembola root feeding", "Collembola Cladosporium", "springtail gut microbiome",
    "Collembola lichen", "Collembola moss", "Collembola biofilm", "Collembola yeast diet", "Collembola bacterial diet",
    "Collembola dung", "Collembola carrion", "Collembola hyphae grazing", "Collembola spores", "Collembola ectomycorrhizal",
    "Collembola compound-specific isotope", "Collembola fatty acid biomarkers", "Collembola gut content analysis",
    "Collembola DNA gut content", "Collembola feeding Antarctic", "Collembola diatoms", "Collembola plant roots",
]
FOOD_N = {"medline": 100, "pmc": 50}
GENUS_N = {"medline": 40, "pmc": 20, "plazi": 20}
SPECIES_N = {"medline": 10, "pmc": 5}
SPECIES2_N = {"medline": 40, "pmc": 20}   # round 3: deeper per-species search
TEXT_FIELDS = {
    "medline": ["title", "abstract"],
    "pmc": ["title", "abstract", "full_text"],
    "plazi": ["treatment_title", "text"],
}

DIET = re.compile(
    r"\b(?:feed(?:s|ing)?|fed|diet(?:s|ary)?|gut contents?|consum(?:e|es|ed|ing|ption)|graz(?:e|es|ed|ing)|"
    r"ingest(?:s|ed|ing|ion)?|mycophag\w*|fungivor\w*|bacterivor\w*|microbivor\w*|algivor\w*|detritivor\w*|"
    r"herbivor\w*|phytophag\w*|saprophag\w*|predator\w*|predat(?:e|es|ed|ing|ion)|prey(?:s|ed)? (?:on|upon)|"
    r"food (?:source|preference|choice|item|web)s?|trophic (?:level|position|niche|group|guild)s?|"
    r"stable isotope|δ15N|δ13C|palatab\w*|nutrition\w*)\b", re.I)

GENERA = json.loads(r'''["Absolonia", "Agrenia", "Allacma", "Anurida", "Anurophorus", "Archisotoma", "Arrhopalites", "Ballistura", "Bilobella", "Bourletiella", "Brachystomella", "Ceratophysella", "Choreutinula", "Cribrochiurus", "Cryptopygus", "Cyphoderus", "Desoria", "Detriturus", "Deuteraphorura", "Deutonura", "Dicyrtoma", "Dicyrtomina", "Endonura", "Entomobrya", "Folsomia", "Folsomides", "Friesea", "Gisinianus", "Gnathisotoma", "Halisotoma", "Hemisotoma", "Heteraphorura", "Heteromurus", "Hymenaphorura", "Hypogastrura", "Isotoma", "Isotomiella", "Isotomodes", "Isotomurus", "Kalaphorura", "Katianna", "Lathriopyga", "Lepidocyrtus", "Lipothrix", "Marisotoma", "Megalothorax", "Megaphorura", "Mesaphorura", "Mesogastrura", "Metaphorura", "Micranurida", "Monobella", "Neanura", "Neelides", "Neelus", "Oligaphorura", "Oncopodura", "Onychiuroides", "Onychiurus", "Orchesella", "Orthonychiurus", "Pachyotoma", "Paratullbergia", "Parisotoma", "Plutomurus", "Podura", "Pogonognathellus", "Proisotoma", "Proisotomodes", "Protaphorura", "Pseudachorutella", "Pseudachorutes", "Pseudanurophorus", "Pseudisotoma", "Pseudosinella", "Pygmarrhopalites", "Rusekianna", "Schoettella", "Scutisotoma", "Seira", "Sminthurides", "Sminthurinus", "Sminthurus", "Sphaeridia", "Stenacidia", "Stenaphorura", "Subisotoma", "Superodontella", "Supraphorura", "Tetracanthella", "Tetrodontophora", "Thalassaphorura", "Thaumanura", "Tomocerina", "Tomocerus", "Tritomurus", "Troglopedetes", "Vertagopus", "Willemia", "Willowsia", "Xenylla", "Xenyllodes", "Allonychiurus", "Alloscopus", "Australotomurus", "Austrodontella", "Austrogastrura", "Axelsonia", "Borgesminthurinus", "Coecobrya", "Coenaletes", "Crossodonthina", "Cylindropygus", "Cyphoderopsis", "Denisiella", "Deuterosminthurus", "Dicranocentrus", "Ephemerotoma", "Folsomotoma", "Gomphiocephalus", "Gressittacantha", "Heteroisotoma", "Homidia", "Isotogastrura", "Keratosminthurus", "Leeonychiurus", "Lepidocyrtoides", "Lobellina", "Mastigoceras", "Metacoelura", "Mexicaphorura", "Micronella", "Monodontocerus", "Mucrosomia", "Multivesicula", "Narynia", "Neonaphorura", "Neorganella", "Odontella", "Palmanura", "Papirioides", "Paralobella", "Polydiscia", "Prabhergia", "Pseudoparonella", "Ptenothrix", "Rhodanella", "Salina", "Semicerura", "Sensillonychiurus", "Sensiphorura", "Sernatropiella", "Setanodosa", "Simonachorutes", "Sinella", "Sinoncopodura", "Skadisotoma", "Spinaethorax", "Spinonychiurus", "Stenognathriopes", "Szeptyckitheca", "Temeritas", "Triacanthella", "Troglobius", "Trogolaphysa", "Tullbergia", "Uralaphorura", "Uzelia"]''')


def log(msg, logf):
    line = time.strftime("%H:%M:%S ") + msg
    print(line, flush=True)
    with open(logf, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def http(url, params=None, form=None, timeout=120, retries=2):
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    data = urllib.parse.urlencode(form).encode() if form else None
    last = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, "Accept": "application/json"},
                                         method="POST" if data else "GET")
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code in (400, 404, 405, 413, 422):
                break
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
        time.sleep(4 * (attempt + 1))
    raise RuntimeError(last)


def hits_of(d):
    if not isinstance(d, dict) or d.get("success") is False:
        return None
    return ((d.get("elastic_output") or {}).get("hits") or {}).get("hits") or []


def search_get(q, col, n):
    return hits_of(http(SEARCH_URL, {"q": q, "col": col, "n": n}))


def search_phrase(species, col, n):
    """Exact-binomial query with feeding boost and a slimmer _source, via the jq parameter."""
    fields = TEXT_FIELDS[col]
    body = {
        "query": {"bool": {
            "must": [{"multi_match": {"query": species, "type": "phrase", "fields": fields}}],
            "should": [{"multi_match": {"query": "feeding feeds fed diet food gut consumed grazing fungi",
                                        "fields": fields}}],
        }},
        "_source": {"excludes": ["annotations"]},
    }
    return hits_of(http(SEARCH_URL, {"col": col, "n": n}, form={"jq": json.dumps(body)}))


def search_genus(genus, col, n):
    """Genus name as a phrase, boosted by feeding terms; annotations dropped."""
    fields = TEXT_FIELDS[col]
    body = {
        "query": {"bool": {
            "must": [{"multi_match": {"query": genus, "type": "phrase", "fields": fields}},
                     {"multi_match": {"query": "feeding feeds fed diet food gut consumed grazing fungi prey",
                                      "fields": fields}}],
        }},
        "_source": {"excludes": ["annotations"]},
    }
    return hits_of(http(SEARCH_URL, {"col": col, "n": n}, form={"jq": json.dumps(body)}))


def doc_id(hit, col):
    s = hit.get("_source") or {}
    if col == "pmc":
        return s.get("pmcid") or hit.get("_id")
    if col == "medline":
        return s.get("pmid") or s.get("docid") or hit.get("_id")
    return s.get("docid") or hit.get("_id")


def doc_text(hit, col):
    s = hit.get("_source") or {}
    parts = [s.get(f).strip() for f in TEXT_FIELDS[col] if isinstance(s.get(f), str) and s.get(f).strip()]
    parts = [p if p[-1] in ".!?" else p + "." for p in parts]
    return re.sub(r"\s+", " ", " ".join(parts)).strip()


_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(\[])")
GENUS_RE = None
COLLEMBOLA = re.compile(r"collembol|springtail", re.I)


STOP = {"spp", "species", "and", "or", "are", "is", "was", "were", "feeds", "feed", "fed", "feeding", "which",
        "that", "with", "in", "on", "from", "has", "have", "showed", "shows", "individuals", "populations",
        "specimens", "juveniles", "adults", "the", "also", "may", "can", "could", "did", "does", "do", "had",
        "preferred", "prefers", "prefer", "consumed", "consume", "consumes", "grazed", "grazes", "graze",
        "ingested", "ingest", "ingests", "mainly", "primarily", "mostly", "often", "probably", "seem", "seems",
        "appear", "appears", "as", "to", "by", "for", "of", "at", "not", "only", "genus", "group", "sensu",
        "among", "being", "live", "lives", "living", "occur", "occurs", "gut", "guts", "diet", "diets"}


def genus_mentions(sentence):
    """Springtail genera named on their own (not followed by a species epithet), or as 'Genus spp.'."""
    out = []
    for m in GENUS_RE.finditer(sentence):
        if sentence[max(0, m.start() - 1):m.start()] == "(":
            continue  # subgenus in parentheses
        nxt = sentence[m.end():m.end() + 40]
        ep = re.match(r"\s+(?:\([A-Z][a-z]+\)\s+)?([a-z]{3,})\b", nxt)
        if ep and ep.group(1) not in STOP:
            continue  # a binomial (species-level statements were harvested before)
        out.append(m.group(1))
    return list(dict.fromkeys(out))


def candidates_from(text):
    sents = _SPLIT.split(text)
    found = []
    for i, s in enumerate(sents):
        names = genus_mentions(s)
        if names and DIET.search(s) and len(s) < 1200:
            ctx = " ".join(sents[max(0, i - 1): i + 2])
            found.append((names, s, ctx[:2500]))
    return found


def main():
    global GENUS_RE
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="kybele_trophic_genus")
    ap.add_argument("--probe", action="store_true")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    logf = os.path.join(args.out, "log.txt")
    cand_path = os.path.join(args.out, "trophic_candidates.jsonl")
    docs_path = os.path.join(args.out, "trophic_docs.jsonl")
    done_path = os.path.join(args.out, "done_queries.txt")
    GENUS_RE = re.compile(r"\b(" + "|".join(sorted(GENERA, key=len, reverse=True)) + r")\b")
    log(f"KYBELE trophic harvest v4 (genus level), output folder: {os.path.abspath(args.out)}", logf)

    if args.probe:
        for col in ("medline", "pmc", "plazi"):
            try:
                h = search_get("Collembola feeding", col, 3)
                log(f"GET {col}: {len(h)} hits; fields {sorted((h[0].get('_source') or {}).keys()) if h else '-'}", logf)
            except Exception as e:
                log(f"GET {col}: failed {e}", logf)
        for col in ("medline", "pmc"):
            try:
                h = search_genus("Protaphorura", col, 3)
                log(f"phrase {col}: {'unsupported' if h is None else len(h)} hits; "
                    f"annotations dropped: {bool(h) and 'annotations' not in (h[0].get('_source') or {})}", logf)
            except Exception as e:
                log(f"phrase {col}: failed {e}", logf)
        return

    done = set(open(done_path, encoding="utf-8").read().splitlines()) if os.path.exists(done_path) else set()
    seen = set()
    if os.path.exists(cand_path):
        for l in open(cand_path, encoding="utf-8"):
            if l.strip():
                r = json.loads(l)
                seen.add(r["key"])
    seen_docs = set()
    if os.path.exists(docs_path):
        for l in open(docs_path, encoding="utf-8"):
            if l.strip():
                seen_docs.add(json.loads(l)["doc_id"])

    tasks = [("general", q, col, GENERAL_N[col]) for q in GENERAL_QUERIES for col in ("medline", "pmc", "plazi")]
    tasks += [("food", q, col, FOOD_N[col]) for q in FOOD_QUERIES for col in ("medline", "pmc")]
    tasks += [("genus", g, col, GENUS_N[col]) for g in GENERA for col in ("medline", "pmc", "plazi")]
    phrase_ok = {"medline": True, "pmc": True, "plazi": True}
    n_new = 0
    t0 = time.time()
    for i, (kind, q, col, n) in enumerate(tasks, 1):
        tkey = f"{kind}\t{q}\t{col}"
        if tkey in done:
            continue
        try:
            hits = None
            if kind == "genus" and phrase_ok.get(col):
                try:
                    hits = search_genus(q, col, n)
                except Exception:
                    hits = None
                if hits is None:
                    phrase_ok[col] = False
                    log(f"      phrase queries not supported for {col}; using keyword search", logf)
            if hits is None:
                qq = f"{q} feeding diet food gut" if kind == "genus" else q
                hits = search_get(qq, col, n)
        except Exception as e:
            log(f"      ({i}/{len(tasks)}) {col} '{q}': failed {e}", logf)
            continue
        for h in hits or []:
            did = doc_id(h, col)
            txt = doc_text(h, col)
            if not did or not txt or (col != "plazi" and not COLLEMBOLA.search(txt)):
                continue
            s = h.get("_source") or {}
            for names, sent, ctx in candidates_from(txt):
                key = hashlib.md5(f"{col}|{did}|{sent}".encode()).hexdigest()
                if key in seen:
                    continue
                seen.add(key)
                with open(cand_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"key": key, "collection": col, "doc_id": str(did), "genera": names, "level": "genus",
                                        "sentence": sent, "context": ctx, "query": q, "query_kind": kind},
                                       ensure_ascii=False) + "\n")
                n_new += 1
                if str(did) not in seen_docs:
                    seen_docs.add(str(did))
                    with open(docs_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps({"doc_id": str(did), "collection": col,
                                            "title": s.get("title") or s.get("treatment_title") or s.get("article-title") or "",
                                            "year": s.get("pubyear") or "", "pmid": s.get("pmid") or "",
                                            "pmcid": s.get("pmcid") or "", "doi": s.get("doi") or "",
                                            "abstract": (s.get("abstract") or "")[:3000]}, ensure_ascii=False) + "\n")
        with open(done_path, "a", encoding="utf-8") as f:
            f.write(tkey + "\n")
        if i % 25 == 0:
            el = (time.time() - t0) / 60
            log(f"      ({i}/{len(tasks)}) {n_new} new candidate sentences, {len(seen_docs)} documents, {el:.1f} min", logf)
        time.sleep(0.3)

    zpath = os.path.abspath("kybele_trophic_genus.zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for name in ("trophic_candidates.jsonl", "trophic_docs.jsonl", "log.txt"):
            p = os.path.join(args.out, name)
            if os.path.exists(p):
                z.write(p, arcname=name)
    log(f"Done: {len(seen)} candidate sentences from {len(seen_docs)} documents. Upload this file to the chat: {zpath}", logf)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted. Re-run the same command to resume where it stopped.")
