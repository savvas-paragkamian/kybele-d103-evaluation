# AGENTS.md

Guide for people and AI agents working in this repository. It holds the project memory: what was
built, why it is the way it is, the rules that keep the published numbers valid, and the known
pitfalls. Read it before changing data, scripts or results. Open work is in [TODO.md](TODO.md);
the repository layout and reproduction commands are in [README.md](README.md).

Last updated: 29 September 2026.

## 1. The project in brief

- **KYBELE** (Knowledge Yield from BiodivErsity Literature through LLM Extraction) is an
  ELIXIR-funded project (January–December 2026; ELIXIR Greece, Italy and Switzerland; leads
  Stelios Ninidakis, coordinator, and Patrick Ruch, SIB). It is WP10 of the ELIXIR Science
  programme "Biodiversity, Food Security and Pathogens" (BFSP) Commissioned Services.
- **D10.3** is the deliverable "Model evaluation results based on a curated sample of taxonomic
  treatments (N>100 instances) and the actions to optimize the entire system". This repository
  holds its benchmarks, scripts and results. The deliverable text is a separate document kept by
  the coordinator; every number in it comes from the summary files in `results/`.
- **The system under test** is SIB's literature question-answering service built on
  [sibils/BioMoQA-RAG](https://github.com/sibils/BioMoQA-RAG), searching the SIBiLS collections
  Medline, PMC and Plazi.
- **The trait-mining pipeline** that consumes the QA answers is
  [ecsltae/collembola-trait-mining](https://github.com/ecsltae/collembola-trait-mining). It covers
  body size, habitat and trophic guild for 330 Collembola species from a BOLD COI dataset, and
  trophic guilds for 102 genera. Its extractor `trait_extraction_v3.py` is pinned at commit
  `1d5b5b62ab8fa6c13e5097701affdbba442c8764`. Its expert review of September 2026 is
  `review_adjudication_2026-09.csv`: 56 adjudicated species–trait pairs.
- **Taxon scope:** Collembola (springtails). Oligochaeta will follow when its resources are ready.

## 2. Three evaluations

| Evaluation | Where | Size | Question |
|---|---|---|---|
| Treatment benchmark | `data/benchmark_traits.csv`, `results/traits_main/`, `results/traits_repeat/` | 126 questions (60 body size, 59 habitat, 7 trophic) from 126 Plazi treatments | Can the service read a trait from a taxonomic treatment? |
| Trophic-guild benchmark | `data/benchmark_trophic.csv`, `results/trophic/` | 102 diet questions (81 species, 21 genus level) from 69 Medline/PMC/Plazi documents | Can it find what a springtail eats, and does the pipeline record it? |
| Expert-reviewed trait mining | in collembola-trait-mining, not here | 56 adjudicated pairs | Does the pipeline's output survive expert review? |

## 3. Running things

- **Network.** The scripts call `https://biodiversitypmc.sibils.org/api` (search) and
  `https://qa.sibils.org/api` (QA, formerly `qa.dev.sibils.org`). Some sandboxes, including the
  one used to build this repository, cannot reach sibils.org. All runs so far were made on the
  coordinator's own computer. Every script that calls the network uses the Python standard
  library only, so it runs anywhere with Python 3.8 or later.
- **Resumable.** The runner and the harvesters append to JSONL files and skip finished work.
  Re-running the same command resumes the run and retries the failures.
- **Runner input.** `scripts/kybele_d103_eval.py --out <folder>` reads `<folder>/candidates.csv`
  and samples nothing when that file exists. The file needs the runner's own columns, so make it
  with `scripts/bench_to_candidates.py <benchmark.csv> <folder>/candidates.csv`. Copying a
  benchmark file directly does not work, because the runner reads `species`, not `taxon`.
- **Scoring needs** `scripts/trait_extraction_v3.py` (see the README for the pinned download).
  It is git-ignored because the upstream repository states no licence.
- **Five configurations:** `doc_extractive` and `doc_generative` supply the gold document through
  `doc_refs`; `e2e_sparse_extractive`, `e2e_sparse_generative` (the API default, and the mode the
  trait pipeline uses) and `e2e_dense_generative` retrieve on their own. The doc configurations
  try the document ID first, then the title, then the taxon name, and record
  `doc_ref_hit_gold`.

## 4. Rules that keep the results valid

1. **Never edit `results/` by hand.** Re-run and re-score. The summaries must reproduce byte for
   byte from `runs.jsonl`:
   ```bash
   T=$(mktemp -d)
   python3 scripts/score_traits.py  data/benchmark_traits.csv  results/traits_main/runs.jsonl $T && cmp $T/summary_traits.json  results/traits_main/summary_traits.json
   python3 scripts/score_trophic.py data/benchmark_trophic.csv results/trophic/runs.jsonl     $T && cmp $T/summary_trophic.json results/trophic/summary_trophic.json
   ```
2. **`data/benchmark_trophic.csv` is generated.** Change `data/curation/trophic/curation_*.py`
   and rebuild with `cd data/curation/trophic && python3 build_trophic.py`. Never edit the CSV.
   `P` IDs are assigned in sort order (species first, then genera, alphabetical), so adding an
   item renumbers the later ones. Use `curation_ref` (T…, G…, X…) as the stable key.
3. **`data/benchmark_traits.csv` is curated directly.** Its `K` IDs are stable and never reused;
   gaps are dropped candidates. The curation scripts in `data/curation/traits/` record the
   decisions but cannot be rerun from this repository alone.
4. **Gold format.** Alternatives are separated by ` || `, and any of them counts. Guilds are
   `|`-separated, from `fungivore`, `bacterivore`, `microbivore`, `algivore`, `herbivore`,
   `predator`, `detritivore` and `omnivore` (the Potapov et al. 2022 scheme used by the
   pipeline). `microbivore` also matches `fungivore` and `bacterivore`.
5. **Any change to a scorer or to the pinned extractor means re-scoring every run.** Then update
   the README tables, and tell the coordinator which D10.3 numbers moved.
6. **Trophic numbers always come with the baseline.** A constant answer "fungi" already scores
   63 % (per-question gold guilds) or 75 % (taxon gold guilds) on guild. Report the named food and
   the non-fungal subset beside any guild accuracy.
7. **A new run goes in a new folder** under `results/`, together with its `log.txt`, which
   records the runner version. Replace local paths in logs with `.`.

## 5. Curation rules

**Treatment benchmark (traits).** Plazi Collembola treatments indexed by SIBiLS were sampled by
querying 28 family names and 6 generic queries (up to 100 hits each; 859 treatments kept, see
`data/sampling_frame.csv`). Candidates were drawn at random with a fixed seed (2026), round-robin
across families, one question per treatment. The final set covers 15 families, and 2 questions
have no family. Gold answers are verbatim spans with the surrounding passage. Candidates were
dropped when the taxon was not a springtail, the species or article was already used, or the
text gave no clear answer. There were two rounds: 139 of 150 kept, of which 51 body-size or
habitat questions were retained; then 74 of 97, plus K248 added by hand. Curation was
AI-assisted. A specialist spot-check of 25 questions is pending (`spotcheck/`).

**Trophic-guild benchmark.**
- **Harvest:** 1,033 candidate sentences. Species level: general and food-specific feeding
  queries, then one and a deeper second query per trait-mining species. Genus level: one query
  per genus for 168 genera. A sentence is a candidate when it names a springtail species or genus
  together with a feeding cue.
- **Review:** 295 taxon–document pairs were checked against their context and 101 kept. One more
  question (X001, Folsomia fimetarioides) comes from the expert review.
- **Keep:** what the taxon eats, from field observation, gut content, stable isotopes or fatty
  acids, laboratory feeding or preference trials, or cited literature. A bare guild label counts
  when the document states it as the taxon's feeding mode (a description of the study organism,
  or a statement with a citation).
- **Drop:**
  - the springtail as prey;
  - occurrence or substrate taken as diet;
  - laboratory culture, stock or toxicity-test diets;
  - statements about Collembola in general;
  - reference-list entries and table fragments;
  - labels used in passing, or only to name a role in an experimental food web;
  - Medline or PMC copies of a document already used;
  - a genus item that repeats a species item from the same experiment.
- **Caps:** one question per taxon and document; at most 4 questions per document; at most 6
  documents per taxon (15 for Folsomia candida, which has 14).
- **Hedged statements** ("suggesting", "assumed") are kept and flagged (18).
- **Questions:** "What does *species* feed on?" for species. For genera the wording is
  "What does *genus* feed on?", exactly as the pipeline asks.
- **Gold:** food items and guilds. Gut-content tables list ingested non-food (mineral
  particles); leave that out of the gold.

## 6. Scoring definitions

- **String metrics** (`score.py`): exact match, answer contains, SQuAD F1, ROUGE-L without
  stemming, and a lexical faithfulness proxy. These follow SIB's D10.2 metrics. They penalise
  correct paraphrases ("1.0 millimeter" against "1 mm"), so they are secondary.
- **Trait level** (`score_traits.py`, primary for the treatment benchmark), applied to the first
  Plazi answer:
  - body size: correct if a stated value in mm is within 2 % of a gold value;
  - habitat: correct if the 13 habitat classes of `trait_extraction_v3` overlap the gold classes;
    an answer that is only a place counts as "geography" (reported as wrong in D10.3);
  - four habitat questions (K053, K203, K205, K225) cannot be scored, so n = 122.
- **Trophic** (`score_trophic.py`), applied to the answer with the highest `answer_score`, as the
  pipeline picks it:
  - *food named*: a gold food item appears verbatim in the answer. This is strict and the most
    informative measure.
  - *guild of the answer*: guilds read sentence by sentence, skipping sentences that say the diet
    is not stated, with the extractor's vocabulary extended by the terms it misses.
  - *guild recorded by the pipeline*: the primary guild of `trait_extraction_v3` for species; the
    genus classifier (`infer_guilds` from `collembola_trophic_batch.py`) for genera.
  - End-to-end answers are scored against the union of the taxon's gold guilds.
- **Intervals:** 95 % Wilson intervals throughout. Round percentages from exact counts, not
  from the 3-decimal summaries (for example 74/102 = 72.55 % is 73 %).

## 7. Key results (the numbers in D10.3)

Treatment benchmark, main run (`results/traits_main/`, 28 September 2026; resumed several times with successive runner versions, so its log has no version tag; the repeat run used v4), correct %:

| Configuration | All (n) | Body size | Habitat | Wrong incl. place only |
|---|--:|--:|--:|--:|
| doc_extractive | 61.5 (122) | 83.3 | 43.6 | 20.5 |
| doc_generative | 49.2 (122) | 55.0 | 45.5 | 6.6 |
| e2e_sparse_extractive | 39.3 (122) | 53.3 | 27.3 | 29.5 |
| e2e_sparse_generative | 45.1 (122) | 58.3 | 32.7 | 11.5 |
| e2e_dense_generative | 40.9 (22) | 64.3 | 0.0 | 13.6 |

- Repeat run, correct %: 61.5, 50.0, 39.3, 44.3 and 36.4 in the same order.
- Dense generative answered only 24 of 126 questions; the rest were server errors.
- 57 % of gold answers lie more than 1,500 characters into the treatment. The extractive reader
  finds body size 96 % of the time before that point and 33 % after it.
- A PMC answer was ranked first for 94 of 126 questions.
- All 20 wrong end-to-end body sizes came from other documents, for example a mayfly sharing
  the epithet.

Trophic-guild benchmark (`results/trophic/`, runner v5, 29 September 2026):

| Configuration | n | Food named | Guild of the answer | Guild recorded by the pipeline | Gold document retrieved |
|---|--:|--:|--:|--:|--:|
| doc_extractive | 102 | 66 % | 77 % | – | 100 % |
| doc_generative | 102 | 69 % | 85 % | 61 % | 100 % |
| e2e_sparse_extractive | 102 | 16 % | 31 % | – | 55 % |
| e2e_sparse_generative | 102 | 44 % | 88 % | 73 % | 55 % |
| e2e_dense_generative | 80 | 41 % | 88 % | 71 % | 48 % |

- On the non-fungal questions, the generative answer's guild is right in 82 % given the source
  and 81 % end to end.
- Wrong guilds run at 4–8 % across configurations.
- Why the pipeline records fewer right guilds than the answers contain:
  - its vocabulary misses litter, roots, carcasses, invertebrates and named fungi or bacteria
    (it recognises the gold guild in 73 of 102 gold answers);
  - a closing caveat demotes every guild to indirect (10 of 81 species answers given the source);
  - the genus classifier treats "collembola", "mite" and "arthropod" as predator keywords
    (5 of 21 genus answers).

Expert-reviewed trait mining (from collembola-trait-mining):
- The reviewers flagged 27 of 40 trophic guilds (68 %) and 14 of 27 body sizes. The repository
  summary says 15; this is still to be reconciled.
- Claim-level extraction (version 3) removed 49 of the 56 flagged values (88 %) and reached the
  expected value in 42 (75 %).
- Actions A1–A5 below are implemented in the pipeline and the service.

| # | Implemented action |
|---|---|
| A1 | Full binomial required as an adjacent phrase in retrieval (`enforce_taxon_phrase`, now the BioMoQA-RAG default) |
| A2 | Each value bound to the sentence that asserts it, and to the nearest preceding taxon heading in treatments |
| A3 | Evidence classed as direct, experimental, co-occurrence, prey-of or non-specific |
| A4 | A habitat needs an ecological descriptor, not a place name |
| A5 | Two-tier output: a primary value, plus an indirect column recording why weaker evidence was set aside |

The planned actions P1–P17 are in [TODO.md](TODO.md).

## 8. Decision log

| Date | Decision | Why |
|---|---|---|
| 2026-09-28 | Collembola only, N > 100 | The deliverable title requires N > 100; Oligochaeta resources were not ready |
| 2026-09-28 | Trait questions only (body size, habitat, trophic); type locality, holotype and etymology dropped | The project mines these traits; body size is the most reliable |
| 2026-09-28 | Trait-level scoring as the primary metric | String metrics penalise correct paraphrases of units and wording |
| 2026-09-28 | QA endpoint moved to `https://qa.sibils.org/api` | `qa.dev.sibils.org` returned 503; the coordinator supplied the new endpoint |
| 2026-09-28 | Server-error detection and retries in the runner; dense requests run sequentially | Dense generative silently returned empty results with no model; the failure is deterministic when BM25 finds few documents |
| 2026-09-28 | Separate trophic benchmark from Medline, PMC and Plazi | Only 13 of 859 treatments mention feeding, and 7 describe what a springtail eats |
| 2026-09-29 | Genus-level trophic questions in the pipeline's wording | The species literature was exhausted at about 80 questions; the pipeline assigns guilds by genus |
| 2026-09-29 | Document cap of 4 questions | Round 1 already had documents with 4 questions; one rule for the whole set |
| 2026-09-29 | Food named as the primary trophic measure, plus baselines | A constant "fungi" answer scores 63–75 % on guild |
| 2026-09-29 | Sentence-level guild reading for the answer; pipeline reading kept separate | The extractor's answer-wide denial rule hid correct answers; both views are needed |
| 2026-09-29 | `trait_extraction_v3.py` not vendored | The upstream repository has no licence |
| 2026-09-29 | Code MIT, data CC BY 4.0 | Coordinator's default; change in LICENSE, LICENSE-DATA and CITATION.cff if needed |

## 9. Known issues and pitfalls

- **Runner versions.** Only v5 (this repository) has every fix; the trophic run used v5 and the repeat trait run v4. Check the first line of
  `log.txt` ("runner v5"). A browser may save a second download as
  `kybele_d103_eval(1).py`, and the old file then runs by mistake.
- **Dense generative server error.** The service returns an empty result with `model: ""` and
  `pipeline_time: null` instead of an HTTP error. This hit 102 of 126 trait questions and 22 of
  102 trophic questions. The runner and scorers treat it as a failure (planned action P1).
- **doc_refs resolution** in BioMoQA-RAG is a keyword search. If an ID is not found exactly, it
  falls back to the top hit, which can be a different document. Always check
  `doc_ref_hit_gold`; it was true for all 126 trait and all 102 trophic questions.
- **`trait_extraction_v3` on genus targets** reads "Agrenia feeds" as a binomial and demotes the
  statement. That is why genus answers are read with the genus classifier.
- **Gold incompleteness.** A trophic gold answer comes from one statement. Another sentence in
  the same document may support a different guild (for example Tomocerus minor, P079), so the
  wrong rate is an upper bound.
- **Messages meant for the original workflow.** The runner and harvesters still print "upload
  this file to the chat". This is harmless.
- **`data/curation/traits/build2.py`** writes to a hard-coded path and reads files that are not
  in the repository. Treat it as a record, not as a pipeline.
- **`results/traits_main/runs.jsonl`** also contains runs for questions of an earlier benchmark
  version. The scorers skip them.

## 10. Service and data facts

- **BioMoQA-RAG:** commit `13abd69` (19 August 2026), still to be confirmed as the version
  deployed on qa.sibils.org.
  - Endpoint: `POST /api/qa/multi` with `question`, `mode` (`extractive` or `generative`),
    `retrieval` (`sparse` or `dense`), `doc_refs` and `debug`.
  - Sparse retrieval: SIBiLS BM25, 10 documents per collection, top 5 kept.
  - Dense retrieval: BM25 plus FAISS (S-PubMedBert-MS-MARCO), fused by reciprocal rank and
    re-ranked by the ms-marco-MiniLM-L-12-v2 cross-encoder.
  - Extractive reader: `ktrapeznikov/biobert_v1.1_pubmed_squad_v2`, about 1,500 characters per
    document.
  - Generative reader: Qwen3-8B (FP8, vLLM), about 600 characters per document, chosen by a
    keyword window.
- **Document IDs** as the service returns them: PMID for Medline, PMCID for PMC (or the DOI when
  there is no PMCID), and the Plazi treatment hex ID for Plazi.
- **Seeds:** trait sampling 2026 (runner `--seed`); specialist spot-check 20260928.
- **ID ranges:**
  - trait questions: `K001`–`K248`, with gaps for dropped candidates;
  - trophic questions: `P001`–`P102`;
  - trophic review IDs: `T001`–`T100` (round 1), `T101`–`T137` and `T201`–`T216` (round 2),
    `T301`–`T392` (round 3), `G001`–`G050` (genus level), `X001` (expert).

## 11. Working conventions

- Keep one change per commit, and say in the message whether results were re-scored.
- Run `python3 -m py_compile scripts/*.py` and the reproduction check in section 4 before pushing.
- Keep the scripts standard-library only where they call the network. `make_spotcheck.py`
  (openpyxl) is the exception.
- Owners: SIB for the QA service (P1–P5). The trait-mining team for the pipeline and vocabularies
  (P6–P17; the node is still to be named). The coordinator for the deliverable and releases.
