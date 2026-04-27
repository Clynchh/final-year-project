# COVID-19 Broadcast Media Sentiment Analysis

**Final Year Project - Corey Lynch (40363992)**  

An end-to-end NLP pipeline that scrapes, transcribes, filters, and analyses sentiment and emotion in BBC broadcast media across the COVID-19 pandemic (June 2016 – May 2023).

**Live results dashboard:** https://clynchh.github.io/final-year-project/

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Repository Structure](#2-repository-structure)
3. [Prerequisites](#3-prerequisites)
4. [Installation](#4-installation)
5. [Pre-Computed Results](#5-pre-computed-results)
6. [Quick Start for Assessors](#6-quick-start-for-assessors)
7. [Running the Pipeline](#7-running-the-pipeline)
   - [7.1 Full Pipeline via Orchestrator](#71-full-pipeline-via-orchestrator)
   - [7.2 Resuming from a Step](#72-resuming-from-a-step)
   - [7.3 Running Individual Steps](#73-running-individual-steps)
8. [Script Reference](#8-script-reference)
   - [8.1 Preprocessing](#81-preprocessing)
   - [8.2 Analysis](#82-analysis)
   - [8.3 Scraping](#83-scraping)
   - [8.4 Utilities](#84-utilities)
9. [Output Files](#9-output-files)
10. [Running the Tests](#10-running-the-tests)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Project Overview

This system analyses how sentiment and emotion in BBC broadcast media evolved across the COVID-19 pandemic. It covers six BBC sources across two genres (news and entertainment) and applies two sentiment models alongside a seven-class emotion classifier.

**Sources:** BBC News TV, BBC Radio 4, The Graham Norton Show, QI, The Last Leg, The One Show

**Pipeline stages:**

```
Scrape → Transcribe → Cleanse → Segment → Filter → Analyse → Summarise → Export
```

**Sentiment models:**
- **VADER** - lexicon-rule system, three-class output (positive / neutral / negative), no GPU required
- **RoBERTa (altmodel)** - `siebert/sentiment-roberta-large-english`, two-class transformer, GPU recommended

**Emotion model:**
- `j-hartmann/emotion-english-distilroberta-base` - seven classes: anger, disgust, fear, joy, neutral, sadness, surprise

---

## 2. Repository Structure

```
final-year-project/
├── run_pipeline.py              # Pipeline orchestrator
├── requirements.txt
├── README.md
│
├── data/
│   ├── raw/                     # Original transcripts (one .txt per source/period/year/month)
│   │   ├── bbc_news_tv/
│   │   ├── bbc_radio4/
│   │   ├── graham_norton/
│   │   ├── qi/
│   │   ├── the_last_leg/
│   │   └── the_one_show/
│   ├── clean/                   # After cleanse step
│   ├── segmented/               # After segment step (one sentence per line)
│   ├── filtered/
│   │   ├── tight/               # COVID-relevant sentences (tight filter)
│   │   └── loose/               # COVID-relevant sentences (loose filter)
│   └── sampled/                 # 2.9% random sample of segmented data
│
├── src/
│   ├── preprocessing/
│   │   ├── constants.py         # COVID term lists (DIRECT_TERMS, INDIRECT_TERMS)
│   │   ├── cleanse.py
│   │   ├── segment.py
│   │   ├── filter_relevant_tight.py
│   │   ├── filter_relevant_loose.py
│   │   ├── sample_sentences.py
│   │   └── filter_sample.py
│   ├── analysis/
│   │   ├── polarity_analysis.py # RoBERTa sentiment (altmodel)
│   │   ├── vader_analysis.py    # VADER sentiment
│   │   ├── emotion_analysis.py  # Emotion classification
│   │   ├── summary.py           # Monthly aggregation
│   │   ├── csv_to_json.py
│   │   ├── emotion_to_json.py
│   │   ├── generate_sentence_count.py
│   │   ├── sentence_count_to_json.py
│   │   └── sample_covid_count.py
│   ├── scraping/
│   │   ├── bob_scraper.py
│   │   ├── bob_audio_downloader.py
│   │   ├── bbc_sounds_downloader.py
│   │   ├── genome_downloader.py
│   │   ├── whisper_transcribe.py
│   │   └── bob_cite_citations.py
│   ├── misc/
│   │   ├── check_missing.py
│   │   └── countall.py
│   └── results/
│       ├── csv/                 # All output CSVs (pre-computed)
│       └── json/                # All output JSONs (pre-computed)
│
├── tests/
│   ├── preprocessing/
│   ├── analysis/
│   └── test_pipeline.py
│
└── docs/
    ├── FYP_Demo_Presentation.pptx
    └── 40363992_Lynch.odt
```

---

## 3. Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.12+ | Must match the virtual environment |
| pip | 23+ | Bundled with Python 3.12 |
| RAM | 8 GB minimum | 16 GB recommended for transformer models |
| Disk space | ~5 GB free | Models are downloaded on first run (~1.5 GB each) |
| GPU | Optional | CUDA GPU dramatically speeds up transformer steps; CPU works but is slow |
| Internet | Required on first run | To download spaCy and Hugging Face models |
| ffmpeg | Optional | Only needed for audio scraping/downloading |
| Chromium | Optional | Only needed for web scraping (`bob_scraper.py`); install via `playwright install chromium` |

 **Assessors:** You do not need a GPU. All pre-computed results already exist in `src/results/`.

---

## 4. Installation

### Step 1 - Clone or extract the repository

```bash
# HTTPS
git clone https://gitlab.eeecs.qub.ac.uk/40363992/fyp-covid-sentiment-analysis.git

# SSH
git clone git@gitlab.eeecs.qub.ac.uk:40363992/fyp-covid-sentiment-analysis.git

cd fyp-covid-sentiment-analysis
```

Or extract the submitted zip:

```bash
unzip 40363992_Lynch_FYP.zip
cd final-year-project
```

### Step 2 - Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows
```

### Step 3 - Install Python dependencies

```bash
pip install -r requirements.txt
```

This installs: `torch`, `transformers`, `spacy`, `vaderSentiment`, `playwright`, `openai-whisper`, `requests`, `beautifulsoup4`, `pytest`, `pytest-cov`.

> **Note:** PyTorch is a large package (~2 GB). On a slow connection this step may take several minutes.

### Step 4 - Download the spaCy language model

```bash
python3 -m spacy download en_core_web_sm
```

This model is required by the sentence segmentation step.

### Step 5 - (Optional) Install Playwright browser

Only needed if you intend to re-run the web scrapers. Skip this for analysis and demo purposes.

```bash
playwright install chromium
```

### Step 6 - Verify the installation

```bash
python3 -c "import torch, transformers, spacy, vaderSentiment; print('All dependencies OK')"
python3 -m spacy info
```

> **Hugging Face transformer models** (`siebert/sentiment-roberta-large-english` and `j-hartmann/emotion-english-distilroberta-base`) are downloaded automatically on first use of `polarity_analysis.py` or `emotion_analysis.py`. They are cached in `~/.cache/huggingface/` and do not need to be downloaded again on subsequent runs.

---

## 5. Pre-Computed Results

**All results have already been computed and are included in the repository.** You do not need to re-run any analysis to view, inspect, or work with the findings.

### CSV results (`src/results/csv/`)

| File | Description |
|------|-------------|
| `sentiment_analysis_details_tight_vader.csv` | Per-sentence VADER sentiment - tight filter |
| `sentiment_analysis_details_tight_altmodel.csv` | Per-sentence RoBERTa sentiment - tight filter |
| `sentiment_analysis_details_loose_vader.csv` | Per-sentence VADER sentiment - loose filter |
| `sentiment_analysis_details_loose_altmodel.csv` | Per-sentence RoBERTa sentiment - loose filter |
| `sentiment_analysis_details_sample_vader.csv` | Per-sentence VADER sentiment - sample filter |
| `sentiment_analysis_details_sample_altmodel.csv` | Per-sentence RoBERTa sentiment - sample filter |
| `sentiment_analysis_monthly_tight_vader.csv` | Monthly aggregated VADER - tight filter |
| `sentiment_analysis_monthly_tight_altmodel.csv` | Monthly aggregated RoBERTa - tight filter |
| `sentiment_analysis_monthly_loose_vader.csv` | Monthly aggregated VADER - loose filter |
| `sentiment_analysis_monthly_loose_altmodel.csv` | Monthly aggregated RoBERTa - loose filter |
| `sentiment_analysis_monthly_sample_vader.csv` | Monthly aggregated VADER - sample filter |
| `sentiment_analysis_monthly_sample_altmodel.csv` | Monthly aggregated RoBERTa - sample filter |
| `emotion_analysis_details_tight.csv` | Per-sentence emotion - tight filter |
| `emotion_analysis_details_loose.csv` | Per-sentence emotion - loose filter |
| `emotion_analysis_details_sample.csv` | Per-sentence emotion - sample filter |
| `emotion_analysis_monthly_tight.csv` | Monthly aggregated emotion - tight filter |
| `emotion_analysis_monthly_loose.csv` | Monthly aggregated emotion - loose filter |
| `emotion_analysis_monthly_sample.csv` | Monthly aggregated emotion - sample filter |
| `sentence_count.csv` | Total sentence count per month across all sources |
| `sample_covid_count.csv` | COVID mention frequency in sampled sentences |

### JSON results (`src/results/json/`)

JSON equivalents of all monthly summary CSVs, used by any visualisation layer.

### CSV column reference

**Sentiment monthly CSVs:**

| Column | Description |
|--------|-------------|
| `source` | Programme name (e.g. `bbc_news_tv`) |
| `period` | `control` or `covid` |
| `year_month` | `YYYY-MM` |
| `mean_sentiment` | Mean sentiment score (−1, 0, +1 for label-based) |
| `weighted_mean_sentiment` | Mean weighted by confidence |
| `median_sentiment` | Median sentiment score |
| `positive_pct` | % of sentences classified positive |
| `neutral_pct` | % classified neutral (VADER only; 0 for altmodel) |
| `negative_pct` | % classified negative |
| `sentence_count` | Number of sentences in that month |
| `covid_sentence_count` | COVID-relevant sentences (from tight filter dir) |
| `sentiment_std` | Standard deviation of scores |

**Emotion monthly CSVs:**

| Column | Description |
|--------|-------------|
| `source`, `period`, `year_month` | As above |
| `sentence_count` | Number of sentences classified |
| `anger_pct` … `surprise_pct` | Percentage of sentences classified as each emotion |

---

## 6. Quick Start for Assessors

These commands are designed to demonstrate the system in a few minutes without requiring any long-running processes. All commands assume you are in the project root with the virtual environment activated.

```bash
source venv/bin/activate
```

### Show the corpus

```bash
# What sources exist
ls data/raw/

# How many transcript files are in the corpus
find data/raw -name "*.txt" | wc -l

# View a raw transcript
head -30 "data/raw/bbc_news_tv/control/2019/Aug 2019.txt"

# View the same file after sentence segmentation
head -30 "data/segmented/bbc_news_tv/control/2019/Aug 2019.txt"

# View what the tight filter kept from the March 2020 lockdown month
cat "data/filtered/tight/bbc_news_tv/covid/2020/Mar 2020.txt"
```

### Demonstrate the COVID filter logic live

```bash
python3 -c "
import re, sys
sys.path.insert(0, 'src/preprocessing')
from constants import DIRECT_TERMS, INDIRECT_TERMS

DIRECT = re.compile(r'\b(' + '|'.join(re.escape(t) for t in DIRECT_TERMS) + r')\b', re.I)
INDIRECT = re.compile(r'\b(' + '|'.join(re.escape(t) for t in INDIRECT_TERMS) + r')\b', re.I)

tests = [
    'The prime minister held a press conference today.',
    'Coronavirus cases reached record levels across the UK.',
    'Hospitals faced severe pressure as the pandemic spread.',
    'The new vaccine showed strong immunity in clinical trials.',
    'Schools moved to remote learning as the lockdown began.',
]
print('Tight filter results:')
for s in tests:
    result = bool(DIRECT.search(s)) or len(INDIRECT.findall(s)) >= 2
    print(f'  [{\"PASS\" if result else \"FAIL\"}] {s}')
"
```

### Check corpus integrity

```bash
python3 src/misc/check_missing.py
```

### Run VADER sentiment analysis on the sample dataset (fast - ~2 seconds)

```bash
python3 src/analysis/vader_analysis.py --filter sample
```

### Aggregate and export to JSON

```bash
python3 src/analysis/summary.py --filter sample --model vader
python3 src/analysis/csv_to_json.py --filter sample --model vader
```

### Inspect key findings from pre-computed results

```bash
# Peak COVID coverage months (March–May 2020)
grep "bbc_news_tv,covid,2020-0[3-5]" src/results/csv/sentiment_analysis_monthly_tight_vader.csv

# Vaccine rollout (Jan 2021) - VADER vs altmodel divergence
grep "bbc_news_tv,covid,2021-01" src/results/csv/sentiment_analysis_monthly_tight_vader.csv
grep "bbc_news_tv,covid,2021-01" src/results/csv/sentiment_analysis_monthly_tight_altmodel.csv

# Emotion at the height of first lockdown (March 2020)
grep "bbc_news_tv,covid,2020-03" src/results/csv/emotion_analysis_monthly_tight.csv

# Delta variant fear peak (June 2021)
grep "bbc_news_tv,covid,2021-06" src/results/csv/emotion_analysis_monthly_tight.csv

# COVID mention rate dropping to zero in late 2022 (return to baseline)
grep "bbc_news_tv,covid,2022-06\|bbc_news_tv,covid,2022-09\|bbc_news_tv,covid,2022-11" src/results/csv/sample_covid_count.csv
```

### Show the pipeline help

```bash
python3 run_pipeline.py --help
```

---

## 7. Running the Pipeline

> **Important:** The full pipeline (from raw transcripts to final results) takes several hours on CPU because it must load and run two large transformer models over thousands of sentences. **Assessors should not need to re-run the full pipeline** - all results are pre-computed. This section documents how to do so if required.

### 7.1 Full Pipeline via Orchestrator

```bash
python3 run_pipeline.py [--filter {tight|loose|sample}] [--model {altmodel|vader}]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--filter` | `tight` | Which COVID filter to use for the analysis steps |
| `--model` | `altmodel` | Sentiment model: `altmodel` (RoBERTa) or `vader` |

**Examples:**

```bash
# Default: tight filter, RoBERTa model
python3 run_pipeline.py

# VADER model (much faster - no GPU needed)
python3 run_pipeline.py --model vader

# Loose filter with RoBERTa
python3 run_pipeline.py --filter loose

# Loose filter with VADER (fastest full run)
python3 run_pipeline.py --filter loose --model vader
```

The pipeline executes these steps in order:

```
cleanse → segment → filter (tight + loose) → sample → filter_sample
→ sentiment → emotion → summary → convert
```

### 7.2 Resuming from a Step

If a run was interrupted, or you only want to re-run from a specific point:

```bash
python3 run_pipeline.py --from <step> [--filter <type>] [--model <name>]
```

Valid step names: `cleanse`, `segment`, `filter`, `sample`, `filter_sample`, `sentiment`, `emotion`, `summary`, `convert`

**Examples:**

```bash
# Re-run only the JSON conversion (instant - reads existing CSVs)
python3 run_pipeline.py --from convert --filter tight --model vader

# Re-run from sentiment analysis onwards
python3 run_pipeline.py --from sentiment --filter tight --model vader

# Re-run summary and convert only
python3 run_pipeline.py --from summary --filter loose --model altmodel
```

### 7.3 Running Individual Steps

Each script in `src/preprocessing/` and `src/analysis/` can be run independently.

---

## 8. Script Reference

All scripts must be run with the virtual environment active. Scripts in `src/preprocessing/` that import from `constants.py` must either be run from within `src/preprocessing/` or invoked via `run_pipeline.py` (which handles the path correctly).

### 8.1 Preprocessing

#### `src/preprocessing/cleanse.py`

Removes subtitle artefacts, resolves overlapping lines, and normalises text in raw transcripts.

```bash
python3 src/preprocessing/cleanse.py
```

- Input: `data/raw/**/*.txt`
- Output: `data/clean/**/*.txt`
- No arguments.

---

#### `src/preprocessing/segment.py`

Splits cleaned text into one sentence per line using spaCy (`en_core_web_sm`).

```bash
python3 src/preprocessing/segment.py
```

- Input: `data/clean/**/*.txt`
- Output: `data/segmented/**/*.txt`
- No arguments.
- Requires spaCy model: `python3 -m spacy download en_core_web_sm`

---

#### `src/preprocessing/filter_relevant_tight.py`

Keeps only sentences that contain at least one direct COVID term **or** two or more indirect COVID terms.

**Direct terms (one match sufficient):** `covid`, `covid-19`, `coronavirus`, `sars-cov-2`

**Indirect terms (two or more matches required):** `pandemic`, `lockdown`, `vaccine`, `variant`, `PCR`, `lateral flow`, `furlough`, `shielding`, `NHS`, `hospitalisations`, and ~50 others (see `src/preprocessing/constants.py` for the full list).

```bash
python3 src/preprocessing/filter_relevant_tight.py
```

- Input: `data/segmented/**/*.txt`
- Output: `data/filtered/tight/**/*.txt`
- No arguments.

---

#### `src/preprocessing/filter_relevant_loose.py`

Keeps sentences containing any single COVID-lexicon term (union of direct and indirect lists).

```bash
python3 src/preprocessing/filter_relevant_loose.py
```

- Input: `data/segmented/**/*.txt`
- Output: `data/filtered/loose/**/*.txt`
- No arguments.

---

#### `src/preprocessing/sample_sentences.py`

Draws a proportional random sample (2.9%) from the segmented data for baseline COVID-frequency estimation.

```bash
python3 src/preprocessing/sample_sentences.py [--seed SEED]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `--seed` | `20` | Random seed for reproducibility |

- Input: `data/segmented/**/*.txt`
- Output: `data/sampled/**/*.txt`

---

#### `src/preprocessing/filter_sample.py`

Applies the tight COVID filter to the sampled sentences.

```bash
python3 src/preprocessing/filter_sample.py
```

- Input: `data/sampled/**/*.txt`
- Output: `data/filtered/sample/**/*.txt`
- No arguments.

---

### 8.2 Analysis

#### `src/analysis/vader_analysis.py`

Sentiment analysis using the VADER lexicon. Fast - no model download or GPU required. Produces three-class output (positive / neutral / negative).

```bash
python3 src/analysis/vader_analysis.py [--filter {tight|loose|sample}]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `--filter` | `tight` | Which filtered dataset to analyse |

- Input: `data/filtered/<filter>/` (or `data/sampled/` when `--filter sample`)
- Output: `src/results/csv/sentiment_analysis_details_<filter>_vader.csv`

**Expected runtime:** Under 5 seconds for `--filter sample` (138 sentences). A few minutes for `tight` or `loose` over the full corpus.

---

#### `src/analysis/polarity_analysis.py`

Sentiment analysis using `siebert/sentiment-roberta-large-english` (RoBERTa). Produces two-class output (positive / negative - no neutral class). Downloads the model (~1.5 GB) on first run.

```bash
python3 src/analysis/polarity_analysis.py [--filter {tight|loose|sample}]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `--filter` | `tight` | Which filtered dataset to analyse |

- Input: `data/filtered/<filter>/`
- Output: `src/results/csv/sentiment_analysis_details_<filter>_altmodel.csv`

**Expected runtime:** Several hours on CPU over the full tight dataset. A GPU reduces this to tens of minutes.

> **Note:** The model is automatically downloaded from Hugging Face on first run and cached in `~/.cache/huggingface/`. Subsequent runs use the cache and do not require internet access.

---

#### `src/analysis/emotion_analysis.py`

Emotion classification using `j-hartmann/emotion-english-distilroberta-base`. Classifies each sentence into one of seven emotions: anger, disgust, fear, joy, neutral, sadness, surprise.

```bash
python3 src/analysis/emotion_analysis.py [--filter {tight|loose|sample}]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `--filter` | `tight` | Which filtered dataset to analyse |

- Input: `data/filtered/<filter>/`
- Output: `src/results/csv/emotion_analysis_details_<filter>.csv`

**Expected runtime:** Similar to `polarity_analysis.py`. Several hours on CPU, significantly faster with GPU.

---

#### `src/analysis/summary.py`

Aggregates per-sentence sentiment and emotion CSVs into monthly summary statistics (mean, median, standard deviation, percentage distributions).

```bash
python3 src/analysis/summary.py [--filter {tight|loose|sample}] [--model {altmodel|vader}]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `--filter` | `tight` | Which result set to summarise |
| `--model` | `altmodel` | Which sentiment model's results to summarise |

- Input: `src/results/csv/sentiment_analysis_details_<filter>_<model>.csv` and `src/results/csv/emotion_analysis_details_<filter>.csv`
- Output: `src/results/csv/sentiment_analysis_monthly_<filter>_<model>.csv` and `src/results/csv/emotion_analysis_monthly_<filter>.csv`

**Expected runtime:** Seconds.

---

#### `src/analysis/csv_to_json.py`

Converts a sentiment monthly summary CSV to JSON format.

```bash
python3 src/analysis/csv_to_json.py [--filter {tight|loose|sample}] [--model {altmodel|vader}]
```

- Output: `src/results/json/sentiment_data_<filter>_<model>.json`
- **Expected runtime:** Instant.

---

#### `src/analysis/emotion_to_json.py`

Converts an emotion monthly summary CSV to JSON format.

```bash
python3 src/analysis/emotion_to_json.py [--filter {tight|loose|sample}]
```

- Output: `src/results/json/emotion_data_<filter>.json`
- **Expected runtime:** Instant.

---

#### `src/analysis/generate_sentence_count.py`

Counts total sentences per month across all sources and writes `sentence_count.csv`.

```bash
python3 src/analysis/generate_sentence_count.py
```

- Input: `data/segmented/**/*.txt`
- Output: `src/results/csv/sentence_count.csv`
- **Expected runtime:** A few seconds.

---

#### `src/analysis/sentence_count_to_json.py`

Converts `sentence_count.csv` to JSON.

```bash
python3 src/analysis/sentence_count_to_json.py
```

- Output: `src/results/json/sentence_count.json`
- **Expected runtime:** Instant.

---

#### `src/analysis/sample_covid_count.py`

Counts how many sentences in the sampled data match the COVID filter, per source and month. Used to estimate the baseline COVID mention rate in the control period.

```bash
python3 src/analysis/sample_covid_count.py
```

- Input: `data/filtered/sample/`
- Output: `src/results/csv/sample_covid_count.csv` and `src/results/json/sample_covid_count.json`
- **Expected runtime:** Seconds.

---

### 8.3 Scraping

> **You do not need to run these scripts.** All raw transcripts are already included in `data/raw/` and all results are pre-computed in `src/results/`. The scripts below are documented for reproducibility only. Re-running them requires institutional access to the Box of Broadcasts (BoB) archive via a university login, which is not available to external users.

#### `src/scraping/bob_scraper.py`

Scrapes BBC News TV transcripts from BoB using Playwright browser automation.

```bash
python3 src/scraping/bob_scraper.py --period {covid|control} [OPTIONS]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `--period` | *(required)* | `covid` or `control` |
| `--source` | `bbc_news_tv` | Output directory name under `data/raw/` |
| `--search` | `"BBC News"` | Search term used on BoB |
| `--title-filter` | *(none)* | Only accept results containing this string in the title |
| `--min-duration` | `120` | Minimum episode duration in minutes |
| `--only YYYY-MM` | *(none)* | Scrape a single month only |
| `--from YYYY-MM` | *(none)* | Skip all months before this date |
| `--overwrite` | `False` | Re-scrape already-downloaded months |
| `--title-only` | `False` | Use title-field search only (more precise) |
| `--media-type` | `""` | Filter by media type: `""` (all), `"R"` (radio), `"T"` (TV) |
| `--debug` | `False` | Print page element info for selector debugging |

---

#### `src/scraping/bob_audio_downloader.py`

Downloads BBC Radio 4 audio from BoB using HLS stream interception and ffmpeg.

```bash
python3 src/scraping/bob_audio_downloader.py --period {covid|control} [OPTIONS]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `--period` | *(required)* | `covid` or `control` |
| `--source` | `bbc_radio4` | Output directory name under `data/raw/` |
| `--search` | `"Six O'Clock News"` | Programme title to search for |
| `--min-duration` | `30` | Minimum episode duration in minutes |
| `--only YYYY-MM` | *(none)* | Download a single month only |
| `--overwrite` | `False` | Re-download already-downloaded months |
| `--dry-run` | `False` | Find URLs but do not download |
| `--debug` | `False` | Print HLS request URLs and diagnostic info |

---

#### `src/scraping/whisper_transcribe.py`

Transcribes `.m4a` audio files using OpenAI Whisper.

```bash
python3 src/scraping/whisper_transcribe.py --source SOURCE --period {covid|control} [--model {tiny|base|small|medium|large}]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `--source` | *(required)* | Source name matching directory under `data/raw/` |
| `--period` | *(required)* | `covid` or `control` |
| `--model` | `base` | Whisper model size. Larger = more accurate but slower |

---

#### `src/scraping/genome_downloader.py`

Bulk-downloads BBC Sounds episodes via the BBC Genome API and DASH stream interception.

```bash
python3 src/scraping/genome_downloader.py --period {covid|control} [OPTIONS]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `--period` | *(required)* | `covid` or `control` |
| `--source` | `bbc_radio4` | Output directory name |
| `--programme` | `"six o'clock news"` | Programme name to search on Genome |
| `--service` | `bbc_radio_fourfm` | Genome service code |
| `--overwrite` | `False` | Re-download existing months |
| `--dry-run` | `False` | Find URLs but do not download |
| `--debug` | `False` | Print diagnostic output |

---

### 8.4 Utilities

#### `src/misc/check_missing.py`

Checks for missing or empty transcript files across all sources and periods, comparing against the expected monthly schedule.

```bash
python3 src/misc/check_missing.py
```

- No arguments. Prints a report to stdout.
- **Expected runtime:** Under 1 second.

---

#### `src/misc/countall.py`

Counts total lines of text across all segmented dataset files and prints a per-file breakdown.

```bash
python3 src/misc/countall.py
```

- No arguments.
- **Expected runtime:** A few seconds (reads all segmented files).

---

## 9. Output Files

### Sentiment score encoding

All models map their output to a numeric sentiment score:

| Label | Score |
|-------|-------|
| positive | +1 |
| neutral | 0 (VADER only) |
| negative | −1 |

Monthly mean sentiment therefore falls in [−1, +1]. Values near 0 indicate mixed or neutral coverage.

### Filter type comparison

| Filter | Sentences included | Use case |
|--------|-------------------|----------|
| `tight` | Direct COVID term present, OR 2+ indirect COVID terms | High-confidence COVID discourse - primary analysis |
| `loose` | Any single COVID-lexicon term present | Broader context - comparison |
| `sample` | 2.9% random sample of all sentences, then tight-filtered | COVID mention frequency baseline estimation |

### Source identifiers in output files

| `source` value | Programme |
|----------------|-----------|
| `bbc_news_tv` | BBC News TV |
| `bbc_radio4` | BBC Radio 4 (Six O'Clock News) |
| `graham_norton` | The Graham Norton Show |
| `qi` | QI |
| `the_last_leg` | The Last Leg |
| `the_one_show` | The One Show |

---

## 10. Running the Tests

The test suite covers preprocessing logic, analysis utilities, and the pipeline orchestrator. Tests use pytest and do not require the transformer models or the full dataset.

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=term-missing

# Run only preprocessing tests
pytest tests/preprocessing/ -v

# Run only analysis tests
pytest tests/analysis/ -v

# Run pipeline integration test
pytest tests/test_pipeline.py -v
```

> **Note:** Run pytest from the project root. The test suite is self-contained and uses temporary directories - it does not modify any files in `data/` or `src/results/`.

---

## 11. Troubleshooting

### `ModuleNotFoundError: No module named 'vaderSentiment'` (or any other module)

The virtual environment is not activated. Run:

```bash
source venv/bin/activate    # macOS / Linux
venv\Scripts\activate       # Windows
```

---

### `Can't find model 'en_core_web_sm'`

The spaCy model has not been downloaded. Run:

```bash
python3 -m spacy download en_core_web_sm
```

---

### `OSError: Can't load tokenizer for 'siebert/sentiment-roberta-large-english'`

The Hugging Face model is being downloaded for the first time and requires internet access. Ensure you are connected to the internet. The model is cached after the first download.

If you are on a restricted network, download the model manually:

```bash
python3 -c "from transformers import AutoTokenizer, AutoModelForSequenceClassification; \
  AutoTokenizer.from_pretrained('siebert/sentiment-roberta-large-english'); \
  AutoModelForSequenceClassification.from_pretrained('siebert/sentiment-roberta-large-english')"
```

---

### `RuntimeError: CUDA out of memory`

Reduce the batch size in `polarity_analysis.py` or `emotion_analysis.py` by editing the `BATCH_SIZE` constant at the top of each file:

```python
BATCH_SIZE = 4   # reduce from default of 8
```

---

### `FileNotFoundError` when running a preprocessing or analysis script directly

Some scripts resolve paths relative to the project root. Always run scripts from the project root directory:

```bash
cd /path/to/final-year-project
python3 src/analysis/vader_analysis.py --filter sample
```

---

### Scripts in `src/preprocessing/` fail with `ModuleNotFoundError: No module named 'constants'`

Run preprocessing scripts through the pipeline orchestrator rather than directly:

```bash
python3 run_pipeline.py --from filter
```

Or invoke them as a module:

```bash
python3 -m src.preprocessing.filter_relevant_tight
```

---

### `playwright._impl._errors.Error: Executable doesn't exist`

Playwright's Chromium browser is not installed. Install it with:

```bash
playwright install chromium
```

This is only required for the scraping scripts. It is not needed for analysis or demo purposes.

---

### Tests fail with import errors

Ensure you are running pytest from the project root and that the virtual environment is active:

```bash
source venv/bin/activate
pytest tests/ -v
```

---

*For any other issues, contact Corey Lynch, 40363992, clynch63@qub.ac.uk*
