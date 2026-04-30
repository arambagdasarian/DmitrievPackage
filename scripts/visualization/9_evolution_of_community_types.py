"""
Evolution of Community Types Visualization

Shows how different community types (RDIF Core, Financial Network, Mixed Network, etc.)
evolve across periods.
"""

import os
import sys
import networkx as nx
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from date_utils import parse_dates_vectorized, assign_period_vectorized


def create_network_from_period_data(df, min_edge_weight=20):
    """Create network from period-filtered dataframe"""
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
    
    # Add node attributes
    node_attributes = df.groupby('Entity').agg({
        'Occurrences': 'sum',
        'Entity_Type': 'first',
        'Sector': 'first'
    }).to_dict()
    
    for node in G.nodes():
        if node in node_attributes['Occurrences']:
            G.nodes[node]['total_occurrences'] = node_attributes['Occurrences'][node]
            G.nodes[node]['entity_type'] = node_attributes['Entity_Type'][node]
            G.nodes[node]['sector'] = node_attributes['Sector'][node] if pd.notna(node_attributes['Sector'][node]) else 'Unknown'
        else:
            G.nodes[node]['total_occurrences'] = 0
            G.nodes[node]['entity_type'] = 'Unknown'
            G.nodes[node]['sector'] = 'Unknown'
    
    return G


def classify_community_type(community_nodes, G):
    """Classify a community based on its nodes"""
    if len(community_nodes) == 0:
        return 'Unknown'
    
    # Get attributes of nodes in community
    entity_types = [G.nodes[node].get('entity_type', 'Unknown') for node in community_nodes]
    sectors = [G.nodes[node].get('sector', 'Unknown') for node in community_nodes]
    
    # Check for RDIF core
    rdif_keywords = ['дмитриев', 'рфпи', 'rdif', 'российский фонд прямых инвестиций']
    if any(any(keyword in node.lower() for keyword in rdif_keywords) for node in community_nodes):
        return 'RDIF Core'
    
    # Count sector distribution
    sector_counts = Counter([s for s in sectors if s != 'Unknown'])
    total_known = sum(sector_counts.values())
    
    if total_known > 0:
        # Check for finance-dominant communities (>35% threshold)
        finance_count = sector_counts.get('Finance', 0)
        if finance_count / total_known > 0.35:
            return 'Finance'
        
        # Check for government-dominant communities (>40% threshold)
        gov_count = sector_counts.get('Government', 0)
        if gov_count / total_known > 0.40:
            return 'Government'
        
        # Check for health communities (>30% threshold)
        health_count = sector_counts.get('Health', 0)
        if health_count / total_known > 0.30:
            return 'Health'
        
        # Check for diplomacy communities (>25% threshold)
        diplomacy_count = sector_counts.get('Diplomacy', 0)
        if diplomacy_count / total_known > 0.25:
            return 'Diplomacy'
    
    # If no single sector dominates, classify by entity type
    entity_type_counts = Counter(entity_types)
    most_common_type = entity_type_counts.most_common(1)[0][0] if entity_type_counts else 'Unknown'
    
    if most_common_type == 'ORG':
        return 'Mixed (Organizations)'
    elif most_common_type == 'PER':
        return 'Mixed (Persons)'
    
    return 'Mixed'


def detect_louvain_communities(G):
    """Detect Louvain communities"""
    if G.number_of_nodes() == 0:
        return []
    
    try:
        import networkx.algorithms.community as nx_comm
        communities = list(nx_comm.louvain_communities(G, seed=42, resolution=1.0))
    except:
        # Fallback to connected components
        communities = list(nx.connected_components(G))
    
    return communities


def create_community_types_evolution(output_dir='final visuals'):
    """Create Evolution of Community Types visualization"""
    
    print("Creating Evolution of Community Types visualization...")
    
    # Use the four period CSVs from data/periods
    period_files = {
        'Pre-Crimea': 'data/periods/pre_crimea.csv',
        'Post-Crimea': 'data/periods/post_crimea.csv',
        'COVID': 'data/periods/covid.csv',
        'War': 'data/periods/war.csv',
    }
    
    period_names = ['Pre-Crimea', 'Post-Crimea', 'COVID', 'War']
    periods = []
    community_type_counts = {}
    
    for period_name in period_names:
        file_path = period_files.get(period_name)
        if not os.path.exists(file_path):
            print(f"⚠ Warning: {file_path} not found, skipping...")
            continue
            
        try:
            # Load period-specific CSV
            period_df = pd.read_csv(file_path)
            
            if len(period_df) == 0:
                print(f"⚠ {period_name}: No data, skipping...")
                continue
            
            G = create_network_from_period_data(period_df, min_edge_weight=20)
            if G.number_of_nodes() == 0:
                print(f"⚠ {period_name}: No nodes, skipping...")
                continue
            
            communities = detect_louvain_communities(G)
            periods.append(period_name)
            
            # Classify each community
            type_counts = Counter()
            for community in communities:
                comm_type = classify_community_type(list(community), G)
                type_counts[comm_type] += 1
            
            community_type_counts[period_name] = type_counts
            print(f"✓ {period_name}: {len(communities)} communities")
            for comm_type, count in type_counts.items():
                print(f"    {comm_type}: {count}")
        except Exception as e:
            print(f"✗ Error processing {period_name}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    if not periods:
        print("❌ No period data loaded. Cannot create visualization.")
        return
    
    # Get all community types
    all_types = set()
    for type_counts in community_type_counts.values():
        all_types.update(type_counts.keys())
    
    # Create visualization
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('white')
    
    # Color mapping for community types
    type_colors = {
        'RDIF Core': '#2ecc71',           # Green
        'Finance': '#3498db',              # Blue
        'Government': '#f39c12',           # Orange
        'Health': '#e74c3c',               # Red
        'Diplomacy': '#9b59b6',            # Purple
        'Mixed (Organizations)': '#16a085', # Teal
        'Mixed (Persons)': '#d35400',      # Dark orange
        'Mixed': '#95a5a6'                 # Gray
    }
    
    # Plot lines for each community type
    for comm_type in sorted(all_types):
        values = [community_type_counts.get(p, Counter()).get(comm_type, 0) for p in periods]
        color = type_colors.get(comm_type, '#95a5a6')
        
        ax.plot(periods, values, marker='o', linewidth=2.5, markersize=8,
               label=comm_type, color=color, alpha=0.9)
    
    ax.set_xlabel('Period', fontsize=12, fontweight='bold')
    ax.set_ylabel('Count', fontsize=12, fontweight='bold')
    ax.set_title('Evolution of Community Types', fontsize=14, fontweight='bold', pad=15)
    ax.set_ylim(bottom=0)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='best', fontsize=10, frameon=True, fancybox=True, ncol=2)
    
    plt.tight_layout()
    
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'evolution_of_community_types.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.savefig(output_file.replace('.png', '.pdf'), dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"✓ Saved: {output_file}")
    
    # Print summary
    print("\n" + "="*60)
    print("Community Types Summary:")
    print("="*60)
    for period in periods:
        print(f"\n{period}:")
        for comm_type, count in community_type_counts[period].most_common():
            print(f"  {comm_type}: {count}")
    
    return fig


if __name__ == "__main__":
    create_community_types_evolution()
