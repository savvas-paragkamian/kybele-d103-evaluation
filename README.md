# KYBELE D10.3 evaluation: Collembola trait question answering

This repository publishes the scripts, benchmark and results of deliverable D10.3 of KYBELE
(Knowledge Yield from BiodivΕrsity Literature through LLM Extraction), an ELIXIR-funded project
(January–December 2026; ELIXIR Greece, Italy and Switzerland; leads Stelios Ninidakis,
HCMR / ELIXIR Greece, and Patrick Ruch, SIB / HES-SO, ELIXIR Switzerland). D10.3 is titled
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
| `data/curation/trophic/` | Curation decisions and review sheets for the trophic-guild benchmark (work in progress) |
| `scripts/kybele_d103_eval.py` | QA runner: sends the questions to the QA API in five configurations |
| `scripts/bench_to_candidates.py` | Converts `benchmark_traits.csv` into the runner's input file |
| `scripts/score.py` | String metrics (exact match, answer contains, SQuAD F1, ROUGE-L, faithfulness proxy, gold retrieval) |
| `scripts/score_traits.py` | Trait-level scoring (correct / wrong / no answer); needs `trait_extraction_v3.py`, see below |
| `scripts/kybele_trophic_harvest.py` | Harvests candidate diet statements from SIBiLS (Medline, PMC, Plazi) for the trophic-guild benchmark |
| `scripts/make_spotcheck.py` | Draws the specialist spot-check sample and writes the reviewer workbook (needs `openpyxl`) |
| `spotcheck/` | Spot-check sample (25 questions) and reviewer workbook |
| `results/traits_main/` | Main run: raw responses (`runs.jsonl`), log, `scored.csv`, `summary.json`, `scored_traits.csv`, `summary_traits.json` |
| `results/traits_repeat/` | Repeat run of the same 126 questions, same files |
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

A separate trophic-guild benchmark (diet statements for springtail species from Medline, PMC and
Plazi, harvested with `scripts/kybele_trophic_harvest.py`) is being finalised, with a target of
more than 100 questions. It will be added as `data/benchmark_trophic.csv`. The curation decisions
and review sheets so far are in `data/curation/trophic/`.

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

The arguments are the benchmark, the runs file and an existing output folder. Only the last
valid answer per question and configuration is scored; failed requests are ignored.

To re-score the published runs, pass `results/traits_main/runs.jsonl` (or
`results/traits_repeat/runs.jsonl`) and an empty folder. This reproduces `summary.json`,
`scored.csv` and `summary_traits.json` of both runs exactly. `results/traits_main/scored_traits.csv`
was written by an earlier version of `score_traits.py` and lacks the `plazi_food` and
`top_food` columns; all other values are identical. `results/traits_main/runs.jsonl` also
contains runs for questions of an earlier benchmark version, which the scorers skip.

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
