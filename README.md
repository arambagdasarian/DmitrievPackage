# Dmitriev Network — Repository Overview

**Paper:** *Brokered Global Engagement Through Patronal Repurposing. Evolution and Structure of Russia's Adaptation Networks*  
Sebastian Hoppe, Anna Filippova, Aram Bagdasarian — *Environment and Planning A*, April 2026

---

## Quick Start (for the supervisor)

The `dmitriev_package/` folder contains a self-contained bundle of all relevant materials — data CSVs, visualization scripts, and final figures — along with its own `README.md` that explains how to reproduce the full analysis.

**Start there:** [`dmitriev_package/README.md`](dmitriev_package/README.md)

---

## Repository Structure

```
ScrapeTestSNA/
├── dmitriev_package/          ← DELIVERABLE: self-contained package for sharing
│   ├── README.md              ← step-by-step guide to reproduce the analysis
│   ├── data/                  ← period CSVs + node attribute sheet
│   ├── scripts/               ← final visualization and analysis scripts
│   └── final_visuals/         ← all paper-ready PNG figures + summary CSVs
│
├── data/
│   ├── periods/               ← source period edge lists and node files
│   │   ├── pre_crimea.csv
│   │   ├── post_crimea.csv
│   │   ├── covid.csv
│   │   ├── war.csv
│   │   ├── final_nodes_edges.csv
│   │   └── Dmitriev_Node_Sheet.xlsx
│   ├── processed/             ← intermediate processed datasets
│   └── raw/                   ← raw scraped articles and NER outputs
│
├── scripts/
│   ├── visualization/         ← all visualization scripts
│   │   ├── 1_statization_of_network.py
│   │   ├── 2_sectoral_repurposing.py
│   │   ├── 3_personalization_individual_brokers.py
│   │   ├── 4_network_consolidation_ratio.py
│   │   ├── 6_finance_sector_statization.py
│   │   ├── 7_network_size_evolution.py
│   │   ├── 8_network_density_across_periods.py
│   │   ├── 9_evolution_of_community_types.py
│   │   ├── louvain_community_networks.py
│   │   ├── louvain_semantic_community_series.py
│   │   ├── top50_network_graphs.py
│   │   ├── top50_nonrus_tables.py
│   │   ├── top_actors_tables.py
│   │   ├── network_change_analysis.py
│   │   ├── network_evolution_no_labels.py
│   │   ├── jurisdiction_evolution_no_russia.py
│   │   ├── sector_evolution_visualizations.py
│   │   ├── create_conceptual_core_structure.py
│   │   ├── run_all_final_visuals.py  ← runs all scripts above
│   │   └── date_utils.py
│   ├── analysis/
│   │   └── robustness_check_two_outlets.py
│   ├── data_processing/       ← NER cleaning and node construction pipeline
│   └── scraping/              ← INTEGRUM scraping setup (ChromeDriver)
│
├── final visuals/             ← all paper-ready output figures (PNG + PDF) + CSVs
│
└── docs/                      ← supplementary paper materials and LaTeX tables
```

---

## Analysis Pipeline

### Stage 1 — Data Acquisition (`scripts/scraping/`)

The INTEGRUM database was queried for **"Кирилл Дмитриев"** (Kirill Dmitriev), returning over 40,000 Russian-language articles published between 2010 and 2025. Scraping used Selenium + ChromeDriver.

### Stage 2 — NER & Cleaning (`scripts/data_processing/`)

Named Entity Recognition (spaCy, `ru_core_news_lg`) was applied to extract persons and organizations. After deduplication, fuzzy matching, and a **50-occurrence threshold**, ~18,000 raw candidates were reduced to approximately **1,000 nodes**. Four attributes were manually coded for each node: actor type, sector, jurisdiction, and state/private status.

Key scripts in order: `initialNER.py` → `harshcleanfinal.py` → `fuzzy.py` → `mergenodes.py` → `finalcountry.py` → `recreate_period_files.py`

### Stage 3 — Visualization (`scripts/visualization/`)

Run all figures at once:

```bash
cd scripts/visualization/
python run_all_final_visuals.py
```

Output goes to `final visuals/`.

---

## Period Definitions

| Period | Date Range | Analytical Focus |
|---|---|---|
| Pre-Crimea | 2010–2013 | Investment brokerage, Western integration |
| Post-Crimea | 2014–2019 | Sanctions adaptation, Gulf/BRICS pivot |
| COVID | 2020–2021 | Vaccine diplomacy, health politics |
| War | 2022–2025 | Wartime backchannel, energy reorientation |

---

## Data Format

Each period CSV (`pre_crimea.csv`, `post_crimea.csv`, `covid.csv`, `war.csv`) has the structure:

| Column | Description |
|---|---|
| `Article_ID` | Unique article identifier |
| `Date` | Publication date |
| `Source` | Media outlet name |
| `Entity` | Entity name (Russian) |
| `Entity_Type` | `PER` (person) or `ORG` (organization) |
| `Occurrences` | Total occurrence count across full corpus |
| `Jurisdiction` | Country/region code |
| `Context_Text` | Article excerpt |
| `Sector` | Finance, Government, Energy, Diplomacy, etc. |
| `State/Private` | State-linked or Private |
| `Actor Type` | Individual, Governmental Body, Fund, Bank, etc. |

Co-occurrence edges are constructed by grouping rows by `Article_ID` — any two entities sharing an article are connected, with edge weight = number of shared articles.

---

## Dependencies

```bash
pip install pandas networkx python-louvain matplotlib seaborn openpyxl
```
