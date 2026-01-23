# ScrapeTestSNA - Project Organization

This repository has been organized into a clear directory structure for better maintainability.

## Directory Structure

### `data/`
All datasets and data files are organized here:
- **`data/periods/`** - Time-period specific datasets (pre_crimea.csv, post_crimea.csv, covid.csv, war.csv, final_nodes.csv)
- **`data/processed/`** - Processed and cleaned datasets (CSV, XLSX, JSON files)
- **`data/raw/`** - Raw Excel files and original data sources

### `scripts/`
All Python scripts organized by function:
- **`scripts/analysis/`** - Network analysis, clustering, and ML scripts
- **`scripts/data_processing/`** - Data cleaning, merging, NER processing scripts
- **`scripts/visualization/`** - Scripts for generating visualizations
- **`scripts/scraping/`** - Web scraping scripts and related tools
- **`scripts/old_technique/`** - Legacy scripts from previous approaches

### `outputs/`
All generated outputs:
- **`outputs/html/`** - Interactive HTML visualizations and dashboards
- **`outputs/visualizations/`** - PNG, PDF visualizations and related CSV data
- **`outputs/assets/`** - Image assets used in visualizations

### `docs/`
Documentation, papers, and reports:
- Markdown documentation files
- PDF papers and reports
- LaTeX files for academic writing
- Text files with extracted content

## Notes

- **All datasets have been preserved** - no data files were deleted during organization
- Only system files (.DS_Store) and temporary log files were removed
- The `deliverables/` directory structure has been integrated into the main organization

## Quick Access

- **Main datasets**: `data/periods/` and `data/processed/`
- **Analysis scripts**: `scripts/analysis/`
- **Visualizations**: `outputs/visualizations/`
- **Interactive dashboards**: `outputs/html/`
