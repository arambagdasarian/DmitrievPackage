#!/usr/bin/env python3
"""
Network Clustering Analysis
Creates visualizations for Louvain communities and attribute-based clustering
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
import numpy as np
from collections import Counter, defaultdict
import warnings
warnings.filterwarnings('ignore')

print("Loading network data...")
with open('network_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

nodes = data['nodes']
edges = data['edges']

PERIODS = ['Pre-Crimea', 'Post-Crimea', 'COVID', 'War']

# ============================================================================
# ANALYSIS 5: LOUVAIN COMMUNITIES WITH ATTRIBUTES
# ============================================================================
print("\n" + "="*80)
print("ANALYSIS 5: Louvain Communities with Attribute Labels")
print("="*80)

def load_louvain_data(period):
    """Load Louvain community data if available"""
    try:
        communities_file = f'Louvains sets/{period.lower()}_communities.csv'
        df = pd.read_csv(communities_file)
        return df
    except FileNotFoundError:
        print(f"  ⚠ Community file not found for {period}")
        return None

def create_louvain_visualizations():
    """Create visualizations of Louvain communities with attribute labels"""
    
    for period in PERIODS:
        print(f"\nAnalyzing {period}...")
        
        # Load community data
        comm_df = load_louvain_data(period)
        if comm_df is None:
            continue
        
        # Get period nodes
        period_nodes = [n for n in nodes if period in n['periods']]
        node_dict = {n['id']: n for n in period_nodes}
        
        # Create networkx graph
        G = nx.Graph()
        
        # Add nodes with attributes
        for node in period_nodes:
            G.add_node(node['id'], 
                      label=node['label'],
                      sector=node['sector'],
                      state_private=node['state_private'],
                      actor_type=node['actor_type'],
                      jurisdiction=node['jurisdiction'],
                      mentions=node['period_counts'].get(period, 0))
        
        # Add edges
        for edge in edges:
            if period in edge.get('periods', []):
                source_id = edge['source'] if isinstance(edge['source'], str) else edge['source']['id']
                target_id = edge['target'] if isinstance(edge['target'], str) else edge['target']['id']
                
                if source_id in node_dict and target_id in node_dict:
                    G.add_edge(source_id, target_id, weight=edge.get('weight', 1))
        
        print(f"  Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        
        # Compute Louvain communities
        from networkx.algorithms import community
        communities = community.louvain_communities(G, seed=42)
        
        # Assign community to each node
        node_community = {}
        for i, comm in enumerate(communities):
            for node_id in comm:
                node_community[node_id] = i
        
        # Analyze community composition
        community_stats = []
        
        for i, comm in enumerate(communities):
            if len(comm) < 3:  # Skip very small communities
                continue
            
            comm_nodes = [node_dict[nid] for nid in comm if nid in node_dict]
            
            sectors = Counter([n['sector'] for n in comm_nodes])
            state_private = Counter([n['state_private'] for n in comm_nodes])
            actor_types = Counter([n['actor_type'] for n in comm_nodes])
            jurisdictions = Counter([n['jurisdiction'] for n in comm_nodes])
            
            # Get top entities
            top_entities = sorted(comm_nodes, 
                                 key=lambda x: x['period_counts'].get(period, 0), 
                                 reverse=True)[:5]
            
            community_stats.append({
                'community': i,
                'size': len(comm),
                'top_sector': sectors.most_common(1)[0][0] if sectors else 'N/A',
                'top_state_private': state_private.most_common(1)[0][0] if state_private else 'N/A',
                'top_actor_type': actor_types.most_common(1)[0][0] if actor_types else 'N/A',
                'dominant_sector_pct': sectors.most_common(1)[0][1] / len(comm) * 100 if sectors else 0,
                'top_entities': ', '.join([f"{e['label'][:30]} ({e['sector']}, {e['state_private']})" 
                                          for e in top_entities[:3]])
            })
        
        stats_df = pd.DataFrame(community_stats)
        stats_df.to_csv(f'visuals/5_louvain_communities_{period}.csv', index=False)
        print(f"  ✓ Saved community stats: visuals/5_louvain_communities_{period}.csv")
        
        # Visualize network with communities colored by sector
        fig, axes = plt.subplots(2, 2, figsize=(24, 24))
        fig.suptitle(f'{period}: Louvain Communities Colored by Attributes', 
                     fontsize=20, fontweight='bold')
        
        attributes = ['sector', 'state_private', 'actor_type', 'jurisdiction']
        axes = axes.flatten()
        
        # Use spring layout for consistent positioning
        pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
        
        # Color schemes
        sector_colors = {'Finance': '#667eea', 'Government': '#f6ad55', 'Health': '#48bb78',
                        'Diplomacy': '#ed64a6', 'Energy': '#fc8181', 'Tech': '#4299e1',
                        'Business': '#9f7aea', 'Education': '#38b2ac', 'Production': '#ed8936',
                        'Infrastructure': '#ecc94b', 'Military': '#e53e3e', 
                        'Telecommunication': '#805ad5', 'Politics': '#d69e2e', 'Unknown': '#718096'}
        
        for idx, attr in enumerate(attributes):
            ax = axes[idx]
            
            # Get unique values and create color map
            values = list(set([G.nodes[n][attr] for n in G.nodes()]))
            
            if attr == 'sector':
                color_map = sector_colors
            else:
                palette = sns.color_palette("husl", len(values))
                color_map = dict(zip(values, palette))
            
            # Assign colors
            node_colors = [color_map.get(G.nodes[n][attr], '#718096') for n in G.nodes()]
            
            # Draw network
            nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.2, width=0.5)
            nx.draw_networkx_nodes(G, pos, ax=ax, 
                                  node_color=node_colors,
                                  node_size=[np.sqrt(G.nodes[n]['mentions']) * 2 for n in G.nodes()],
                                  alpha=0.8)
            
            # Add labels for largest nodes
            top_nodes = sorted(G.nodes(), 
                             key=lambda n: G.nodes[n]['mentions'], 
                             reverse=True)[:10]
            labels = {n: G.nodes[n]['label'][:20] for n in top_nodes}
            nx.draw_networkx_labels(G, pos, labels, ax=ax, font_size=7)
            
            ax.set_title(f'Colored by {attr.replace("_", " ").title()}', 
                        fontsize=14, fontweight='bold')
            ax.axis('off')
            
            # Create legend
            legend_elements = [plt.Line2D([0], [0], marker='o', color='w', 
                                         markerfacecolor=color_map.get(val, '#718096'), 
                                         markersize=8, label=val)
                             for val in sorted(values)]
            ax.legend(handles=legend_elements, loc='upper left', fontsize=8)
        
        plt.tight_layout()
        plt.savefig(f'visuals/5_louvain_network_{period}.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Saved network visualization: visuals/5_louvain_network_{period}.png")

# ============================================================================
# ANALYSIS 6: ATTRIBUTE-BASED CLUSTERING
# ============================================================================
print("\n" + "="*80)
print("ANALYSIS 6: Attribute-Based Community Detection")
print("="*80)

def create_attribute_clusters():
    """Detect and visualize clusters based on attributes"""
    
    for period in PERIODS:
        print(f"\nAnalyzing {period}...")
        
        # Get period nodes
        period_nodes = [n for n in nodes if period in n['periods']]
        node_dict = {n['id']: n for n in period_nodes}
        
        # Create networkx graph
        G = nx.Graph()
        
        for node in period_nodes:
            G.add_node(node['id'], **node)
        
        for edge in edges:
            if period in edge.get('periods', []):
                source_id = edge['source'] if isinstance(edge['source'], str) else edge['source']['id']
                target_id = edge['target'] if isinstance(edge['target'], str) else edge['target']['id']
                
                if source_id in node_dict and target_id in node_dict:
                    G.add_edge(source_id, target_id, weight=edge.get('weight', 1))
        
        # Analyze clusters by each attribute
        attributes = ['sector', 'state_private', 'actor_type']
        
        fig, axes = plt.subplots(1, 3, figsize=(30, 10))
        fig.suptitle(f'{period}: Attribute-Based Clustering Analysis', 
                     fontsize=20, fontweight='bold')
        
        for idx, attr in enumerate(attributes):
            ax = axes[idx]
            
            # Group nodes by attribute
            attr_groups = defaultdict(list)
            for node_id in G.nodes():
                attr_value = G.nodes[node_id][attr]
                attr_groups[attr_value].append(node_id)
            
            # Calculate intra-cluster vs inter-cluster connections
            results = []
            
            for attr_value, group_nodes in attr_groups.items():
                if len(group_nodes) < 2:
                    continue
                
                # Create subgraph
                subgraph = G.subgraph(group_nodes)
                
                # Calculate metrics
                internal_edges = subgraph.number_of_edges()
                
                # Count external edges
                external_edges = 0
                for node in group_nodes:
                    for neighbor in G.neighbors(node):
                        if neighbor not in group_nodes:
                            external_edges += 1
                external_edges = external_edges // 2  # Each edge counted twice
                
                total_possible_internal = len(group_nodes) * (len(group_nodes) - 1) / 2
                density = internal_edges / total_possible_internal if total_possible_internal > 0 else 0
                
                # Average degree within cluster
                avg_degree = 2 * internal_edges / len(group_nodes) if len(group_nodes) > 0 else 0
                
                results.append({
                    'attribute_value': attr_value,
                    'size': len(group_nodes),
                    'internal_edges': internal_edges,
                    'external_edges': external_edges,
                    'density': density,
                    'avg_degree': avg_degree,
                    'modularity_indicator': internal_edges / (internal_edges + external_edges + 1)
                })
            
            results_df = pd.DataFrame(results).sort_values('modularity_indicator', ascending=False)
            
            # Visualize
            x = np.arange(len(results_df))
            width = 0.35
            
            ax2 = ax.twinx()
            
            bars1 = ax.bar(x - width/2, results_df['internal_edges'], width, 
                          label='Internal Edges', alpha=0.8, color='#2ecc71')
            bars2 = ax.bar(x + width/2, results_df['external_edges'], width, 
                          label='External Edges', alpha=0.8, color='#e74c3c')
            
            line = ax2.plot(x, results_df['modularity_indicator'] * 100, 
                           'o-', color='#3498db', linewidth=3, markersize=10,
                           label='Cohesion Score')
            
            ax.set_xlabel(f'{attr.replace("_", " ").title()}', fontsize=12, fontweight='bold')
            ax.set_ylabel('Number of Edges', fontsize=12, fontweight='bold')
            ax2.set_ylabel('Cohesion Score (%)', fontsize=12, fontweight='bold', color='#3498db')
            ax.set_title(f'Clustering by {attr.replace("_", " ").title()}', 
                        fontsize=14, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels(results_df['attribute_value'], rotation=45, ha='right')
            ax.legend(loc='upper left')
            ax2.legend(loc='upper right')
            ax.grid(True, alpha=0.3, axis='y')
            
            # Save detailed results
            results_df.to_csv(f'visuals/6_attribute_clusters_{attr}_{period}.csv', index=False)
        
        plt.tight_layout()
        plt.savefig(f'visuals/6_attribute_clustering_{period}.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Saved clustering analysis: visuals/6_attribute_clustering_{period}.png")
        
        # Create separate network visualizations for each major sector/attribute
        create_sector_specific_networks(G, period)

def create_sector_specific_networks(G, period):
    """Create detailed network visualizations for specific sectors"""
    
    # Focus on major sectors/groups
    sectors = set([G.nodes[n]['sector'] for n in G.nodes()])
    major_sectors = [s for s in sectors 
                    if sum(1 for n in G.nodes() if G.nodes[n]['sector'] == s) >= 5]
    
    if not major_sectors:
        return
    
    n_sectors = len(major_sectors)
    n_cols = 3
    n_rows = (n_sectors + n_cols - 1) // n_cols
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(24, 8*n_rows))
    fig.suptitle(f'{period}: Sector-Specific Network Clusters', 
                 fontsize=20, fontweight='bold')
    
    if n_rows == 1:
        axes = axes.reshape(1, -1)
    
    axes = axes.flatten()
    
    for idx, sector in enumerate(sorted(major_sectors)):
        if idx >= len(axes):
            break
        
        ax = axes[idx]
        
        # Get nodes in this sector
        sector_nodes = [n for n in G.nodes() if G.nodes[n]['sector'] == sector]
        
        # Create subgraph with neighbors
        neighbors = set(sector_nodes)
        for node in sector_nodes:
            neighbors.update(G.neighbors(node))
        
        subgraph = G.subgraph(neighbors)
        
        # Layout
        pos = nx.spring_layout(subgraph, k=1.5, iterations=50, seed=42)
        
        # Color by state/private
        colors = []
        for node in subgraph.nodes():
            if G.nodes[node]['sector'] == sector:
                if G.nodes[node]['state_private'] == 'State':
                    colors.append('#e74c3c')
                elif G.nodes[node]['state_private'] == 'Private':
                    colors.append('#3498db')
                else:
                    colors.append('#f39c12')
            else:
                colors.append('#95a5a6')
        
        # Draw
        nx.draw_networkx_edges(subgraph, pos, ax=ax, alpha=0.3, width=0.5)
        nx.draw_networkx_nodes(subgraph, pos, ax=ax,
                              node_color=colors,
                              node_size=[np.sqrt(G.nodes[n]['mentions']) * 3 
                                        for n in subgraph.nodes()],
                              alpha=0.7)
        
        # Label top nodes
        top_nodes = sorted([n for n in subgraph.nodes() if G.nodes[n]['sector'] == sector],
                          key=lambda n: G.nodes[n]['mentions'], 
                          reverse=True)[:5]
        labels = {n: G.nodes[n]['label'][:20] for n in top_nodes}
        nx.draw_networkx_labels(subgraph, pos, labels, ax=ax, font_size=7)
        
        ax.set_title(f'{sector} Cluster\n({len(sector_nodes)} entities, '
                    f'{subgraph.number_of_edges()} connections)',
                    fontsize=12, fontweight='bold')
        ax.axis('off')
        
        # Legend
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#e74c3c',
                      markersize=8, label='State'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#3498db',
                      markersize=8, label='Private'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#f39c12',
                      markersize=8, label='Mixed'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#95a5a6',
                      markersize=8, label='Other Sector')
        ]
        ax.legend(handles=legend_elements, loc='upper left', fontsize=7)
    
    # Hide empty subplots
    for idx in range(len(major_sectors), len(axes)):
        axes[idx].axis('off')
    
    plt.tight_layout()
    plt.savefig(f'visuals/6_sector_networks_{period}.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Saved sector networks: visuals/6_sector_networks_{period}.png")

# Run the analyses
import os
os.makedirs('visuals', exist_ok=True)

create_louvain_visualizations()
create_attribute_clusters()

print("\n" + "="*80)
print("✅ Network clustering analysis complete!")
print("="*80)



