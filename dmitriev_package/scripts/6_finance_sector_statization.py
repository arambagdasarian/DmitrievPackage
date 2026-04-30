"""
Finance Sector Statization Visualization

Shows State vs Private percentage within Finance sector only.
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


def create_finance_statization_visualization(output_dir='final visuals'):
    """Create Finance Sector Statization visualization"""
    
    print("Creating Finance Sector Statization visualization...")

    # Use the four period CSVs from data/periods
    period_files = {
        'Pre-Crimea': 'data/periods/pre_crimea.csv',
        'Post-Crimea': 'data/periods/post_crimea.csv',
        'COVID': 'data/periods/covid.csv',
        'War': 'data/periods/war.csv',
    }

    periods = ['Pre-Crimea', 'Post-Crimea', 'COVID', 'War']
    period_stats = {}

    for period_name in periods:
        file_path = period_files.get(period_name)
        if not os.path.exists(file_path):
            print(f"⚠ Warning: {file_path} not found for {period_name}, skipping...")
            continue

        df = pd.read_csv(file_path)
        
        # Create network with min_edge_weight=20
        G = create_network_from_csv(file_path, min_edge_weight=20)
        network_nodes = set(G.nodes())
        
        # Filter for Finance sector entities that are IN THE NETWORK
        df = df[['Entity', 'Sector', 'State/Private']].copy()
        df = df[(df['Sector'] == 'Finance') & (df['Entity'].isin(network_nodes))].copy()
        df = df[df['State/Private'].isin(['State', 'Private'])].copy()  # Only pure State/Private
        df = df.drop_duplicates(subset=['Entity'])

        if len(df) == 0:
            continue

        state_private_counts = df['State/Private'].value_counts()
        total = state_private_counts.sum()

        if total > 0:
            percentages = (state_private_counts / total * 100)
            period_stats[period_name] = {
                'State': percentages.get('State', 0),
                'Private': percentages.get('Private', 0)
            }
            print(f"✓ {period_name}: State={percentages.get('State', 0):.1f}%, Private={percentages.get('Private', 0):.1f}% ({int(total)} finance entities in network)")
    
    # Create visualization (GROUPED bar chart, not stacked)
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('white')
    
    state_values = [period_stats.get(p, {}).get('State', 0) for p in periods]
    private_values = [period_stats.get(p, {}).get('Private', 0) for p in periods]
    
    x = range(len(periods))
    width = 0.35  # Width of each bar
    
    # Create grouped bars - State (red) and Private (green) side by side
    bars1 = ax.bar([i - width/2 for i in x], state_values, width, 
                   label='State', color='#e74c3c', alpha=0.9, edgecolor='black', linewidth=1.5)
    bars2 = ax.bar([i + width/2 for i in x], private_values, width,
                   label='Private', color='#2ecc71', alpha=0.9, edgecolor='black', linewidth=1.5)
    
    ax.set_xlabel('Period', fontsize=12, fontweight='bold')
    ax.set_ylabel('Percentage (%)', fontsize=12, fontweight='bold')
    ax.set_title('Finance Sector Statization', fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(periods)
    ax.set_ylim(0, 100)
    ax.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax.legend(loc='upper left', fontsize=11, frameon=True, fancybox=True)
    
    # Add value labels on top of bars
    for i, (bar, val) in enumerate(zip(bars1, state_values)):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                   f'{val:.1f}%', ha='center', va='bottom', 
                   fontsize=10, fontweight='bold')
    
    for i, (bar, val) in enumerate(zip(bars2, private_values)):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                   f'{val:.1f}%', ha='center', va='bottom', 
                   fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'finance_sector_statization.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.savefig(output_file.replace('.png', '.pdf'), dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"✓ Saved: {output_file}")
    return fig


if __name__ == "__main__":
    create_finance_statization_visualization()
