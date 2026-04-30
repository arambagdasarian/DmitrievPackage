"""
Louvain Community Network Visualizations

Creates network visualizations showing Louvain communities for each period.
Nodes colored by: RDIF Core (red), New entities joining (green), Continuing entities (blue).
No node labels. Color legend included.
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

# RDIF core keywords for classification
RDIF_KEYWORDS = ['дмитриев', 'дмитриева', 'рфпи', 'rdif', 'российский фонд прямых инвестиций', 'rfpi']


def create_network_from_csv(file_path, min_edge_weight=20):
    """Create network from CSV file"""
    df = pd.read_csv(file_path)
    
    article_entities = df.groupby('Article_ID')['Entity'].apply(list).reset_index()
    
    edge_weights = {}
    for _, row in article_entities.iterrows():
        entities = row['Entity']
        if len(entities) < 2:
            continue
            
        for i in range(len(entities)):
            for j in range(i + 1, len(entities)):
                entity1, entity2 = entities[i], entities[j]
                edge = tuple(sorted([entity1, entity2]))
                edge_weights[edge] = edge_weights.get(edge, 0) + 1
    
    filtered_edges = [(e[0], e[1], w) for e, w in edge_weights.items() if w >= min_edge_weight]
    
    G = nx.Graph()
    G.add_weighted_edges_from(filtered_edges)
    
    # Add node attributes
    node_attributes = df.groupby('Entity').agg({
        'Occurrences': 'sum',
        'Entity_Type': 'first',
        'Sector': 'first'
    }).to_dict()
    
    for node in G.nodes():
        if node in node_attributes['Occurrences']:
            G.nodes[node]['total_occurrences'] = node_attributes['Occurrences'][node]
            G.nodes[node]['entity_type'] = node_attributes['Entity_Type'].get(node, 'Unknown')
            G.nodes[node]['sector'] = node_attributes['Sector'].get(node, 'Unknown')
        else:
            G.nodes[node]['total_occurrences'] = 0
            G.nodes[node]['entity_type'] = 'Unknown'
            G.nodes[node]['sector'] = 'Unknown'
    
    return G


def detect_louvain_communities(G):
    """Detect Louvain communities"""
    if G.number_of_nodes() == 0:
        return {}
    
    try:
        import networkx.algorithms.community as nx_comm
        communities = list(nx_comm.louvain_communities(G, seed=42, resolution=1.0))
    except Exception:
        communities = list(nx.connected_components(G))
    
    node_community = {}
    for idx, community in enumerate(communities):
        for node in community:
            node_community[node] = idx
    return node_community


def is_rdif_core(node_name):
    """Check if node is RDIF core (Dmitriev, RDIF, etc.)"""
    if node_name is None or (isinstance(node_name, float) and pd.isna(node_name)):
        return False
    s = str(node_name).lower()
    return any(kw in s for kw in RDIF_KEYWORDS)


def create_louvain_visualizations(output_dir='final visuals'):
    """Create Louvain community visualizations for all periods"""
    
    print("Creating Louvain community visualizations...")
    
    period_files = {
        'Pre-Crimea': 'data/periods/pre_crimea.csv',
        'Post-Crimea': 'data/periods/post_crimea.csv',
        'COVID': 'data/periods/covid.csv',
        'War': 'data/periods/war.csv'
    }
    
    # Colors: RDIF Core (red), New entities (green), Continuing entities (blue)
    COLOR_RDIF_CORE = '#e74c3c'
    COLOR_NEW = '#2ecc71'
    COLOR_CONTINUING = '#3498db'
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Load Pre-Crimea baseline (same edge weight as viz)
    min_edge = 120
    pre_crimea_path = period_files['Pre-Crimea']
    if not os.path.exists(pre_crimea_path):
        print("⚠ Pre-Crimea data not found. Cannot define baseline.")
        return
    
    G_baseline = create_network_from_csv(pre_crimea_path, min_edge_weight=min_edge)
    baseline_nodes = set(G_baseline.nodes())
    print(f"Baseline (Pre-Crimea, edge ≥ {min_edge}): {len(baseline_nodes)} nodes")
    
    for period_name, file_path in period_files.items():
        if not os.path.exists(file_path):
            print(f"⚠ Warning: {file_path} not found, skipping...")
            continue
        
        try:
            print(f"\nProcessing {period_name}...")
            G = create_network_from_csv(file_path, min_edge_weight=min_edge)
            
            if G.number_of_nodes() == 0:
                print(f"  No nodes in network, skipping...")
                continue
            
            node_community = detect_louvain_communities(G)
            current_nodes = set(G.nodes())
            
            # Classify each node: RDIF Core (red) | New (green) | Continuing (blue)
            node_colors = []
            for node in G.nodes():
                if is_rdif_core(node):
                    node_colors.append(COLOR_RDIF_CORE)
                elif period_name == 'Pre-Crimea':
                    # Baseline: no "new"; all non-RDIF are continuing
                    node_colors.append(COLOR_CONTINUING)
                elif node in baseline_nodes:
                    node_colors.append(COLOR_CONTINUING)
                else:
                    node_colors.append(COLOR_NEW)
            
            # Node sizes by degree
            degrees = dict(G.degree())
            max_degree = max(degrees.values()) if degrees else 1
            node_sizes = [300 + (degrees[node] / max_degree) * 700 for node in G.nodes()]
            
            pos = nx.spring_layout(G, k=1.5, iterations=50, seed=42)
            
            fig, ax = plt.subplots(figsize=(16, 12))
            fig.patch.set_facecolor('white')
            ax.set_facecolor('white')
            
            nx.draw_networkx_edges(G, pos, edge_color='#cccccc', width=0.5, alpha=0.4, ax=ax)
            nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes,
                                  alpha=0.9, edgecolors='white', linewidths=1.5, ax=ax)
            # No name labels
            
            ax.set_title(f"{period_name} Period\nSemantic Community Structure (Edge weight ≥ {min_edge})",
                        fontsize=14, fontweight='bold', pad=20)
            
            # Color legend: RDIF Core (red), New (green), Continuing (blue)
            legend_elements = [
                mpatches.Patch(color=COLOR_RDIF_CORE, label='RDIF Core Network'),
                mpatches.Patch(color=COLOR_NEW, label='New entities joining the network'),
                mpatches.Patch(color=COLOR_CONTINUING, label='Continuing entities')
            ]
            ax.legend(handles=legend_elements, loc='upper right', fontsize=10,
                     frameon=True, fancybox=True)
            
            ax.axis('off')
            plt.tight_layout()
            
            period_slug = period_name.lower().replace('-', '_').replace(' ', '_')
            output_file = os.path.join(output_dir, f'louvain_community_{period_slug}.png')
            plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
            plt.savefig(output_file.replace('.png', '.pdf'), dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            n_rdif = sum(1 for n in G.nodes() if is_rdif_core(n))
            n_new = 0 if period_name == 'Pre-Crimea' else sum(1 for n in G.nodes() if n not in baseline_nodes and not is_rdif_core(n))
            n_cont = sum(1 for n in G.nodes() if (period_name == 'Pre-Crimea' or n in baseline_nodes) and not is_rdif_core(n))
            print(f"  ✓ Saved: {output_file}")
            print(f"  Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}, Communities: {len(set(node_community.values()))}")
            print(f"  RDIF Core: {n_rdif}, New: {n_new}, Continuing: {n_cont}")
            
        except Exception as e:
            print(f"  ✗ Error processing {period_name}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n✓ All Louvain community visualizations created!")


if __name__ == "__main__":
    create_louvain_visualizations()
