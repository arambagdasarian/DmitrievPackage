"""
Network Consolidation Ratio Visualization

Shows State:Private ratio across periods using network weighted degree.
"""

import os
import sys
import pandas as pd
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


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
    
    return G


def create_consolidation_ratio_visualization(output_dir='final visuals'):
    """Create Network Consolidation Ratio visualization"""
    
    print("Creating Network Consolidation Ratio visualization...")

    # Use the four period CSVs from data/periods
    period_files = {
        'Pre-Crimea': 'data/periods/pre_crimea.csv',
        'Post-Crimea': 'data/periods/post_crimea.csv',
        'COVID': 'data/periods/covid.csv',
        'War': 'data/periods/war.csv',
    }

    periods = ['Pre-Crimea', 'Post-Crimea', 'COVID', 'War']
    ratios = []
    colors = ['#3498db', '#9b59b6', '#f39c12', '#e74c3c']
    
    for period_name in periods:
        file_path = period_files.get(period_name)
        if not os.path.exists(file_path):
            print(f"⚠ Warning: {file_path} not found, skipping...")
            ratios.append(0)
            continue

        df = pd.read_csv(file_path)
        
        # Create network with min_edge_weight=20
        G = create_network_from_csv(file_path, min_edge_weight=20)
        
        if G.number_of_nodes() == 0:
            ratios.append(0)
            continue
        
        # Get State/Private classification
        entity_classification = df[['Entity', 'State/Private']].dropna(subset=['State/Private']).drop_duplicates(subset=['Entity'])
        entity_dict = dict(zip(entity_classification['Entity'], entity_classification['State/Private']))
        
        # Calculate weighted degree for each node in the network
        weighted_degrees = {}
        for node in G.nodes():
            # Weighted degree = sum of weights of all edges connected to this node
            weighted_degree = sum(G[node][neighbor]['weight'] for neighbor in G.neighbors(node))
            weighted_degrees[node] = weighted_degree
        
        # Classify nodes by State/Private
        state_degrees = []
        private_degrees = []
        
        for entity, degree in weighted_degrees.items():
            classification = entity_dict.get(entity)
            if classification == 'State':
                state_degrees.append(degree)
            elif classification == 'Private':
                private_degrees.append(degree)
        
        # Calculate ratio of total weighted degrees
        state_total_degree = sum(state_degrees) if state_degrees else 0
        private_total_degree = sum(private_degrees) if private_degrees else 0
        
        if private_total_degree > 0:
            ratio = state_total_degree / private_total_degree
            ratios.append(ratio)
            print(f"✓ {period_name}: {ratio:.1f}:1 (State: {int(state_total_degree):,} / Private: {int(private_total_degree):,} weighted degree)")
        else:
            ratios.append(0)
    
    # Create visualization (bar chart)
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('white')
    
    bars = ax.bar(periods, ratios, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    
    ax.set_xlabel('Period', fontsize=12, fontweight='bold')
    ax.set_ylabel('State:Private Ratio', fontsize=12, fontweight='bold')
    ax.set_title('Network Consolidation Ratio', fontsize=14, fontweight='bold', pad=15)
    ax.set_ylim(0, 20)  # Adjusted to fit expected range
    ax.grid(True, alpha=0.3, linestyle='--', axis='y')
    
    # Add value labels on bars
    for i, (bar, ratio) in enumerate(zip(bars, ratios)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.2,
               f'{ratio:.1f}:1', ha='center', va='bottom', 
               fontsize=11, fontweight='bold')
    
    plt.tight_layout()
    
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'network_consolidation_ratio.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.savefig(output_file.replace('.png', '.pdf'), dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"✓ Saved: {output_file}")
    return fig


if __name__ == "__main__":
    create_consolidation_ratio_visualization()
