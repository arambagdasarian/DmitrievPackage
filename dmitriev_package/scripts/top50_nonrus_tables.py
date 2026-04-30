"""
Top 50 Non-Russian Actors by Composite Score — LaTeX Tables

Builds the full co-occurrence network per period (edge weight >= 20), computes
composite = 0.4*degree + 0.4*closeness + 0.2*occ_norm in the full network
context, then ranks only entities whose most common Jurisdiction != 'RUS'.
Excludes Dmitriev and RDIF as usual.

Period tables: pre_crimea.csv, post_crimea.csv, covid.csv, war.csv
Overall table: final_nodes_fixed.csv (pooled)
"""

import os
import pandas as pd
import networkx as nx
import numpy as np

EXCLUDE_KEYWORDS = ['дмитриев', 'дмитриева', 'рфпи', 'rdif',
                    'российский фонд прямых инвестиций', 'rfpi']
RUSSIAN_JURISDICTIONS = {'RUS', 'Russia', 'RU', 'Russian Federation'}
MIN_EDGE_WEIGHT = 20

PERIOD_FILES = {
    'Pre-Crimea': 'data/periods/pre_crimea.csv',
    'Post-Crimea': 'data/periods/post_crimea.csv',
    'COVID':       'data/periods/covid.csv',
    'War':         'data/periods/war.csv',
}
OVERALL_FILE = 'data/periods/final_nodes_fixed.csv'


# ── helpers ──────────────────────────────────────────────────────────────────

def _latex_escape(s):
    if not isinstance(s, str):
        s = str(s)
    for c, r in [('&', r'\&'), ('%', r'\%'), ('_', r'\_'),
                 ('#', r'\#'), ('$', r'\$')]:
        s = s.replace(c, r)
    return s


def _is_excluded(name):
    if name is None or (isinstance(name, float) and pd.isna(name)):
        return True
    return any(kw in str(name).lower() for kw in EXCLUDE_KEYWORDS)


def _is_russian(name, entity_jurisdiction_map):
    """Return True if entity's most common jurisdiction is Russian."""
    jur = entity_jurisdiction_map.get(name)
    if jur is None:
        return False
    return str(jur).strip() in RUSSIAN_JURISDICTIONS


def build_jurisdiction_map(df):
    """Return {entity: most_common_jurisdiction} from df."""
    if 'Jurisdiction' not in df.columns:
        return {}
    jur = (df[['Entity', 'Jurisdiction']]
           .dropna(subset=['Jurisdiction'])
           .groupby('Entity')['Jurisdiction']
           .agg(lambda s: s.mode().iloc[0] if len(s) > 0 else None))
    return jur.to_dict()


def build_network(df):
    """Build weighted co-occurrence graph; attach occurrences and edge_count."""
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
    edges = [(a, b, w) for (a, b), w in ew.items() if w >= MIN_EDGE_WEIGHT]
    G = nx.Graph()
    G.add_weighted_edges_from(edges)
    occ = df.groupby('Entity')['Occurrences'].sum().to_dict()
    for n in G.nodes():
        wdeg = sum(G[n][nb]['weight'] for nb in G.neighbors(n))
        G.nodes[n]['occurrences'] = int(occ.get(n, 0))
        G.nodes[n]['edge_count'] = int(wdeg)
    return G


def compute_metrics(G, entity_jurisdiction_map):
    """
    Compute composite metrics for all non-excluded nodes in G.
    Filter to non-Russian jurisdictions before returning.
    """
    if G.number_of_nodes() == 0:
        return pd.DataFrame()
    dc = nx.degree_centrality(G)
    cc = nx.closeness_centrality(G)
    rows = []
    for n in G.nodes():
        if _is_excluded(n):
            continue
        if _is_russian(n, entity_jurisdiction_map):
            continue
        occ = G.nodes[n].get('occurrences', 0)
        ec  = G.nodes[n].get('edge_count', 0)
        rows.append({'actor': n, 'degree': dc.get(n, 0),
                     'closeness': cc.get(n, 0),
                     'occurrences': occ, 'edge_count': ec})
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    occ_max = df['occurrences'].max()
    occ_norm = (df['occurrences'] / occ_max) if occ_max > 0 else df['occurrences'] * 0
    df['composite'] = (0.4 * df['degree']
                       + 0.4 * df['closeness']
                       + 0.2 * occ_norm)
    df = df.sort_values('composite', ascending=False).reset_index(drop=True)
    return df[['actor', 'composite', 'degree', 'closeness', 'occurrences', 'edge_count']]


# ── LaTeX formatting ──────────────────────────────────────────────────────────

def latex_table(df, title, label, top_n=50):
    """Produce a longtable block matching the style of top50_actors_tables.tex."""
    df = df.head(top_n).copy().reset_index(drop=True)
    lines = [
        r'{\footnotesize',
        r'\setlength{\tabcolsep}{3.5pt}',
        r'\begin{longtable}{r >{\raggedright\arraybackslash}p{4.2cm} '
        r'S[table-format=1.4] S[table-format=1.4] S[table-format=1.4] r r}',
        f'\\caption{{{title}}} \\label{{{label}}} \\\\',
        r'\toprule',
        r'\textbf{Rank} & \textbf{Actor} & \textbf{Composite} & '
        r'\textbf{Degree} & \textbf{Closeness} & \textbf{Occurrences} & '
        r'\textbf{Edge Count} \\',
        r'\midrule',
        r'\endfirsthead',
        r'',
        r'\multicolumn{7}{r}{(Continued)} \\',
        r'\toprule',
        r'\textbf{Rank} & \textbf{Actor} & \textbf{Composite} & '
        r'\textbf{Degree} & \textbf{Closeness} & \textbf{Occurrences} & '
        r'\textbf{Edge Count} \\',
        r'\midrule',
        r'\endhead',
        r'',
        r'\endfoot',
        r'',
        r'\bottomrule',
        r'\endlastfoot',
        r'',
    ]
    for rank, row in df.iterrows():
        actor = _latex_escape(row['actor'])
        lines.append(
            f'{rank + 1} & {actor} & {row["composite"]:.4f} & '
            f'{row["degree"]:.4f} & {row["closeness"]:.4f} & '
            f'{int(row["occurrences"])} & {int(row["edge_count"])} \\\\'
        )
    lines += [r'\end{longtable}', r'}', '']
    return '\n'.join(lines)


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    os.chdir(base)
    out_dir = 'final visuals'
    os.makedirs(out_dir, exist_ok=True)

    header = (
        '% Top 50 NON-RUSSIAN actors by composite score (excl. Dmitriev/RDIF).\n'
        '% Composite = 0.4 * degree_cent + 0.4 * closeness_cent + 0.2 * occ_norm.\n'
        '% Centrality computed in FULL network; ranking filtered to Jurisdiction != RUS.\n'
        '% Required: \\usepackage{booktabs}, \\usepackage{siunitx}, '
        '\\usepackage{longtable}, \\usepackage{array}.\n\n'
        '\\setlength{\\LTleft}{0pt plus 1fill}\n'
        '\\setlength{\\LTright}{0pt plus 1fill}\n\n'
    )

    blocks = []

    # ── period tables ─────────────────────────────────────────────────────────
    for period_name, path in PERIOD_FILES.items():
        if not os.path.exists(path):
            print(f'  SKIP (not found): {path}')
            continue
        print(f'Processing {period_name} ...')
        df = pd.read_csv(path)
        jur_map = build_jurisdiction_map(df)
        G = build_network(df)
        m = compute_metrics(G, jur_map)
        if m.empty:
            print(f'  No non-Russian nodes found for {period_name}')
            continue
        slug  = period_name.replace('-', '_').replace(' ', '_').lower()
        title = f'Top 50 Non-Russian Actors by Composite Score -- {period_name} Period'
        label = f'tab:top50_nonrus_{slug}'
        blocks.append(latex_table(m, title, label))
        print(f'  {len(m)} non-Russian actors; top entry: {m.iloc[0]["actor"]} '
              f'({m.iloc[0]["composite"]:.4f})')

    # ── overall table (final_nodes_fixed.csv) ─────────────────────────────────
    print(f'\nProcessing Overall ({OVERALL_FILE}) ...')
    if os.path.exists(OVERALL_FILE):
        df_all = pd.read_csv(OVERALL_FILE)
        jur_map_all = build_jurisdiction_map(df_all)
        G_all = build_network(df_all)
        m_all = compute_metrics(G_all, jur_map_all)
        if not m_all.empty:
            blocks.append(latex_table(
                m_all,
                'Top 50 Non-Russian Actors by Composite Score -- Overall',
                'tab:top50_nonrus_overall'
            ))
            print(f'  {len(m_all)} non-Russian actors; top entry: '
                  f'{m_all.iloc[0]["actor"]} ({m_all.iloc[0]["composite"]:.4f})')
        else:
            print('  No non-Russian nodes found for overall.')
    else:
        print(f'  SKIP (not found): {OVERALL_FILE}')

    # ── write output ──────────────────────────────────────────────────────────
    out_path = os.path.join(out_dir, 'top50_nonrus_tables.tex')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(header)
        for b in blocks:
            f.write(b)
            f.write('\n')
    print(f'\nWrote {out_path}')


if __name__ == '__main__':
    main()
