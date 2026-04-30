"""
Top 50 Actors by Composite Score — LaTeX Tables

Computes composite = f(degree centrality, closeness centrality, occurrences).
Excludes Dmitriev and RDIF. Outputs:
- Top 50 per period (Pre-Crimea, Post-Crimea, COVID, War)
- Top 50 overall (pooled network)
"""

import os
import re
import pandas as pd
import networkx as nx
import numpy as np

EXCLUDE_KEYWORDS = ['дмитриев', 'дмитриева', 'рфпи', 'rdif', 'российский фонд прямых инвестиций', 'rfpi']
MIN_EDGE_WEIGHT = 20
PERIOD_FILES = {
    'Pre-Crimea': 'data/periods/pre_crimea.csv',
    'Post-Crimea': 'data/periods/post_crimea.csv',
    'COVID': 'data/periods/covid.csv',
    'War': 'data/periods/war.csv',
}


def _latex_escape(s):
    if not isinstance(s, str):
        s = str(s)
    for c, r in [('&', r'\&'), ('%', r'\%'), ('_', r'\_'), ('#', r'\#'), ('$', r'\$')]:
        s = s.replace(c, r)
    return s


def _is_excluded(name):
    if name is None or (isinstance(name, float) and pd.isna(name)):
        return True
    x = str(name).lower()
    return any(kw in x for kw in EXCLUDE_KEYWORDS)


def build_network(df, min_edge_weight=20):
    """Build weighted graph from entity co-occurrences. Return G and entity->{occ, edge_count}."""
    ae = df.groupby('Article_ID')['Entity'].apply(list).reset_index()
    ew = {}
    for _, row in ae.iterrows():
        entities = row['Entity']
        if len(entities) < 2:
            continue
        for i in range(len(entities)):
            for j in range(i + 1, len(entities)):
                e1, e2 = sorted([entities[i], entities[j]])
                k = (e1, e2)
                ew[k] = ew.get(k, 0) + 1
    edges = [(a, b, w) for (a, b), w in ew.items() if w >= min_edge_weight]
    G = nx.Graph()
    G.add_weighted_edges_from(edges)
    occ = df.groupby('Entity')['Occurrences'].sum().to_dict()
    wdeg = {}
    for n in G.nodes():
        wdeg[n] = sum(G[n][nb]['weight'] for nb in G.neighbors(n))
    for n in G.nodes():
        G.nodes[n]['occurrences'] = int(occ.get(n, 0))
        G.nodes[n]['edge_count'] = int(wdeg.get(n, 0))
    return G


def compute_metrics(G):
    """DataFrame with columns: actor, composite, degree, closeness, occurrences, edge_count."""
    if G.number_of_nodes() == 0:
        return pd.DataFrame()
    dc = nx.degree_centrality(G)
    cc = nx.closeness_centrality(G)
    rows = []
    for n in G.nodes():
        if _is_excluded(n):
            continue
        occ = G.nodes[n].get('occurrences', 0)
        ec = G.nodes[n].get('edge_count', 0)
        d = dc.get(n, 0)
        c = cc.get(n, 0)
        rows.append({'actor': n, 'degree': d, 'closeness': c, 'occurrences': occ, 'edge_count': ec})
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    occ_max = df['occurrences'].max()
    occ_norm = (df['occurrences'] / occ_max).replace(np.nan, 0) if occ_max > 0 else df['occurrences'] * 0
    # Composite: 0.4 * degree + 0.4 * closeness + 0.2 * occ_norm
    df['composite'] = 0.4 * df['degree'] + 0.4 * df['closeness'] + 0.2 * occ_norm
    df = df.sort_values('composite', ascending=False).reset_index(drop=True)
    return df[['actor', 'composite', 'degree', 'closeness', 'occurrences', 'edge_count']]


def latex_table(df, title, label, top_n=50):
    """Produce LaTeX longtable: flows across pages, header repeated on each."""
    df = df.head(top_n).copy()
    df['rank'] = range(1, len(df) + 1)
    lines = [
        r'{\small',
        r'\begin{longtable}{r >{\raggedright\arraybackslash}p{4.2cm} S[table-format=1.4] S[table-format=1.4] S[table-format=1.4] r r}',
        f'\\caption{{{title}}} \\label{{{label}}} \\\\',
        r'\toprule',
        r'\textbf{Rank} & \textbf{Actor} & \textbf{Composite} & \textbf{Degree} & \textbf{Closeness} & \textbf{Occurrences} & \textbf{Edge Count} \\',
        r'\midrule',
        r'\endfirsthead',
        r'',
        r'\multicolumn{7}{r}{(Continued)} \\',
        r'\toprule',
        r'\textbf{Rank} & \textbf{Actor} & \textbf{Composite} & \textbf{Degree} & \textbf{Closeness} & \textbf{Occurrences} & \textbf{Edge Count} \\',
        r'\midrule',
        r'\endhead',
        r'',
        r'\midrule',
        r'\multicolumn{7}{r}{(Continued on next page)} \\',
        r'\endfoot',
        r'',
        r'\bottomrule',
        r'\endlastfoot',
        r'',
    ]
    for _, row in df.iterrows():
        actor = _latex_escape(row['actor'])
        r = int(row['rank'])
        comp = float(row['composite'])
        deg = float(row['degree'])
        close = float(row['closeness'])
        occ = int(row['occurrences'])
        ec = int(row['edge_count'])
        lines.append(f'{r} & {actor} & {comp:.4f} & {deg:.4f} & {close:.4f} & {occ} & {ec} \\\\')
    lines.extend([r'\end{longtable}', r'}', ''])
    return '\n'.join(lines)


def main():
    base = os.path.join(os.path.dirname(__file__), '..', '..')
    os.chdir(base)
    out_dir = 'final visuals'
    os.makedirs(out_dir, exist_ok=True)

    all_dfs = []
    period_tables = []

    for period_name, path in PERIOD_FILES.items():
        if not os.path.exists(path):
            continue
        df = pd.read_csv(path)
        G = build_network(df, MIN_EDGE_WEIGHT)
        m = compute_metrics(G)
        if m.empty:
            continue
        m = m.head(50)
        all_dfs.append(m.assign(period=period_name))
        slug = period_name.replace('-', '_').replace(' ', '_').lower()
        title = f'Top 50 Actors by Composite Score -- {period_name} Period'
        label = f'tab:top50_{slug}'
        period_tables.append(latex_table(m, title, label, top_n=50))

    # Overall: pool all period data
    combined = []
    for path in PERIOD_FILES.values():
        if os.path.exists(path):
            combined.append(pd.read_csv(path))
    if combined:
        pool = pd.concat(combined, ignore_index=True)
        G_all = build_network(pool, MIN_EDGE_WEIGHT)
        m_all = compute_metrics(G_all).head(50)
        title_all = 'Top 50 Actors by Composite Score -- Overall'
        label_all = 'tab:top50_overall'
        overall_table = latex_table(m_all, title_all, label_all, top_n=50)
    else:
        overall_table = ''

    # Write LaTeX file
    out_path = os.path.join(out_dir, 'top50_actors_tables.tex')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('% Top 50 actors by composite score (excl. Dmitriev/RDIF).\n')
        f.write('% Composite = 0.4 * degree_cent + 0.4 * closeness_cent + 0.2 * occ_norm.\n')
        f.write('% Required: \\usepackage{booktabs}, \\usepackage{siunitx}, \\usepackage{longtable}.\n')
        f.write('% Tables flow across pages; header repeats on each continued page.\n\n')
        for t in period_tables:
            f.write(t)
            f.write('\n')
        if overall_table:
            f.write(overall_table)
    print(f'Wrote {out_path}')
    return out_path


if __name__ == '__main__':
    main()
