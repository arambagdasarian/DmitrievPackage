# Separate Visualizations - One Graph Per File

This directory contains all visualizations generated from the refined dataset: **Dmitriev_Node_Sheet_092025_SH_AF_102025.xlsx**

## File Naming Convention

All files follow a consistent naming pattern:
- `{analysis_number}_{type}_{attribute}_{period}.png` for visualizations
- `{analysis_number}_{type}_{period}.csv` for data tables

## Analysis Breakdown

### Analysis 1: Composition Changes Over Periods

**Pie Charts (16 files):**
- `1_pie_Sector_{Period}.png` - Sector composition for each period
- `1_pie_State_Private_{Period}.png` - State/Private composition for each period
- `1_pie_Actor Type_{Period}.png` - Actor Type composition for each period
- `1_pie_Jurisdiction_{Period}.png` - Jurisdiction composition for each period

**Evolution Graphs (4 files):**
- `1_evolution_Sector.png` - Sector evolution across all periods
- `1_evolution_State_Private.png` - State/Private evolution
- `1_evolution_Actor Type.png` - Actor Type evolution
- `1_evolution_Jurisdiction.png` - Jurisdiction evolution

### Analysis 2: Top 50 vs Overall Comparison

**Comparison Charts (16 files):**
- `2_top50_comparison_{Attribute}_{Period}.png` - Side-by-side comparison of Top 50 vs Overall network for each attribute and period

### Analysis 3: Sector Composition and Institutional Repurposing

**Tables (1 file):**
- `3_sector_composition_table.csv` - Detailed sector breakdown comparing Overall, Top 20, and Top 50

**Comparison Charts (4 files):**
- `3_sector_comparison_{Period}.png` - Bar charts comparing sector composition across network levels

### Analysis 4: Clustering Trends

**Trend Charts (4 files):**
- `4_clustering_trend_{Attribute}.png` - Stacked area charts showing clustering trends across periods

### Analysis 5: Louvain Communities with Attributes

**Network Visualizations (16 files):**
- `5_louvain_{Attribute}_{Period}.png` - Louvain community networks colored by each attribute

**Composition Tables (4 files):**
- `5_louvain_composition_{Period}.csv` - Attribute composition statistics for each Louvain community

### Analysis 6: Attribute-Based Clustering

**Cluster Visualizations (16 files):**
- `6_attribute_cluster_{Attribute}_{Period}.png` - Networks colored by attributes showing attribute-based clusters (green edges = internal, gray = external)

**Metrics Table (1 file):**
- `6_attribute_clustering_metrics.csv` - Cohesion metrics for each attribute and period

## Total Files

- **PNG files:** ~76+ visualization files (one graph per file)
- **CSV files:** ~6+ data tables

## Usage

All visualizations are high-resolution (300 DPI) and ready for:
- Academic presentations
- Paper figures
- Reports
- Further analysis

Each file is self-contained and can be used independently.

## Data Source

All visualizations are based on:
- **Refined dataset:** Dmitriev_Node_Sheet_092025_SH_AF_102025.xlsx
- **Period CSV files:** pre_crimea.csv, post_crimea.csv, covid.csv, war.csv

The refined attributes (Sector, State/Private, Actor Type, Jurisdiction) from the Excel file have been merged with the period-specific CSV data.


