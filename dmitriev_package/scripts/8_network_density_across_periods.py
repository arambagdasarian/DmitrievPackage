"""
Network Density Across Periods Visualization

Shows network density evolution across periods.
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


def create_network_density_visualization(output_dir='final visuals'):
    """Create Network Density Across Periods visualization"""
    
    print("Creating Network Density Across Periods visualization...")
    
    period_files = {
        'Pre-Crimea': 'data/periods/pre_crimea.csv',
        'Post-Crimea': 'data/periods/post_crimea.csv',
        'COVID': 'data/periods/covid.csv',
        'War': 'data/periods/war.csv'
    }
    
    periods = []
    densities = []
    
    for period_name, file_path in period_files.items():
        if not os.path.exists(file_path):
            print(f"⚠ Warning: {file_path} not found, skipping...")
            continue
        
        try:
            G = create_network_from_csv(file_path, min_edge_weight=20)
            if G.number_of_nodes() > 0:
                density = nx.density(G)
                periods.append(period_name)
                densities.append(density)
                print(f"✓ {period_name}: density = {density:.4f}")
            else:
                print(f"⚠ {period_name}: No nodes, skipping...")
        except Exception as e:
            print(f"✗ Error loading {period_name}: {e}")
            continue
    
    if not periods:
        print("❌ No period data loaded. Cannot create visualization.")
        return
    
    # Create visualization
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('white')
    
    # Use a single consistent purple color like the reference
    bars = ax.bar(periods, densities, color='#9b59b6', 
                  alpha=0.7, edgecolor='none', width=0.6)
    
    ax.set_xlabel('Period', fontsize=12, fontweight='bold')
    ax.set_ylabel('Network Density', fontsize=12, fontweight='bold')
    ax.set_title('Network Density Across Periods', fontsize=14, fontweight='bold', pad=15)
    ax.set_ylim(0, 0.08)  # Set reasonable y-axis limit
    ax.grid(True, alpha=0.3, linestyle='--', axis='y')
    
    # Add value labels on bars
    for bar, density in zip(bars, densities):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.002,
               f'{density:.3f}', ha='center', va='bottom', 
               fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'network_density_across_periods.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.savefig(output_file.replace('.png', '.pdf'), dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"✓ Saved: {output_file}")
    
    # Print summary
    print("\n" + "="*60)
    print("Network Density Summary:")
    print("="*60)
    for period, density in zip(periods, densities):
        print(f"{period}: {density:.4f}")
    
    return fig


if __name__ == "__main__":
    create_network_density_visualization()
