# Dmitriev Network Analysis — Supervisor Package

**Paper:** *Brokered Global Engagement Through Patronal Repurposing. Evolution and Structure of Russia's Adaptation Networks*  
Sebastian Hoppe, Anna Filippova, Aram Bagdasarian (April 2026)

This folder contains all materials needed to understand and reproduce the quantitative network analysis underlying the paper.

---

## What Is This Project?

The paper constructs a **co-occurrence network** around Kirill Dmitriev (CEO of the Russian Direct Investment Fund, RDIF) using over 40,000 Russian-language media articles from the INTEGRUM database (2010–2025). Each node is an individual, firm, or institution appearing in the same articles as Dmitriev. The dataset is sliced into four periods reflecting major geopolitical shocks:

| Period | Years | Context |
|---|---|---|
| Pre-Crimea | 2010–2013 | RDIF as investment-attracting sovereign wealth fund |
| Post-Crimea | 2014–2019 | Sanctions consolidation, pivot to non-Western partners |
| COVID | 2020–2021 | Vaccine diplomacy (Sputnik V), pandemic health politics |
| War | 2022–2025 | Full-scale invasion, wartime backchannel diplomacy |

---

## Folder Contents

```
dmitriev_package/
├── README.md                        ← this file
├── data/
│   ├── pre_crimea.csv               ← entity-article table, Pre-Crimea period
│   ├── post_crimea.csv              ← entity-article table, Post-Crimea period
│   ├── covid.csv                    ← entity-article table, COVID period
│   ├── war.csv                      ← entity-article table, War period
│   ├── final_nodes_edges.csv        ← combined table (all periods)
│   └── Dmitriev_Node_Sheet.xlsx     ← node attributes (~1,000 nodes)
│                                       columns: name, actor_type, sector,
│                                       jurisdiction, state_private
├── scripts/
│   ├── run_all_final_visuals.py     ← entry point: runs all scripts below
│   ├── date_utils.py                ← shared period date utilities
│   │
│   ├── 1_statization_of_network.py
│   ├── 2_sectoral_repurposing.py
│   ├── 3_personalization_individual_brokers.py
│   ├── 4_network_consolidation_ratio.py
│   ├── 6_finance_sector_statization.py
│   ├── 7_network_size_evolution.py
│   ├── 8_network_density_across_periods.py
│   ├── 9_evolution_of_community_types.py
│   ├── louvain_community_networks.py
│   ├── louvain_semantic_community_series.py
│   ├── top50_network_graphs.py
│   ├── top50_nonrus_tables.py
│   ├── top_actors_tables.py
│   ├── network_change_analysis.py
│   ├── network_evolution_no_labels.py
│   ├── jurisdiction_evolution_no_russia.py
│   ├── sector_evolution_visualizations.py
│   ├── create_conceptual_core_structure.py
│   └── robustness_check_two_outlets.py
└── final_visuals/
        All paper-ready figures (PNG) and supporting summary CSVs
```

---

## Data Format

### Period CSVs (e.g. `pre_crimea.csv`)

Each row is one entity's appearance in one article:

| Column | Description |
|---|---|
| `Article_ID` | Unique article identifier |
| `Date` | Publication date |
| `Source` | Media outlet |
| `Entity` | Entity name (Russian) |
| `Entity_Type` | `PER` (person) or `ORG` (organization) |
| `Occurrences` | Total article-count in full corpus |
| `Jurisdiction` | Country/region code |
| `Context_Text` | Article excerpt |
| `Sector` | Finance, Government, Energy, Diplomacy, etc. |
| `State/Private` | State-linked or Private |
| `Actor Type` | Individual, Fund, Bank, Governmental Body, etc. |

**To build a co-occurrence edge list:** group by `Article_ID`, then create an edge between every pair of entities sharing an article. Edge weight = number of shared articles.

### Node Sheet (`Dmitriev_Node_Sheet.xlsx`)

One row per node in the ~1,000-node network, with manually coded attributes: actor type, sector, jurisdiction, and state/private status.

---

## Reproducing the Figures

### Install dependencies

```bash
pip install pandas networkx python-louvain matplotlib seaborn openpyxl
```

### Run all visualization scripts

```bash
cd scripts/
python run_all_final_visuals.py
```

This regenerates all figures and saves them to `final_visuals/`. Individual scripts can be run separately (e.g. `python 1_statization_of_network.py`).

---

## Key Findings

- The **domestic core** (Putin, Medvedev, Russian state banks, RDIF) remained structurally stable across all four periods despite sanctions and geopolitical shocks
- **International partners** shifted: Western finance (Goldman Sachs, Blackstone) pre-Crimea → Gulf sovereign funds (Mubadala, PIF) post-Crimea → health-system actors during COVID → BRICS diplomats and energy brokers during the war
- **Louvain communities** reveal distinct thematic sub-networks that reconfigure around each geopolitical mission
- **Network density** increases over time, suggesting tighter coordination under mounting external pressure
- **Robustness check** confirms results hold when the two largest media outlets are excluded

---

## Contact

Aram Bagdasarian — Harvard University
