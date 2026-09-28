# KYBELE D10.3 evaluation: Collembola trait question answering

This repository publishes the scripts, benchmark and results of deliverable D10.3 of KYBELE
(Knowledge Yield from BiodivErsity Literature through LLM Extraction), an ELIXIR-funded project
(January–December 2026; ELIXIR Greece, Italy and Switzerland; leads Stelios Ninidakis and
Patrick Ruch). D10.3 is titled
"Model evaluation results based on a curated sample of taxonomic treatments (N>100 instances)
and the actions to optimize the entire system". It evaluates the SIB / SIBiLS biomedical and
biodiversity question-answering service (API `https://qa.sibils.org/api`, code
[sibils/BioMoQA-RAG](https://github.com/sibils/BioMoQA-RAG) at commit `13abd69`; generative
model Qwen/Qwen3-8B-FP8, extractive reader ktrapeznikov/biobert_v1.1_pubmed_squad_v2, as reported
by the service during the runs) on 126 curated questions about the body size, habitat and trophic
guild of Collembola (springtails), taken from Plazi taxonomic treatments, in five retrieval and
answering configurations.

## Repository layout

| Path | Content |
|---|---|
| `data/benchmark_traits.csv` | The trait benchmark: 126 questions with gold answers |
| `data/sampling_frame.csv` | Metadata of the 859 Plazi treatments the questions were drawn from (no treatment text) |
| `data/curation/traits/` | Raw candidates and curation decisions for the trait benchmark (two rounds) |
| `data/benchmark_trophic.csv` | The trophic-guild benchmark: 102 diet questions (81 species, 21 genus level) with gold food items and gold guilds |
| `data/curation/trophic/` | Candidate sentences, review sheets, curation decisions and `build_trophic.py` for the trophic-guild benchmark |
| `scripts/kybele_d103_eval.py` | QA runner: sends the questions to the QA API in five configurations |
| `scripts/bench_to_candidates.py` | Converts `benchmark_traits.csv` into the runner's input file |
| `scripts/score.py` | String metrics (exact match, answer contains, SQuAD F1, ROUGE-L, faithfulness proxy, gold retrieval) |
| `scripts/score_traits.py` | Trait-level scoring (correct / wrong / no answer); needs `trait_extraction_v3.py`, see below |
| `scripts/kybele_trophic_harvest.py` | Harvests candidate species-level diet statements from SIBiLS (Medline, PMC, Plazi) |
| `scripts/kybele_trophic_genus.py` | Harvests candidate genus-level diet statements from SIBiLS |
| `scripts/score_trophic.py` | Trophic-guild scoring (guilds with the pipeline's vocabulary and with an extended one, food match, gold retrieval) |
| `scripts/make_spotcheck.py` | Draws the specialist spot-check sample and writes the reviewer workbook (needs `openpyxl`) |
| `spotcheck/` | Spot-check sample (25 questions) and reviewer workbook |
| `results/traits_main/` | Main run: raw responses (`runs.jsonl`), log, `scored.csv`, `summary.json`, `scored_traits.csv`, `summary_traits.json` |
| `results/traits_repeat/` | Repeat run of the same 126 questions, same files |
| `results/trophic/` | Trophic-guild run: raw responses, log, `scored.csv`, `summary.json`, `scored_trophic.csv`, `summary_trophic.json` |
| `LICENSE`, `LICENSE-DATA`, `CITATION.cff` | Licences and citation metadata |

## Trait benchmark

`data/benchmark_traits.csv` holds 126 questions, one per treatment and species, from Plazi
Collembola treatments indexed by SIBiLS:

| Trait (`question_type`) | Questions | Template |
|---|--:|---|
| `body_size` | 60 | What is the body length of *species*? |
| `habitat` | 59 | What is the habitat of *species*? |
| `trophic_guild` | 7 | What does *species* feed on? |

**Sampling.** The runner queried the SIBiLS Plazi collection with the names of 28 Collembola
families plus 6 generic queries (for example "Collembola new species"), up to 100 hits each, and
kept 859 species-level Collembola treatments with text (`data/sampling_frame.csv`). Candidate
questions were drawn at random with a fixed seed, stratified by family (round-robin across the
family strata, one question per treatment). The final questions cover 15 families; 2 are
unassigned.

**Curation.** Candidates were curated with AI assistance against the treatment text in two
rounds: round 1 (`candidates_raw_round1.csv`, 150 candidates over six question types; 139 kept
in `benchmark_round1_139.csv`, of which the 51 body-length and habitat questions were retained)
and round 2 (`candidates_raw_round2.csv`, 97 trait-focused candidates; 74 kept, plus one trophic
question added by hand, K248). Candidates were dropped when the taxon was not a springtail, when
the article or species was already used, or when the text gave no clear answer. The decisions are
recorded in `curation.py` and `curation2.py`; `build2.py` assembled the benchmark. These scripts
document the process and are not runnable from this repository alone: they read the treatment
texts, which are not redistributed, and use the original file names (`candidates.csv`,
`new_candidates_raw.csv`, `benchmark.csv`, plus `candidates_curated.csv` and `treatments.jsonl`).
A specialist spot-check of 25 questions (12 body size, 12 habitat, 1 trophic guild; `spotcheck/`)
is pending.

**Gold answers** are verbatim spans from the treatment. Where several answers are acceptable,
the alternatives are separated by ` || ` and any of them counts as correct (for example
`1.7–1.8 mm || 1.7-1.8 mm`).

**Columns of `benchmark_traits.csv`**

| Column | Content |
|---|---|
| `qid` | Question identifier (K001–K248; gaps are dropped candidates) |
| `docid` | Plazi treatment identifier in SIBiLS (the gold document) |
| `taxon` | Species name used in the question |
| `family` | Collembola family (`unassigned` if none could be determined) |
| `question_type` | `body_size`, `habitat` or `trophic_guild` |
| `question` | Question text |
| `gold_answer` | Gold answer; alternatives separated by ` \|\| ` |
| `gold_context` | Treatment text around the gold answer (about 300 characters either side) |
| `answer_offset` | Character offset of the gold answer in the whitespace-normalised treatment text |
| `text_length` | Length of the whitespace-normalised treatment text |
| `treatment_title` | Title of the treatment |
| `article_title` | Title of the article the treatment belongs to |
| `doi` | DOI (Zenodo or publication) |
| `treatment_uri` | Plazi TreatmentBank URI |
| `curation_note` | Curator's note, if any |

`data/sampling_frame.csv` has the columns `docid`, `treatment_title`, `species` (derived from the
title by the runner), `family` (the family query that returned the treatment; empty for the
generic queries), `query`, `search_score`, `article_title`, `doi`, `treatment_uri` and
`text_length`.

### Trophic-guild benchmark

`data/benchmark_trophic.csv` holds 102 diet questions: 81 about 48 species ("What does *species*
feed on?") and 21 about 17 genera ("What does *genus* feed on?", the wording of the KYBELE
trait pipeline, which assigns guilds at genus level). Treatments rarely state diet, so the
questions come from Medline abstracts (26), PMC full texts (72) and Plazi treatments (4), all
indexed by SIBiLS; they cover 69 documents.

**Harvest.** `scripts/kybele_trophic_harvest.py` (species level: general and food-specific
feeding queries, then one and a deeper second query per species for the 330 trait-mining species)
and `scripts/kybele_trophic_genus.py` (genus level: one query per genus for 168 genera) keep
sentences that name a springtail species or genus together with a feeding cue. They produced
1,033 candidate sentences (`data/curation/trophic/candidate_sentences_*.jsonl`).

**Curation.** 295 taxon–document pairs were checked against their context with AI assistance
(`review*.json`) and 101 were kept (`curation_t1.py`, `curation_t2.py`, `curation_t3.py`,
`curation_g.py`); one question comes from the trait-mining expert review (Folsomia fimetarioides).
Kept: what the taxon eats, from field observation, gut content, stable isotopes or fatty acids,
laboratory feeding or preference trials, or cited literature. Dropped: the springtail as prey;
occurrence or substrate taken as diet; laboratory culture, stock or toxicity-test diets;
statements about Collembola in general; reference-list entries and table fragments; guild labels
used in passing or only to name a role in an experimental food web; Medline/PMC copies of a
document already used. Caps: one question per taxon and document, at most 4 questions per
document, at most 6 documents per taxon (15 for Folsomia candida, which has 14). Hedged statements
("suggesting", "assumed") are kept and flagged (18). Rebuild the benchmark with
`cd data/curation/trophic && python3 build_trophic.py`.

**Columns of `benchmark_trophic.csv`:** `qid` (P001–P102), `docid` (PMCID, PMID, DOI or Plazi
treatment ID of the gold document), `taxon`, `taxon_rank` (`species` or `genus`), `question`,
`gold_answer` (food items; alternatives separated by ` \|\| `), `gold_guilds` (Potapov et al. 2022
guilds, `|`-separated), `evidence` (`lab`, `literature`, `isotope`, `gut`, `field`), `hedged`,
`collection`, `source_title`, `gold_context` (the sentence with one sentence either side),
`curation_ref` (ID in the review sheets) and `curation_note`.

## Reproducing the evaluation

All scripts need Python 3.8 or later and use the standard library only, except
`make_spotcheck.py` (`openpyxl`).

**1. Run the questions through the QA service.** The runner reads a `candidates.csv` in its
output folder, with its own column names (`species` rather than `taxon`) and a `gold_answer`
column that marks the file as curated. Convert the benchmark first; copying
`benchmark_traits.csv` directly does not work.

```bash
python3 scripts/bench_to_candidates.py data/benchmark_traits.csv kybele_d103/candidates.csv
python3 scripts/kybele_d103_eval.py --probe            # connectivity check
python3 scripts/kybele_d103_eval.py --out kybele_d103  # 126 x 5 = 630 requests, about 45 min; resumable
```

The runner writes `kybele_d103/runs.jsonl` and `kybele_d103/log.txt`, and a
`kybele_d103_results.zip` in the current directory. Re-running the same command retries failed
requests. Use `--qa-base` to point to another deployment of the API.

**2. Score.** `score_traits.py` uses the habitat and trophic-guild classifiers of the KYBELE
trait-mining pipeline, `trait_extraction_v3.py` from
[ecsltae/collembola-trait-mining](https://github.com/ecsltae/collembola-trait-mining). That file
has no stated licence and is not included here; fetch the pinned version first:

```bash
curl -L -o scripts/trait_extraction_v3.py https://raw.githubusercontent.com/ecsltae/collembola-trait-mining/1d5b5b62ab8fa6c13e5097701affdbba442c8764/scripts/trait_extraction_v3.py

python3 scripts/score.py        data/benchmark_traits.csv kybele_d103/runs.jsonl kybele_d103
python3 scripts/score_traits.py data/benchmark_traits.csv kybele_d103/runs.jsonl kybele_d103
```

For the trophic-guild benchmark:

```bash
python3 scripts/bench_to_candidates.py data/benchmark_trophic.csv kybele_trophic_eval/candidates.csv
python3 scripts/kybele_d103_eval.py --out kybele_trophic_eval
python3 scripts/score_trophic.py data/benchmark_trophic.csv kybele_trophic_eval/runs.jsonl kybele_trophic_eval
```

`score_trophic.py` reads the answer the way the trait pipeline does (the highest-scoring answer
across collections) and scores its guilds twice: with the vocabulary of `trait_extraction_v3`
as it is, and with that vocabulary extended by terms it misses (litter, roots, fungal and
bacterial genus names, invertebrates and others, listed in the script). The pipeline vocabulary
recognises the gold guild in 73 of the 102 first gold answers, the extended one in all 102.

The arguments are the benchmark, the runs file and an existing output folder. Only the last
valid answer per question and configuration is scored; failed requests are ignored.

To re-score the published runs, pass `results/traits_main/runs.jsonl` (or
`results/traits_repeat/runs.jsonl`) and an empty folder. This reproduces `summary.json`,
`scored.csv`, `scored_traits.csv` and `summary_traits.json` of both runs exactly.
`results/traits_main/runs.jsonl` also contains runs for questions of an earlier benchmark
version, which the scorers skip.

**Trait-level outcomes** (`score_traits.py`). Each answer is read the way the trait pipeline
would read it:

- body size: correct if a stated value in mm equals a gold value within 2 %;
- habitat: correct if the habitat classes found in the answer (13-class scheme of
  `trait_extraction_v3`) overlap those of the gold answer; an answer that names only a place is
  counted as "place only" (`geography`);
- trophic guild: correct if the guilds (Potapov et al. 2022 scheme) overlap the gold guilds;
- no answer: the answer states no usable value (for example "not mentioned").

Four habitat questions (K053, K203, K205, K225) are not scored because no habitat class could be
derived from their gold answer, so n = 122 per configuration. The outcomes refer to the first
answer of the Plazi collection in the response.

## Results

Main run (`results/traits_main/summary_traits.json`), all traits:

| Configuration | n | Correct % | Wrong % | No answer % | Place only % | Gold document retrieved % |
|---|--:|--:|--:|--:|--:|--:|
| `doc_extractive` | 122 | 61.5 | 3.3 | 18.0 | 17.2 | 100.0 |
| `doc_generative` | 122 | 49.2 | 4.1 | 44.3 | 2.5 | 100.0 |
| `e2e_sparse_extractive` | 122 | 39.3 | 24.6 | 31.1 | 4.9 | 60.7 |
| `e2e_sparse_generative` | 122 | 45.1 | 8.2 | 43.4 | 3.3 | 64.8 |
| `e2e_dense_generative` | 22 | 40.9 | 9.1 | 45.5 | 4.5 | 50.0 |

Correct answers by trait:

| Configuration | Body size: n | Body size: correct % | Habitat: n | Habitat: correct % |
|---|--:|--:|--:|--:|
| `doc_extractive` | 60 | 83.3 | 55 | 43.6 |
| `doc_generative` | 60 | 55.0 | 55 | 45.5 |
| `e2e_sparse_extractive` | 60 | 53.3 | 55 | 27.3 |
| `e2e_sparse_generative` | 60 | 58.3 | 55 | 32.7 |
| `e2e_dense_generative` | 14 | 64.3 | 7 | 0.0 |

Configurations: `doc_*` supply the gold treatment to the service (`doc_refs`), so the gold
document is always retrieved; `e2e_*` retrieve from the SIBiLS collections with sparse (BM25) or
dense retrieval. `*_extractive` use the extractive reader, `*_generative` the generative model.
"Gold document retrieved" means the gold treatment is among the Plazi documents returned.

- `e2e_dense_generative` returned an internal server error (an empty result) for most
  questions; only 24 of 126 questions received an answer (22 scorable), so its figures are not
  comparable with the other configurations.
- The seven trophic-guild questions are included in the "all" rows but too few to report
  separately; see `summary_traits.json`. Their gold guilds are set in `score_traits.py` and are
  still to be confirmed [TBC].
- Repeat run (`results/traits_repeat/`), correct %: `doc_extractive` 61.5 (n = 122),
  `doc_generative` 50.0 (n = 122), `e2e_sparse_extractive` 39.3 (n = 122),
  `e2e_sparse_generative` 44.3 (n = 122), `e2e_dense_generative` 36.4 (n = 22).
- String metrics (exact match, F1, ROUGE-L and others) are in `summary.json` in each results
  folder.

### Trophic-guild benchmark results

Run of 29 September 2026 (`results/trophic/summary_trophic.json`); 22 of the 102
`e2e_dense_generative` requests returned the server error, so that row has n = 80.

| Configuration | n | Food named % | Guild of the answer % | Wrong guild % | Guild recorded by the pipeline % | Gold document retrieved % |
|---|--:|--:|--:|--:|--:|--:|
| `doc_extractive` | 102 | 66 | 77 | 4 | – | 100 |
| `doc_generative` | 102 | 69 | 85 | 6 | 61 | 100 |
| `e2e_sparse_extractive` | 102 | 16 | 31 | 8 | – | 55 |
| `e2e_sparse_generative` | 102 | 44 | 88 | 8 | 73 | 55 |
| `e2e_dense_generative` | 80 | 41 | 88 | 5 | 71 | 48 |

- *Food named*: a gold food item appears verbatim in the answer (strict).
- *Guild of the answer*: guilds the answer states, read sentence by sentence with the extended
  vocabulary; end-to-end answers are scored against all gold guilds of the taxon.
- *Guild recorded by the pipeline*: `trait_extraction_v3` primary guild (species) or the genus
  classifier of `collembola_trophic_batch.py` (genera); generative configurations only, since the
  pipeline runs in generative mode.
- Most springtails are fungivores: a constant answer "fungi" scores 63 % (per-question gold guilds)
  and 75 % (taxon gold guilds) on guild. On the questions whose gold guilds include no fungal
  feeding, the generative answer is right in 82 % (`doc_generative`, n = 38) and 81 %
  (`e2e_sparse_generative`, n = 26).

## Licences

- Code (`scripts/` and the Python files in `data/curation/`): MIT, see [LICENSE](LICENSE).
- Data and results (`data/`, `results/`, `spotcheck/`): CC BY 4.0, see [LICENSE-DATA](LICENSE-DATA).
  Text excerpts quoted from treatments and articles remain subject to their original terms.
- `trait_extraction_v3.py` is not part of this repository; its licence is not stated upstream.

## Citation

Please cite this repository using the metadata in [CITATION.cff](CITATION.cff).
Zenodo DOI: [TBC].

## Acknowledgements

KYBELE is funded by ELIXIR. The question-answering service, the SIBiLS collections and the
BioMoQA-RAG code are provided by SIB Swiss Institute of Bioinformatics. Taxonomic treatments are
from Plazi TreatmentBank.
