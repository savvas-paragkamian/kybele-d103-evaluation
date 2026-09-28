#!/usr/bin/env python3
"""
KYBELE D10.3 trophic-guild harvest (Collembola diet statements from SIBiLS)
============================================================================

Collects candidate diet statements for springtail species from the SIBiLS collections the
KYBELE QA service searches (Medline abstracts, PMC full texts, Plazi treatments):

  1. 20 general Collembola feeding queries in Medline, PMC and Plazi.
  2. One query per species for the 330 species of the KYBELE trait-mining list, in Medline
     and PMC, requiring the full binomial as a phrase where the API allows it.

Only sentences that name a springtail species AND contain a feeding cue are kept, with one
sentence of context on each side, so the output stays small. Everything ends up in
kybele_trophic_harvest.zip; upload that file to the chat for curation.

Requirements: Python 3.8+, standard library only.
Usage:
    python3 kybele_trophic_harvest.py --probe     # 1-minute check
    python3 kybele_trophic_harvest.py             # full run, about 20-40 min, resumable
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
UA = "KYBELE-D10.3-trophic-harvest/1.0 (ELIXIR KYBELE project)"

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
GENUS_N = {"medline": 30, "pmc": 20}
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

SEED = json.loads(r'''{"species":["Agrenia bidenticulata","Allacma fusca","Anurida granaria","Anurida granulata","Anurida maritima","Anurida polaris","Anurida thalassophila","Anurida tullbergi","Anurophorus atlanticus","Anurophorus laricis","Anurophorus septentrionalis","Archisotoma interstitialis","Archisotoma megalops","Archisotoma pulchella","Arrhopalites caecus","Ballistura borealis","Bilobella aurantiaca","Bilobella braunerae","Bilobella massoudi","Bourletiella arvalis","Bourletiella viridescens","Brachystomella parvula","Ceratophysella bengtssoni","Ceratophysella cavicola","Ceratophysella denticulata","Ceratophysella engadinensis","Ceratophysella gibbosa","Ceratophysella granulata","Ceratophysella longispina","Ceratophysella scotica","Ceratophysella sigillata","Ceratophysella stachi","Ceratophysella succinea","Choreutinula inermis","Choreutinula kulla","Cribrochiurus subcribrosus","Cryptopygus clavatus","Cyphoderus albinus","Desoria blekeni","Desoria blufusata","Desoria calderonis","Desoria fennica","Desoria grisea","Desoria hiemalis","Desoria infuscata","Desoria intermedia","Desoria neglecta","Desoria nivea","Desoria olivacea","Desoria orobica","Desoria propinqua","Desoria saltans","Desoria tigrina","Desoria tolya","Desoria trispinata","Desoria tshernovi","Desoria violacea","Detriturus jubilarius","Deuteraphorura kratochvili","Deuteraphorura scotaria","Deutonura albella","Deutonura caerulescens","Deutonura decolorata","Deutonura deficiens","Deutonura gibbosa","Deutonura monticola","Deutonura provincialis","Deutonura stachi","Dicyrtoma aurata","Dicyrtoma fusca","Dicyrtomina minuta","Dicyrtomina ornata","Dicyrtomina saundersi","Endonura gracilirostris","Entomobrya albocincta","Entomobrya assuta","Entomobrya atrocincta","Entomobrya corticalis","Entomobrya handschini","Entomobrya intermedia","Entomobrya lanuginosa","Entomobrya marginata","Entomobrya multifasciata","Entomobrya muscorum","Entomobrya nicoleti","Entomobrya nivalis","Entomobrya quinquelineata","Entomobrya unostrigata","Folsomia agrelli","Folsomia binoculata","Folsomia bisetosa","Folsomia candida","Folsomia ciliata","Folsomia coeruleogrisea","Folsomia fimetaria","Folsomia fimetarioides","Folsomia inoculata","Folsomia manolachei","Folsomia palaearctica","Folsomia penicula","Folsomia quadrioculata","Folsomia sensibilis","Folsomia sexoculata","Folsomia spinosa","Folsomia thalassophila","Folsomides angularis","Folsomides parvulus","Friesea atypica","Friesea claviseta","Friesea mirabilis","Friesea quinquespinosa","Friesea truncata","Gisinianus flammeolus","Gnathisotoma bicolor","Halisotoma arenicola","Halisotoma maritima","Hemisotoma thermophila","Heteraphorura carpatica","Heteromurus absoloni","Heteromurus major","Heteromurus nitidus","Hymenaphorura dentifera","Hymenaphorura parva","Hymenaphorura polonica","Hymenaphorura pseudosibirica","Hypogastrura assimilis","Hypogastrura burkilli","Hypogastrura concolor","Hypogastrura distincta","Hypogastrura kelmendica","Hypogastrura monticola","Hypogastrura purpurescens","Hypogastrura sahlbergi","Hypogastrura socialis","Hypogastrura subboldorii","Hypogastrura tullbergi","Hypogastrura vernalis","Hypogastrura viatica","Isotoma anglicana","Isotoma caerulea","Isotoma riparia","Isotoma viridis","Isotomiella minor","Isotomiella paraminor","Isotomodes trisetosus","Isotomurus alticolus","Isotomurus antennalis","Isotomurus balteatus","Isotomurus cassagnaui","Isotomurus gallicus","Isotomurus graminis","Isotomurus maculatus","Isotomurus palustris","Isotomurus plumosus","Isotomurus pseudopalustris","Isotomurus stuxbergi","Isotomurus unifasciatus","Kalaphorura paradoxa","Lathriopyga longiseta","Lepidocyrtus cyaneus","Lepidocyrtus fimetarius","Lepidocyrtus lanuginosus","Lepidocyrtus lignorum","Lepidocyrtus pallidus","Lepidocyrtus paradoxus","Lepidocyrtus ruber","Lepidocyrtus violaceus","Lepidocyrtus weidneri","Lipothrix lubbocki","Marisotoma canaliculata","Megalothorax carpaticus","Megalothorax hipmani","Megalothorax incertus","Megalothorax minimus","Megalothorax perspicillum","Megalothorax sanctistephani","Megalothorax svalbardensis","Megalothorax tatrensis","Megalothorax willemi","Megaphorura arctica","Mesaphorura florae","Mesaphorura hylophila","Mesaphorura krausbaueri","Mesaphorura macrochaeta","Mesaphorura simplex","Mesogastrura libyca","Metaphorura affinis","Metaphorura denisi","Micranurida forsslundi","Micranurida meridionalis","Micranurida pygmaea","Monobella grassei","Neanura moldavica","Neanura muscorum","Neelides minutus","Neelus koseli","Oligaphorura absoloni","Oligaphorura groenlandica","Oligaphorura uralica","Oligaphorura ursi","Oncopodura crassicornis","Onychiuroides alpinus","Onychiuroides granulosus","Onychiurus ambulans","Onychiurus folsomi","Orchesella bifasciata","Orchesella cincta","Orchesella flavescens","Orchesella multifasciata","Orchesella orientalis","Orchesella pseudobifasciata","Orchesella spectabilis","Orchesella villosa","Orthonychiurus rectopapillatus","Pachyotoma curva","Paratullbergia callipygos","Parisotoma agrelli","Parisotoma ekmani","Parisotoma notabilis","Podura aquatica","Pogonognathellus flavescens","Pogonognathellus longicornis","Proisotoma clavipila","Proisotoma minima","Proisotoma minuta","Proisotomodes bipunctatus","Protaphorura armata","Protaphorura aurantiaca","Protaphorura campata","Protaphorura cancellata","Protaphorura fimata","Protaphorura glebata","Protaphorura janosik","Protaphorura macfadyeni","Protaphorura pannonica","Protaphorura pseudovanderdrifti","Protaphorura subarmata","Protaphorura subuliginata","Protaphorura tricampata","Pseudachorutella asigillata","Pseudachorutes dubius","Pseudachorutes palmiensis","Pseudachorutes parvulus","Pseudachorutes subcrassus","Pseudanurophorus alticolus","Pseudisotoma monochaeta","Pseudisotoma sensibilis","Pseudosinella alba","Pseudosinella decipiens","Pseudosinella duodecimoculata","Pseudosinella halophila","Pseudosinella horaki","Pseudosinella imparipunctata","Pseudosinella ksenemani","Pseudosinella moldavica","Pseudosinella noseki","Pseudosinella octopunctata","Pseudosinella paclti","Pseudosinella sexoculata","Pygmarrhopalites principalis","Pygmarrhopalites pygmaeus","Rusekianna albifrons","Schoettella ununguiculata","Scutisotoma armeriae","Scutisotoma subarctica","Seira pallidipes","Sminthurides aquaticus","Sminthurides malmgreni","Sminthurides parvulus","Sminthurides schoetti","Sminthurinus alpinus","Sminthurinus aureus","Sminthurinus bimaculatus","Sminthurinus concolor","Sminthurinus domesticus","Sminthurinus elegans","Sminthurinus niger","Sminthurinus quadrimaculatus","Sminthurinus reticulatus","Sminthurinus signatus","Sminthurinus trinotatus","Sminthurus nigromaculatus","Sminthurus viridis","Sphaeridia pumilis","Stenacidia violacea","Stenaphorura denisi","Stenaphorura quadrispina","Subisotoma pusilla","Superodontella alpina","Superodontella gisini","Supraphorura furcifera","Tetracanthella brachyura","Tetracanthella fjellbergi","Tetracanthella strenzkei","Tetracanthella wahlgreni","Tetrodontophora bielanensis","Thalassaphorura encarpata","Thaumanura carolii","Tomocerina minuta","Tomocerus baudoti","Tomocerus minor","Tomocerus problematicus","Tomocerus vulgaris","Vertagopus alpinus","Vertagopus arboreus","Vertagopus fradustaensis","Vertagopus glacialis","Vertagopus glacieinigrae","Vertagopus pseudocinereus","Vertagopus psychrophilus","Vertagopus sarekensis","Willemia anophthalma","Willemia denisi","Willemia scandinavica","Willemia similis","Willowsia buski","Willowsia nigromaculata","Xenylla acauda","Xenylla boerneri","Xenylla brevisimilis","Xenylla humicola","Xenylla maritima","Xenylla mediterranea","Xenylla nitida","Xenylla pomorskii","Xenylla szeptyckii","Xenylla tullbergi","Xenylla xavieri","Xenyllodes armatus","Xenyllodes psammo"],"genera":["Agrenia","Allacma","Allonychiurus","Alloscopus","Anurida","Anurophorus","Archisotoma","Arrhopalites","Australotomurus","Austrodontella","Austrogastrura","Axelsonia","Ballistura","Bilobella","Borgesminthurinus","Bourletiella","Brachystomella","Ceratophysella","Choreutinula","Coecobrya","Coenaletes","Cribrochiurus","Crossodonthina","Cryptopygus","Cylindropygus","Cyphoderopsis","Cyphoderus","Denisiella","Desoria","Detriturus","Deuteraphorura","Deuterosminthurus","Deutonura","Dicranocentrus","Dicyrtoma","Dicyrtomina","Endonura","Entomobrya","Ephemerotoma","Folsomia","Folsomides","Folsomotoma","Friesea","Gisinianus","Gnathisotoma","Gomphiocephalus","Gressittacantha","Halisotoma","Hemisotoma","Heteraphorura","Heteroisotoma","Heteromurus","Homidia","Hymenaphorura","Hypogastrura","Isotogastrura","Isotoma","Isotomiella","Isotomodes","Isotomurus","Kalaphorura","Katianna","Keratosminthurus","Lathriopyga","Leeonychiurus","Lepidocyrtoides","Lepidocyrtus","Lipothrix","Lobellina","Marisotoma","Mastigoceras","Megalothorax","Megaphorura","Mesaphorura","Mesogastrura","Metacoelura","Metaphorura","Mexicaphorura","Micranurida","Micronella","Monobella","Monodontocerus","Mucrosomia","Multivesicula","Narynia","Neanura","Neelides","Neelus","Neonaphorura","Neorganella","Odontella","Oligaphorura","Oncopodura","Onychiuroides","Onychiurus","Orchesella","Orthonychiurus","Pachyotoma","Palmanura","Papirioides","Paralobella","Paratullbergia","Parisotoma","Plutomurus","Podura","Pogonognathellus","Polydiscia","Prabhergia","Proisotoma","Proisotomodes","Protaphorura","Pseudachorutella","Pseudachorutes","Pseudanurophorus","Pseudisotoma","Pseudoparonella","Pseudosinella","Ptenothrix","Pygmarrhopalites","Rhodanella","Rusekianna","Salina","Schoettella","Scutisotoma","Seira","Semicerura","Sensillonychiurus","Sensiphorura","Sernatropiella","Setanodosa","Simonachorutes","Sinella","Sinoncopodura","Skadisotoma","Sminthurides","Sminthurinus","Sminthurus","Sphaeridia","Spinaethorax","Spinonychiurus","Stenacidia","Stenaphorura","Stenognathriopes","Subisotoma","Superodontella","Supraphorura","Szeptyckitheca","Temeritas","Tetracanthella","Tetrodontophora","Thalassaphorura","Thaumanura","Tomocerina","Tomocerus","Triacanthella","Troglobius","Troglopedetes","Trogolaphysa","Tullbergia","Uralaphorura","Uzelia","Vertagopus","Willemia","Willowsia","Xenylla","Xenyllodes"]}''')


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


def binomials(sentence, known):
    """Full binomials of springtail genera in the sentence, plus abbreviations (F. candida) resolved
    against full names seen earlier in the same document."""
    out = []
    for m in GENUS_RE.finditer(sentence):
        out.append(f"{m.group(1)} {m.group(2)}")
    for m in re.finditer(r"\b([A-Z])\.\s*([a-z]{3,})\b", sentence):
        for k in known:
            g, e = k.split()[0], k.split()[1]
            if g[0] == m.group(1) and e == m.group(2):
                out.append(k)
                break
    return list(dict.fromkeys(out))


def candidates_from(text):
    sents = _SPLIT.split(text)
    known = []
    found = []
    for i, s in enumerate(sents):
        names = binomials(s, known)
        for nme in names:
            if nme not in known:
                known.append(nme)
        if names and DIET.search(s) and len(s) < 1200:
            ctx = " ".join(sents[max(0, i - 1): i + 2])
            found.append((names, s, ctx[:2500]))
    return found


def main():
    global GENUS_RE
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="kybele_trophic")
    ap.add_argument("--probe", action="store_true")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    logf = os.path.join(args.out, "log.txt")
    cand_path = os.path.join(args.out, "trophic_candidates.jsonl")
    docs_path = os.path.join(args.out, "trophic_docs.jsonl")
    done_path = os.path.join(args.out, "done_queries.txt")
    GENUS_RE = re.compile(r"\b(" + "|".join(sorted(SEED["genera"], key=len, reverse=True)) + r")\s+([a-z]{3,})\b")
    log(f"KYBELE trophic harvest v3, output folder: {os.path.abspath(args.out)}", logf)

    if args.probe:
        for col in ("medline", "pmc", "plazi"):
            try:
                h = search_get("Collembola feeding", col, 3)
                log(f"GET {col}: {len(h)} hits; fields {sorted((h[0].get('_source') or {}).keys()) if h else '-'}", logf)
            except Exception as e:
                log(f"GET {col}: failed {e}", logf)
        for col in ("medline", "pmc"):
            try:
                h = search_phrase("Folsomia candida", col, 3)
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
    tasks += [("species", sp, col, SPECIES_N[col]) for sp in SEED["species"] for col in ("medline", "pmc")]
    tasks += [("food", q, col, FOOD_N[col]) for q in FOOD_QUERIES for col in ("medline", "pmc")]
    tasks += [("species2", sp, col, SPECIES2_N[col]) for sp in SEED["species"] for col in ("medline", "pmc")]
    genera = sorted({sp.split()[0] for sp in SEED["species"]})
    tasks += [("genus", g, col, GENUS_N[col]) for g in genera for col in ("medline", "pmc")]
    phrase_ok = {"medline": True, "pmc": True}
    n_new = 0
    t0 = time.time()
    for i, (kind, q, col, n) in enumerate(tasks, 1):
        tkey = f"{kind}\t{q}\t{col}"
        if tkey in done:
            continue
        try:
            hits = None
            if kind in ("species", "species2", "genus") and phrase_ok.get(col):
                try:
                    hits = search_genus(q, col, n) if kind == "genus" else search_phrase(q, col, n)
                except Exception:
                    hits = None
                if hits is None:
                    phrase_ok[col] = False
                    log(f"      phrase queries not supported for {col}; using keyword search", logf)
            if hits is None:
                qq = f"{q} feeding diet food gut" if kind in ("species", "species2", "genus") else q
                hits = search_get(qq, col, n)
        except Exception as e:
            log(f"      ({i}/{len(tasks)}) {col} '{q}': failed {e}", logf)
            continue
        for h in hits or []:
            did = doc_id(h, col)
            txt = doc_text(h, col)
            if not did or not txt:
                continue
            s = h.get("_source") or {}
            for names, sent, ctx in candidates_from(txt):
                key = hashlib.md5(f"{col}|{did}|{sent}".encode()).hexdigest()
                if key in seen:
                    continue
                seen.add(key)
                with open(cand_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"key": key, "collection": col, "doc_id": str(did), "species": names,
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

    zpath = os.path.abspath("kybele_trophic_harvest.zip")
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
