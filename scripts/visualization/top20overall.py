#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create LaTeX table with the 20 top actors across ALL periods combined,
ranked by a composite centrality score.

Fixes (2025‑07‑25):
- Use the **Occurrences** column directly without aggregating/summing.
- Betweenness & closeness computed on *inverse* edge weights so higher co‑occurrence ↔ stronger/shorter connection.
- Composite score now uses only **normalised** Edge Count (N_Edge); raw Edge Count is kept solely for display.

Author: Your Name
Date  : 2025‑07‑25
"""
import warnings
from collections import Counter
from pathlib import Path

import networkx as nx
import pandas as pd
from tabulate import tabulate

warnings.filterwarnings("ignore")

# --------------------------------------------------------------------------- #
# ------------------------------  I/O helpers  ------------------------------ #
# --------------------------------------------------------------------------- #

def load_and_prepare_data() -> dict:
    """Read all period CSV files. Adjust the paths if necessary."""
    try:
        data = {
            "pre_crimea": pd.read_csv("pre_crimea.csv"),
            "post_crimea": pd.read_csv("post_crimea.csv"),
            "covid": pd.read_csv("covid.csv"),
            "war": pd.read_csv("war.csv"),
        }
        return data
    except FileNotFoundError as err:
        print(f"[ERROR] Cannot load CSV files – {err}")
        return {}


def combine_all_periods(datasets: dict) -> pd.DataFrame:
    """Combine all period datasets into a single DataFrame for overall analysis."""
    frames = []
    for period_name, df in datasets.items():
        if not df.empty:
            tmp = df.copy()
            tmp["Period"] = period_name
            frames.append(tmp)
    if frames:
        combined = pd.concat(frames, ignore_index=True)
        print(f"[INFO] Combined dataset has {len(combined):,} rows from {len(frames)} periods")
        return combined
    return pd.DataFrame()

# --------------------------------------------------------------------------- #
# ---------------------------  network functions  --------------------------- #
# --------------------------------------------------------------------------- #

def build_cooccurrence_graph(df: pd.DataFrame) -> nx.Graph:
    """Build an undirected weighted graph based on entity co‑occurrence."""
    g = nx.Graph()
    for _, grp in df.groupby("Article_ID"):
        ents = grp["Entity"].tolist()
        for i in range(len(ents)):
            for j in range(i + 1, len(ents)):
                a, b = ents[i], ents[j]
                if g.has_edge(a, b):
                    g[a][b]["weight"] += 1
                else:
                    g.add_edge(a, b, weight=1)

    # add isolated nodes
    for ent in df["Entity"].unique():
        g.add_node(ent)

    # store inverse weights for distance‑based metrics (larger weight ⇒ shorter distance)
    for u, v, data in g.edges(data=True):
        data["inv_weight"] = 1.0 / data["weight"]
    return g


def count_edges_per_entity(df: pd.DataFrame) -> dict:
    """Edge count = how many partners an entity appears with across all articles."""
    cnt = Counter()
    for _, grp in df.groupby("Article_ID"):
        ents = grp["Entity"].tolist()
        for e in ents:
            cnt[e] += len(ents) - 1
    return cnt

# --------------------------------------------------------------------------- #
# ----------------------------  metric pipeline  ---------------------------- #
# --------------------------------------------------------------------------- #

def centrality_metrics(g: nx.Graph, df: pd.DataFrame) -> pd.DataFrame:
    """Compute centralities and enrich with Occurrences & Edge Count."""
    # --- centralities ------------------------------------------------------
    bet = nx.betweenness_centrality(g, weight="inv_weight")  # inverse weight → stronger = closer
    deg = nx.degree_centrality(g)
    clo = nx.closeness_centrality(g, distance="inv_weight")

    # --- occurrences -------------------------------------------------------
    if "Occurrences" in df.columns:
        # assume Occurrences is already aggregated per entity → keep first
        occ = (
            df.drop_duplicates(subset=["Entity"])
            .set_index("Entity")["Occurrences"]
            .to_dict()
        )
    else:
        occ = df["Entity"].value_counts().to_dict()

    occ_series = pd.Series(occ, dtype=float)
    norm_occ = occ_series / occ_series.sum()

    # --- edge counts -------------------------------------------------------
    edge_cnt = count_edges_per_entity(df)

    entities = list(g.nodes())
    metrics = pd.DataFrame(
        {
            "Entity": entities,
            "Betweenness": [bet.get(e, 0.0) for e in entities],
            "Degree": [deg.get(e, 0.0) for e in entities],
            "Closeness": [clo.get(e, 0.0) for e in entities],
            "Occurrences": [occ.get(e, 0) for e in entities],
            "Norm_Occ": [norm_occ.get(e, 0.0) for e in entities],
            "Edge_Count": [edge_cnt.get(e, 0) for e in entities],
        }
    )
    return metrics


def add_composite_score(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise metrics and compute weighted composite score. Excludes betweenness centrality."""
    def minmax(series: pd.Series) -> pd.Series:
        rng = series.max() - series.min()
        return (series - series.min()) / (rng + 1e-12)

    df = df.copy()
    df["N_Deg"] = minmax(df["Degree"])
    df["N_Clo"] = minmax(df["Closeness"])
    df["N_Edge"] = minmax(df["Edge_Count"])

    # Updated composite score without betweenness centrality
    # Redistributed weights: 0.4 Degree + 0.3 Closeness + 0.2 Norm_Occ + 0.1 Edge Count
    df["Composite_Score"] = (
        0.40 * df["N_Deg"]
        + 0.30 * df["N_Clo"]
        + 0.20 * df["Norm_Occ"]
        + 0.10 * df["N_Edge"]  # *normalised* edge count only
    )
    return df

# --------------------------------------------------------------------------- #
# ------------------------------  formatting  ------------------------------- #
# --------------------------------------------------------------------------- #

def make_display_table(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    # Filter out RDIF/Dmitriev related entities
    rdif_keywords = ['РФПИ', 'RDIF', 'Российский фонд прямых инвестиций', 'Russian Direct Investment Fund', 
                     'Дмитриев', 'Dmitriev', 'Кирилл Дмитриев', 'Kirill Dmitriev']
    
    # Create a mask to exclude entities containing any of these keywords
    mask = ~df['Entity'].str.contains('|'.join(rdif_keywords), case=False, na=False)
    filtered_df = df[mask]
    
    top = filtered_df.sort_values("Composite_Score", ascending=False).head(top_n).reset_index(drop=True)
    return pd.DataFrame(
        {
            "Rank": range(1, len(top) + 1),
            "Actor": top["Entity"],
            "Composite Score": top["Composite_Score"].round(4),
            "Degree": top["Degree"].round(4),
            "Closeness": top["Closeness"].round(4),
            "Occurrences": top["Occurrences"].astype(int),
            "Edge Count": top["Edge_Count"].astype(int),
        }
    )


def _escape_latex(text: str) -> str:
    """Escape LaTeX‑special characters."""
    mapping = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
        "\\": r"\textbackslash{}",
    }
    for k, v in mapping.items():
        text = text.replace(k, v)
    return text


def save_latex(table_df: pd.DataFrame, title_suffix: str, fname: str) -> None:
    """Write a standalone LaTeX file with the results table."""
    table_df = table_df.copy()
    table_df["Actor"] = table_df["Actor"].astype(str).apply(_escape_latex)

    header = r"""\documentclass[11pt,a4paper]{article}
\usepackage{booktabs,longtable,array,geometry,caption,siunitx}
\geometry{margin=1in}
\captionsetup{labelfont=bf}
\title{Network Analysis: Top 20 Actors -- """ + _escape_latex(title_suffix) + r"""}
\author{Automated SNA Report}
\date{\today}
\begin{document}
\maketitle
\section{Methodology}
A composite score $0.4\,\text{Degree} + 0.3\,\text{Closeness} + 0.2\,\text{Norm.\ Occurrences} + 0.1\,\text{Edge Count}$ ranks entities across all time periods. RDIF and Dmitriev entities are excluded from rankings.
\section{Results}
\begin{table}[htbp]
\centering
\caption{Top 20 actors by composite score -- """ + _escape_latex(title_suffix) + r"""}
\label{tab:top20overall}
\begin{tabular}{r l S[table-format=1.4] S[table-format=1.4] S[table-format=1.4] r r}
\toprule
Rank & Actor & {Composite} & {Degree} & {Closeness} & Occurrences & {Edge Count}\\
\midrule
"""

    body = "\n".join(
        f"{row.Rank} & {row.Actor} & {row['Composite Score']:.4f} & "
        f"{row.Degree:.4f} & {row.Closeness:.4f} & {row.Occurrences} & {row['Edge Count']} \\\
"
        for _, row in table_df.iterrows()
    )

    footer = r"""\bottomrule
\end{tabular}
\end{table}
\section{Discussion}
This analysis combines data from all time periods (Pre‑Crimea, Post‑Crimea, COVID, and War) to identify actors with consistent influence across the entire temporal scope.
\end{document}
"""

    Path(fname).write_text(header + body + footer, encoding="utf-8")
    print(f"[OK] LaTeX saved to '{fname}'")

# --------------------------------------------------------------------------- #
# ------------------------------  main driver  ------------------------------ #
# --------------------------------------------------------------------------- #

def analyse_overall_periods(combined_df: pd.DataFrame) -> None:
    if combined_df.empty:
        print("[ERROR] No combined data available for analysis")
        return

    g = build_cooccurrence_graph(combined_df)
    metrics = centrality_metrics(g, combined_df)
    metrics = add_composite_score(metrics)
    table = make_display_table(metrics)

    # console output
    print("\n" + "=" * 70)
    print(" TOP 20 ACTORS – ALL PERIODS COMBINED")
    print("=" * 70)
    print(tabulate(table, headers="keys", tablefmt="grid", floatfmt=".4f", showindex=False))

    # LaTeX output
    save_latex(table, "All Periods Combined", "top_20_actors_all_periods_combined.tex")


def main() -> None:
    data = load_and_prepare_data()
    if not data:
        return

    combined = combine_all_periods(data)
    if not combined.empty:
        analyse_overall_periods(combined)
    else:
        print("[ERROR] No data available from any period")

# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    main()
