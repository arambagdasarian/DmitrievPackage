"""
Top 50 Network Graphs (excl. RDIF/Dmitriev)

Four network visualizations (Pre-Crimea, Post-Crimea, COVID, War). Each shows
the top 50 actors by composite score; nodes colored by period when they first
entered the network. New entities joining (and leaving) are documented in a
separate text file, not on the graph.
"""

import os
import sys
import pandas as pd
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

EXCLUDE_KEYWORDS = ['дмитриев', 'дмитриева', 'рфпи', 'rdif', 'российский фонд прямых инвестиций', 'rfpi']
MIN_EDGE_WEIGHT = 20
PERIODS = ['Pre-Crimea', 'Post-Crimea', 'COVID', 'War']
PERIOD_FILES = {
    'Pre-Crimea': 'data/periods/pre_crimea.csv',
    'Post-Crimea': 'data/periods/post_crimea.csv',
    'COVID': 'data/periods/covid.csv',
    'War': 'data/periods/war.csv',
}

# Colors by period when entity first entered
PERIOD_COLORS = {
    'Pre-Crimea': '#000000',
    'Post-Crimea': '#e67e22',
    'COVID': '#27ae60',
    'War': '#c0392b',
}


def _is_excluded(name):
    if name is None or (isinstance(name, float) and pd.isna(name)):
        return True
    x = str(name).lower()
    return any(kw in x for kw in EXCLUDE_KEYWORDS)


def build_network(df, min_edge_weight=20):
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
    df['composite'] = 0.4 * df['degree'] + 0.4 * df['closeness'] + 0.2 * occ_norm
    df = df.sort_values('composite', ascending=False).reset_index(drop=True)
    return df[['actor', 'composite', 'degree', 'closeness', 'occurrences', 'edge_count']]


def get_top50_per_period():
    """Return dict period -> set of top 50 actor names (excl. RDIF/Dmitriev)."""
    out = {}
    for p in PERIODS:
        path = PERIOD_FILES.get(p)
        if not path or not os.path.exists(path):
            continue
        df = pd.read_csv(path)
        G = build_network(df, MIN_EDGE_WEIGHT)
        m = compute_metrics(G).head(50)
        out[p] = set(m['actor'].tolist())
    return out


def first_period(actor, top50_per_period):
    """Earliest period in which actor appears in top 50."""
    for p in PERIODS:
        if actor in top50_per_period.get(p, set()):
            return p
    return None


def run(output_dir='final visuals'):
    base = os.path.join(os.path.dirname(__file__), '..', '..')
    os.chdir(base)
    os.makedirs(output_dir, exist_ok=True)

    top50 = get_top50_per_period()
    networks = {}
    for p in PERIODS:
        path = PERIOD_FILES.get(p)
        if not path or not os.path.exists(path):
            continue
        df = pd.read_csv(path)
        G = build_network(df, MIN_EDGE_WEIGHT)
        networks[p] = G

    # Join/leave: relative to *top 50* of previous period
    joining = {p: [] for p in PERIODS}
    leaving = {p: [] for p in PERIODS}
    prev = set()
    for p in PERIODS:
        curr = top50.get(p, set())
        joining[p] = sorted(curr - prev)
        leaving[p] = sorted(prev - curr) if prev else []
        prev = curr

    # Draw 4 graphs
    for period_name in PERIODS:
        G = networks.get(period_name)
        nodes = top50.get(period_name, set())
        if not G or not nodes:
            continue
        nodes = nodes & set(G.nodes())
        if not nodes:
            continue
        H = G.subgraph(nodes).copy()
        if H.number_of_nodes() == 0:
            continue

        node_colors = [PERIOD_COLORS.get(first_period(n, top50), '#95a5a6') for n in H.nodes()]
        first_periods = [first_period(n, top50) for n in H.nodes()]
        used_periods = sorted(set(first_periods) & set(PERIODS), key=PERIODS.index)

        pos = nx.spring_layout(H, k=1.4, iterations=100, seed=42)
        fig, ax = plt.subplots(figsize=(14, 12))
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')
        nx.draw_networkx_edges(H, pos, edge_color='#cccccc', width=0.5, alpha=0.45, ax=ax)
        nx.draw_networkx_nodes(H, pos, node_color=node_colors, node_size=450, alpha=0.95,
                              edgecolors='white', linewidths=1.5, ax=ax)
        # No node labels

        ax.set_title(f'{period_name} Period\nTop 50 actors', fontsize=13, fontweight='bold', pad=14)
        ax.axis('off')
        plt.tight_layout()

        import matplotlib.patches as mpatches
        legend_handles = [mpatches.Patch(color=PERIOD_COLORS[p], label=f'Entered in {p}') for p in used_periods]
        ax.legend(handles=legend_handles, loc='upper left', fontsize=9, frameon=True, fancybox=True)

        slug = period_name.lower().replace('-', '_').replace(' ', '_')
        out_png = os.path.join(output_dir, f'top50_network_{slug}.png')
        out_pdf = out_png.replace('.png', '.pdf')
        plt.savefig(out_png, dpi=300, bbox_inches='tight', facecolor='white')
        plt.savefig(out_pdf, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        print(f'  ✓ {out_png}')

    # Join/leave document
    report_path = os.path.join(output_dir, 'top50_network_joining_leaving.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('=' * 80 + '\n')
        f.write('TOP 50 NETWORK: ENTITIES JOINING AND LEAVING (excl. RDIF/Dmitriev)\n')
        f.write('=' * 80 + '\n\n')
        f.write('Joining = in this period\'s top 50 but not in the previous period\'s top 50.\n')
        f.write('Leaving = in the previous period\'s top 50 but not in this period\'s top 50.\n\n')
        for p in PERIODS:
            f.write('\n' + '=' * 80 + '\n')
            f.write(f'{p} Period\n')
            f.write('=' * 80 + '\n\n')
            f.write(f'JOINING THE TOP 50 NETWORK ({len(joining[p])})\n')
            f.write('-' * 80 + '\n\n')
            for e in joining[p]:
                f.write(f'  • {e}\n')
            f.write(f'\nLEAVING THE TOP 50 NETWORK ({len(leaving[p])})\n')
            f.write('-' * 80 + '\n\n')
            for e in leaving[p]:
                f.write(f'  • {e}\n')
    print(f'  ✓ {report_path}')
    print('Done.')


if __name__ == '__main__':
    run()
