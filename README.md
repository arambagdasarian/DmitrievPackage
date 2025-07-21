Dmitriev Network Mapping Project
This repository contains the codebase and ongoing development work for a complex data science research initiative on the social, political, and financial networks surrounding Kirill Dmitriev, the head of Russia’s sovereign wealth fund. The project is being conducted under the auspices of the Centre for East European and International Studies (ZOiS), where I serve as a Data Science Research Assistant. I am also the Principal Investigator on the forthcoming publication, authored by Dr. Sebastian Hoppe, expected for release in Winter 2025.

Project Overview
This project uses graph-theoretic techniques, fuzzy data cleaning, named entity recognition (NER), and large-scale web scraping to map the multilevel affiliations, influence pathways, and structural patterns of the elite networks in which Dmitriev operates. The goal is to understand the architecture of post-Soviet elite brokerage, particularly within the context of Russian state capitalism and international finance.

The research builds on and contributes to social network analysis (SNA) literature through its use of custom-built tools to extract and clean entity-level data from Russian-language media sources, using proprietary datasets such as Integrum, along with public financial disclosures, organizational rosters, and legal documents.

Key Features
1. Fuzzy Matching and Entity Cleaning
Implements Levenshtein-based and embedding-based fuzzy matching algorithms to reconcile variations in names and organizational titles across thousands of entries.

Standardizes transliterated Russian names and resolves ambiguities across datasets.

Deduplicates named entities across time periods using both statistical and linguistic heuristics.

2. Named Entity Recognition and Labeling
Applies rule-based and model-based NER techniques to extract persons, organizations, and geo-political entities.

Custom post-processing pipeline developed to resolve co-reference issues and identify aliases and abbreviations in Russian-language contexts.

3. Web Scraping & Source Aggregation
Automated scraping modules gather data from Integrum, Kommersant, RBC, and other relevant Russian news sources.

Dynamic content handling (e.g., JavaScript-rendered sites) is facilitated via Selenium-based scraping, with rate-limiting and session rotation to avoid blocking.

4. Graph Construction & Theoretical Modeling
Graphs are constructed over defined temporal windows to capture network evolution.

Employs:
- Degree centrality, betweenness, and eigenvector centrality
- K-core decomposition
- Community detection algorithms (Louvain, Leiden)
- Brokerage metrics, including constraint scores and layer transition frequencies
- Nodes and edges are weighted based on frequency, type of interaction, and co-occurrence strength.

5. 3D Visualization (In Progress)
Interactive 3D network visualizations are being developed using Plotly and Three.js for web deployment.
- Visualization modules are tailored to:
- Highlight role-based distinctions (e.g., political vs. financial actors)
- Animate network growth across time slices
- Export embeddable and shareable visual content for academic publication

Status
This project is currently in the advanced development and validation stage. A full paper, authored by Dr. Sebastian Hoppe (with myself as PI), is slated for submission in Winter 2025. Code components are continually updated as data pipelines are refined and additional graph metrics are introduced.

Requirements
Python 3.7+
pandas, numpy
scikit-learn
fuzzywuzzy
spaCy (with Russian models)
networkx
plotly
selenium
beautifulsoup4


Citation
Pending publication of the paper, please contact aram.bagdasarian@zois.de or sebastian.hoppe@zois.de for citation guidance or pre-publication collaboration inquiries.