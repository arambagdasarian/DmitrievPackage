"""
Network Size Evolution Visualization

Shows nodes and edges count across periods to verify post-Crimea period cut.
"""

import networkx as nx
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os


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
    
    # Filter for significant connections
    filtered_edges = [(e[0], e[1], w) for e, w in edge_weights.items() if w >= min_edge_weight]
    
    G = nx.Graph()
    G.add_weighted_edges_from(filtered_edges)
    
    return G


def create_network_size_evolution(output_dir='final visuals'):
    """Create Network Size Evolution visualization"""
    
    print("Creating Network Size Evolution visualization...")
    
    period_files = {
        'Pre-Crimea': 'data/periods/pre_crimea.csv',
        'Post-Crimea': 'data/periods/post_crimea.csv',
        'COVID': 'data/periods/covid.csv',
        'War': 'data/periods/war.csv'
    }
    
    periods = []
    node_counts = []
    edge_counts = []
    
    for period_name, file_path in period_files.items():
        if not os.path.exists(file_path):
            print(f"⚠ Warning: {file_path} not found, skipping...")
            continue
        
        try:
            G = create_network_from_csv(file_path, min_edge_weight=20)
            periods.append(period_name)
            node_counts.append(G.number_of_nodes())
            edge_counts.append(G.number_of_edges())
            print(f"✓ {period_name}: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        except Exception as e:
            print(f"✗ Error loading {period_name}: {e}")
            continue
    
    if not periods:
        print("❌ No period data loaded. Cannot create visualization.")
        return
    
    # Create visualization
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('white')
    
    x = np.arange(len(periods))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, node_counts, width, label='Nodes', 
                   color='#add8e6', alpha=0.6, edgecolor='none')
    bars2 = ax.bar(x + width/2, edge_counts, width, label='Edges', 
                   color='#ffb6c1', alpha=0.6, edgecolor='none')
    
    ax.set_xlabel('Period', fontsize=12, fontweight='bold')
    ax.set_ylabel('Count', fontsize=12, fontweight='bold')
    ax.set_title('Network Size Evolution', fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(periods)
    ax.legend(loc='upper right', fontsize=11, frameon=True, fancybox=True)
    ax.grid(True, alpha=0.3, linestyle='--', axis='y')
    
    plt.tight_layout()
    
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'network_size_evolution.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.savefig(output_file.replace('.png', '.pdf'), dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"✓ Saved: {output_file}")
    
    # Print summary
    print("\n" + "="*60)
    print("Network Size Summary:")
    print("="*60)
    for period, nodes, edges in zip(periods, node_counts, edge_counts):
        print(f"{period}: {nodes} nodes, {edges} edges")
    
    return fig


if __name__ == "__main__":
    create_network_size_evolution()
