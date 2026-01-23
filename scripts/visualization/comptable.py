#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create LaTeX tables with the 20 top actors (per period) ranked by a
composite centrality score.

Author: Your Name
Date  : 2025-07-25
"""
import warnings
from collections import Counter

import networkx as nx
import pandas as pd
from tabulate import tabulate

warnings.filterwarnings("ignore")

# --------------------------------------------------------------------------- #
# ------------------------------  I/O helpers  ------------------------------ #
# --------------------------------------------------------------------------- #
def load_and_prepare_data() -> dict:
    """
    Read all period CSV files.  Adjust the paths if necessary.
    """
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


# --------------------------------------------------------------------------- #
# ---------------------------  network functions  --------------------------- #
# --------------------------------------------------------------------------- #
def build_cooccurrence_graph(df: pd.DataFrame, min_edge_weight: int = 2) -> nx.Graph:
    """
    Build an undirected weighted graph where an edge weight equals the number
    of articles in which the two entities co-occur.
    Filter edges with weight < min_edge_weight for better centrality calculation.
    """
    print(f"Building co-occurrence graph with minimum edge weight: {min_edge_weight}")
    
    edge_weights = {}
    article_count = 0
    
    for _, group in df.groupby("Article_ID"):
        entities = group["Entity"].tolist()
        article_count += 1
        
        # Only process articles with multiple entities
        if len(entities) > 1:
            for i in range(len(entities)):
                for j in range(i + 1, len(entities)):
                    a, b = entities[i], entities[j]
                    edge = tuple(sorted([a, b]))  # Ensure consistent ordering
                    edge_weights[edge] = edge_weights.get(edge, 0) + 1
    
    print(f"Processed {article_count} articles, found {len(edge_weights)} potential edges")
    
    # Filter edges by minimum weight
    filtered_edges = [(a, b, w) for (a, b), w in edge_weights.items() if w >= min_edge_weight]
    
    print(f"Kept {len(filtered_edges)} edges with weight >= {min_edge_weight}")
    
    # Build graph
    g = nx.Graph()
    g.add_weighted_edges_from(filtered_edges)
    
    # Add isolated nodes for entities without sufficient connections
    all_entities = set(df["Entity"].unique())
    connected_entities = set(g.nodes())
    isolated_entities = all_entities - connected_entities
    
    g.add_nodes_from(isolated_entities)
    
    print(f"Final graph: {g.number_of_nodes()} nodes, {g.number_of_edges()} edges")
    print(f"Connected entities: {len(connected_entities)}, Isolated: {len(isolated_entities)}")
    
    return g


def count_edges_per_entity(df: pd.DataFrame) -> dict:
    """
    Edge count = how many times an entity appears *with someone else* in the
    same article (co-occurrence frequency).
    """
    counts = Counter()
    for _, group in df.groupby("Article_ID"):
        ents = group["Entity"].tolist()
        for ent in ents:
            counts[ent] += len(ents) - 1
    return counts


# --------------------------------------------------------------------------- #
# ----------------------------  metric pipeline  ---------------------------- #
# --------------------------------------------------------------------------- #
def centrality_metrics(g: nx.Graph, df: pd.DataFrame) -> pd.DataFrame:
    """
    Combine centralities, occurrences and edge counts into one DataFrame.
    """
    print(f"Calculating centralities for graph with {g.number_of_nodes()} nodes and {g.number_of_edges()} edges...")
    
    # Calculate centralities with proper normalization
    bet = nx.betweenness_centrality(g, weight="weight", normalized=True)
    deg = nx.degree_centrality(g)  # Already normalized
    clo = nx.closeness_centrality(g, distance="weight")  # Use weight as distance
    
    print(f"Betweenness range: {min(bet.values()):.6f} to {max(bet.values()):.6f}")
    print(f"Degree range: {min(deg.values()):.6f} to {max(deg.values()):.6f}")
    print(f"Closeness range: {min(clo.values()):.6f} to {max(clo.values()):.6f}")

    # CORRECTED: Sum occurrences per entity across all their appearances
    if "Occurrences" in df.columns:
        # Sum occurrences for each entity across all articles
        occ = df.groupby('Entity')['Occurrences'].sum().to_dict()
        print(f"Total occurrences calculated for {len(occ)} entities")
    else:
        # Fallback: count appearances if no Occurrences column
        occ = df["Entity"].value_counts().to_dict()

    edge_cnt = count_edges_per_entity(df)

    # Convert to pandas Series for easier manipulation
    occ_series = pd.Series(occ)
    total_occ = occ_series.sum()
    norm_occ = occ_series / total_occ
    
    print(f"Occurrence range: {occ_series.min()} to {occ_series.max()}")

    entities = list(g.nodes())
    data = {
        "Entity": entities,
        "Betweenness": [bet.get(e, 0) for e in entities],
        "Degree": [deg.get(e, 0) for e in entities],
        "Closeness": [clo.get(e, 0) for e in entities],
        "Occurrences": [occ.get(e, 0) for e in entities],
        "Norm_Occ": [norm_occ.get(e, 0) for e in entities],
        "Edge_Count": [edge_cnt.get(e, 0) for e in entities],
    }
    return pd.DataFrame(data)


def add_composite_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalise metrics to [0,1] and compute weighted composite score.
    Excludes betweenness centrality as requested.
    """
    def minmax(s):
        return (s - s.min()) / (s.max() - s.min() + 1e-12)

    df["N_Deg"] = minmax(df["Degree"])
    df["N_Clo"] = minmax(df["Closeness"])
    df["N_Edge"] = minmax(df["Edge_Count"])

    # Updated composite score without betweenness centrality
    # Redistributed weights: 0.4 Degree + 0.3 Closeness + 0.2 Norm_Occ + 0.1 Edge Count
    df["Composite_Score"] = (
        0.4 * df["N_Deg"]
        + 0.3 * df["N_Clo"]
        + 0.2 * df["Norm_Occ"]
        + 0.1 * df["N_Edge"]
    )
    return df


# --------------------------------------------------------------------------- #
# ------------------------------  formatting  ------------------------------- #
# --------------------------------------------------------------------------- #
def make_display_table(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """
    Return a DataFrame ready for printing / LaTeX (no normalised columns).
    Excludes RDIF/Dmitriev entities and betweenness centrality.
    """
    # Filter out RDIF/Dmitriev related entities
    rdif_keywords = ['РФПИ', 'RDIF', 'Российский фонд прямых инвестиций', 'Russian Direct Investment Fund', 
                     'Дмитриев', 'Dmitriev', 'Кирилл Дмитриев', 'Kirill Dmitriev']
    
    # Create a mask to exclude entities containing any of these keywords
    mask = ~df['Entity'].str.contains('|'.join(rdif_keywords), case=False, na=False)
    filtered_df = df[mask]
    
    top = (
        filtered_df.sort_values("Composite_Score", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )

    out = pd.DataFrame(
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
    return out


def escape_latex(text: str) -> str:
    """
    Escape LaTeX-special characters in strings.
    """
    repl = {
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
    for char, esc in repl.items():
        text = text.replace(char, esc)
    return text


def save_latex(df: pd.DataFrame, period: str, fname: str) -> None:
    """
    Write a full standalone LaTeX file containing the results table.
    """
    # escape actor names
    df = df.copy()
    df["Actor"] = df["Actor"].astype(str).apply(escape_latex)

    header = r"""\documentclass[11pt,a4paper]{article}
\usepackage{booktabs,longtable,array,geometry,caption,siunitx}
\geometry{margin=1in}
\captionsetup{labelfont=bf}
\title{Network Analysis: Top 20 Actors -- """ + f"{escape_latex(period)} Period" + r"""}
\author{Automated SNA Report}
\date{\today}
\begin{document}
\maketitle
\section{Methodology}
A composite score $0.4\,\text{Degree}+0.3\,\text{Closeness}+0.2\,\text{Norm.\ Occurrences}+0.1\,\text{Edge Count}$ ranks entities. RDIF and Dmitriev entities are excluded from rankings.
\section{Results}
\begin{table}[htbp]
\centering
\caption{Top 20 actors by composite score -- """ + f"{escape_latex(period)} Period" + r"""}
\label{tab:top20}
\begin{tabular}{r l S[table-format=1.4] S[table-format=1.4] S[table-format=1.4] r r}
\toprule
Rank & Actor & {Composite} & {Degree} & {Closeness} & Occurrences & {Edge Count}\\
\midrule
"""

    body_lines = []
    for _, row in df.iterrows():
        body_lines.append(
            f"{row['Rank']} & {row['Actor']} & "
            f"{row['Composite Score']:.4f} & "
            f"{row['Degree']:.4f} & {row['Closeness']:.4f} & "
            f"{row['Occurrences']} & {row['Edge Count']} \\\\"
        )
    body = "\n".join(body_lines)

    footer = r"""\bottomrule
\end{tabular}
\end{table}
\end{document}
"""

    with open(fname, "w", encoding="utf-8") as tex:
        tex.write(header + body + footer)

    print(f"[OK]  LaTeX saved to '{fname}'")


# --------------------------------------------------------------------------- #
# ------------------------------  main driver  ------------------------------ #
# --------------------------------------------------------------------------- #
def analyse_period(df: pd.DataFrame, period: str) -> None:
    """
    Run full pipeline for a single period and write LaTeX + console table.
    """
    print(f"\n{'='*70}")
    print(f"ANALYZING PERIOD: {period.upper()}")
    print(f"Dataset size: {len(df)} rows, {df['Entity'].nunique()} unique entities")
    print(f"{'='*70}")
    
    # Use minimum edge weight of 2 to focus on meaningful connections
    graph = build_cooccurrence_graph(df, min_edge_weight=2)
    metrics = centrality_metrics(graph, df)
    metrics = add_composite_score(metrics)
    table = make_display_table(metrics)

    # --- console output ----------------------------------------------------
    print("\n" + "=" * 70)
    print(f" TOP 20 ACTORS – {period.upper()} PERIOD")
    print("=" * 70)
    print(
        tabulate(
            table,
            headers="keys",
            tablefmt="grid",
            floatfmt=".4f",
            showindex=False,
            maxcolwidths=[5, 25, 10, 10, 10, 10, 10, 10],
        )
    )

    # --- LaTeX output ------------------------------------------------------
    fname = f"top_20_actors_{period.lower().replace(' ', '_').replace('-', '_')}.tex"
    save_latex(table, period, fname)


def main() -> None:
    periods = {
        "Pre-Crimea": "pre_crimea",
        "Post-Crimea": "post_crimea",
        "COVID": "covid",
        "War": "war",
    }

    datasets = load_and_prepare_data()
    if not datasets:
        return

    for pretty, key in periods.items():
        if key in datasets and not datasets[key].empty:
            analyse_period(datasets[key], pretty)
        else:
            print(f"[WARN] No data for period '{pretty}'")


# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    main()
