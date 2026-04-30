"""
Semantic Community Structure Series (Edge weight ≥ 120)

Creates Louvain community visualizations colored by community type only:
- RDIF Core Network (red)
- Financial Network (orange)
- Financial Institutions (dark grey)
- Mixed Network (pink/magenta)
- Other (blue) — Government, Energy, etc.

No node labels. Color legend included. Joining/leaving are documented in a
separate text report, not shown on the graph.
"""

import os
import sys
import pandas as pd
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

MIN_EDGE_WEIGHT = 120
RDIF_KEYWORDS = ['дмитриев', 'дмитриева', 'рфпи', 'rdif', 'российский фонд прямых инвестиций', 'rfpi']
FI_KEYWORDS = ['банк', 'bank', 'фонд', 'fund', 'институт', 'institution', 'инвест', 'investment']


def create_network_from_csv(file_path, min_edge_weight=20):
    """Build network from period CSV and attach node attributes."""
    df = pd.read_csv(file_path)
    article_entities = df.groupby('Article_ID')['Entity'].apply(list).reset_index()
    edge_weights = {}
    for _, row in article_entities.iterrows():
        entities = row['Entity']
        if len(entities) < 2:
            continue
        for i in range(len(entities)):
            for j in range(i + 1, len(entities)):
                e1, e2 = sorted([entities[i], entities[j]])
                edge_weights[(e1, e2)] = edge_weights.get((e1, e2), 0) + 1
    filtered = [(a, b, w) for (a, b), w in edge_weights.items() if w >= min_edge_weight]
    G = nx.Graph()
    G.add_weighted_edges_from(filtered)
    agg_dict = {'Occurrences': 'sum', 'Entity_Type': 'first', 'Sector': 'first'}
    if 'State/Private' in df.columns:
        agg_dict['State/Private'] = 'first'
    if 'Jurisdiction' in df.columns:
        agg_dict['Jurisdiction'] = 'first'
    node_attrs = df.groupby('Entity').agg(agg_dict).to_dict()
    for node in G.nodes():
        sec = node_attrs.get('Sector', {}).get(node)
        typ = node_attrs.get('Entity_Type', {}).get(node)
        sp = node_attrs.get('State/Private', {}).get(node) if 'State/Private' in agg_dict else None
        jur = node_attrs.get('Jurisdiction', {}).get(node) if 'Jurisdiction' in agg_dict else None
        occ = node_attrs.get('Occurrences', {}).get(node, 0)
        G.nodes[node]['sector'] = sec if sec is not None and (not isinstance(sec, float) or not pd.isna(sec)) else 'Unknown'
        G.nodes[node]['entity_type'] = typ if typ is not None and (not isinstance(typ, float) or not pd.isna(typ)) else 'Unknown'
        G.nodes[node]['state_private'] = sp if sp is not None and (not isinstance(sp, float) or not pd.isna(sp)) else 'Unknown'
        G.nodes[node]['jurisdiction'] = jur if jur is not None and (not isinstance(jur, float) or not pd.isna(jur)) else 'Unknown'
        G.nodes[node]['total_occurrences'] = int(occ) if occ is not None else 0
    return G


def get_entity_metadata_from_csv(file_path, entities):
    """Return dict entity -> {sector, entity_type, state_private, jurisdiction, occurrences}."""
    df = pd.read_csv(file_path)
    agg = {'Occurrences': 'sum', 'Entity_Type': 'first', 'Sector': 'first'}
    if 'State/Private' in df.columns:
        agg['State/Private'] = 'first'
    if 'Jurisdiction' in df.columns:
        agg['Jurisdiction'] = 'first'
    g = df.groupby('Entity').agg(agg)
    out = {}
    for e in entities:
        if e not in g.index:
            out[e] = {'sector': 'Unknown', 'entity_type': 'Unknown', 'state_private': 'Unknown', 'jurisdiction': 'Unknown', 'occurrences': 0}
            continue
        row = g.loc[e]
        def _v(x, default='Unknown'):
            if x is None or (isinstance(x, float) and pd.isna(x)):
                return default
            return x
        out[e] = {
            'sector': _v(row.get('Sector', 'Unknown')),
            'entity_type': _v(row.get('Entity_Type', 'Unknown')),
            'state_private': _v(row.get('State/Private', 'Unknown')) if 'State/Private' in agg else 'Unknown',
            'jurisdiction': _v(row.get('Jurisdiction', 'Unknown')) if 'Jurisdiction' in agg else 'Unknown',
            'occurrences': int(row.get('Occurrences', 0) or 0),
        }
    return out


def is_rdif_core(name):
    if name is None or (isinstance(name, float) and pd.isna(name)):
        return False
    s = str(name).lower()
    return any(kw in s for kw in RDIF_KEYWORDS)


def is_financial_institution(name, sector):
    if sector is None or (isinstance(sector, float) and pd.isna(sector)):
        sector = ''
    s = (str(name) + ' ' + str(sector)).lower()
    return any(kw in s for kw in FI_KEYWORDS)


def classify_node_community(node, G):
    """Classify node by community type only (no new/continuing). Return (label, color)."""
    sector = G.nodes[node].get('sector') or 'Unknown'
    if pd.isna(sector):
        sector = 'Unknown'
    sector = str(sector)
    if is_rdif_core(node):
        return 'RDIF Core Network', '#e74c3c'
    if (sector == 'Finance' or 'Finance' in sector) and is_financial_institution(node, sector):
        return 'Financial Institutions', '#34495e'
    if sector == 'Finance' or 'Finance' in sector:
        return 'Financial Network', '#e67e22'
    if sector == 'Unknown' or sector == 'Mixed' or sector == '':
        return 'Mixed Network', '#e91e8c'
    return 'Other', '#3498db'


def detect_louvain_communities(G):
    if G.number_of_nodes() == 0:
        return {}
    try:
        from networkx.algorithms import community as nx_comm
        comms = list(nx_comm.louvain_communities(G, seed=42, resolution=1.0))
    except Exception:
        comms = list(nx.connected_components(G))
    m = {}
    for i, c in enumerate(comms):
        for n in c:
            m[n] = i
    return m


def create_semantic_series(output_dir='final visuals'):
    period_files = {
        'Pre-Crimea': 'data/periods/pre_crimea.csv',
        'Post-Crimea': 'data/periods/post_crimea.csv',
        'COVID': 'data/periods/covid.csv',
        'War': 'data/periods/war.csv',
    }
    os.makedirs(output_dir, exist_ok=True)
    min_edge = MIN_EDGE_WEIGHT

    # Baseline
    pre_path = period_files['Pre-Crimea']
    if not os.path.exists(pre_path):
        print('Pre-Crimea data not found.')
        return
    G_base = create_network_from_csv(pre_path, min_edge_weight=min_edge)
    baseline_nodes = set(G_base.nodes())
    print(f"Semantic series (edge ≥ {min_edge}). Baseline: {len(baseline_nodes)} nodes.")

    # Legend: community types only (no new/continuing)
    legend_spec = [
        ('RDIF Core Network', '#e74c3c'),
        ('Financial Network', '#e67e22'),
        ('Financial Institutions', '#34495e'),
        ('Mixed Network', '#e91e8c'),
        ('Other', '#3498db'),
    ]

    for period_name, path in period_files.items():
        if not os.path.exists(path):
            continue
        try:
            print(f"\nProcessing {period_name}...")
            G = create_network_from_csv(path, min_edge_weight=min_edge)
            if G.number_of_nodes() == 0:
                continue
            node_community = detect_louvain_communities(G)
            node_colors = []
            node_labels = []
            for n in G.nodes():
                label, color = classify_node_community(n, G)
                node_labels.append(label)
                node_colors.append(color)
            degrees = dict(G.degree())
            mx = max(degrees.values()) if degrees else 1
            node_sizes = [300 + 700 * (degrees[n] / mx) for n in G.nodes()]
            pos = nx.spring_layout(G, k=1.5, iterations=50, seed=42)
            fig, ax = plt.subplots(figsize=(16, 12))
            fig.patch.set_facecolor('white')
            ax.set_facecolor('white')
            nx.draw_networkx_edges(G, pos, edge_color='#cccccc', width=0.5, alpha=0.4, ax=ax)
            nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes,
                                  alpha=0.9, edgecolors='white', linewidths=1.5, ax=ax)
            ax.set_title(f"{period_name} Period (Edge weight ≥ {min_edge})\nSemantic Community Structure",
                        fontsize=14, fontweight='bold', pad=20)
            legend_handles = [mpatches.Patch(color=c, label=l) for l, c in legend_spec]
            ax.legend(handles=legend_handles, loc='upper right', fontsize=10, frameon=True, fancybox=True)
            ax.axis('off')
            plt.tight_layout()
            slug = period_name.lower().replace('-', '_').replace(' ', '_')
            out_png = os.path.join(output_dir, f'semantic_community_{slug}.png')
            out_pdf = out_png.replace('.png', '.pdf')
            plt.savefig(out_png, dpi=300, bbox_inches='tight', facecolor='white')
            plt.savefig(out_pdf, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            print(f"  ✓ {out_png} | nodes={G.number_of_nodes()} edges={G.number_of_edges()} communities={len(set(node_community.values()))}")
        except Exception as e:
            import traceback
            print(f"  ✗ {period_name}: {e}")
            traceback.print_exc()

    # Join/leave report for semantic network (edge ≥ 120)
    _write_joining_leaving_report(period_files, min_edge, output_dir)
    print("\n✓ Semantic community series and join/leave report done.")


def _write_joining_leaving_report(period_files, min_edge, output_dir):
    """Text report of entities joining and leaving the semantic network (edge ≥ 120)."""
    networks = {}
    metadata = {}
    for name, path in period_files.items():
        if not os.path.exists(path):
            continue
        G = create_network_from_csv(path, min_edge_weight=min_edge)
        networks[name] = G
        metadata[name] = get_entity_metadata_from_csv(path, set(G.nodes()))
    if 'Pre-Crimea' not in networks:
        return
    baseline = set(networks['Pre-Crimea'].nodes())
    report_path = os.path.join(output_dir, 'semantic_network_entities_joining_leaving.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("SEMANTIC NETWORK: ENTITIES JOINING AND LEAVING\n")
        f.write("(Edge weight ≥ 120)\n")
        f.write("=" * 80 + "\n\n")
        f.write("Baseline: Pre-Crimea. \"Joining\" = in period but not in Pre-Crimea.\n")
        f.write("\"Leaving\" = in Pre-Crimea but not in period.\n\n")
        f.write(f"Baseline nodes: {len(baseline)}\n")
        f.write(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        for period in ['Post-Crimea', 'COVID', 'War']:
            if period not in networks:
                continue
            curr = set(networks[period].nodes())
            joined = curr - baseline
            left = baseline - curr
            meta = metadata.get(period, {})
            meta_base = metadata.get('Pre-Crimea', {})
            f.write("\n" + "=" * 80 + "\n")
            f.write(f"{period}\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"JOINING THE NETWORK ({len(joined)})\n")
            f.write("-" * 80 + "\n\n")
            for e in sorted(joined, key=lambda x: meta.get(x, {}).get('occurrences', 0), reverse=True):
                m = meta.get(e, {})
                f.write(f"  • {e}\n")
                f.write(f"    Sector: {m.get('sector', 'Unknown')}  Type: {m.get('entity_type', 'Unknown')}  ")
                f.write(f"State/Private: {m.get('state_private', 'Unknown')}  Jurisdiction: {m.get('jurisdiction', 'Unknown')}\n")
                f.write(f"    Occurrences: {m.get('occurrences', 0):,}\n\n")
            f.write(f"\nLEAVING THE NETWORK ({len(left)})\n")
            f.write("-" * 80 + "\n\n")
            for e in sorted(left, key=lambda x: meta_base.get(x, {}).get('occurrences', 0), reverse=True):
                m = meta_base.get(e, {})
                f.write(f"  • {e}\n")
                f.write(f"    Sector: {m.get('sector', 'Unknown')}  Type: {m.get('entity_type', 'Unknown')}  ")
                f.write(f"State/Private: {m.get('state_private', 'Unknown')}  Jurisdiction: {m.get('jurisdiction', 'Unknown')}\n")
                f.write(f"    Occurrences (Pre-Crimea): {m.get('occurrences', 0):,}\n\n")
    print(f"  ✓ {report_path}")


if __name__ == '__main__':
    create_semantic_series()
