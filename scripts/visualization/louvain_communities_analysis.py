import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as mpatches
import pandas as pd
from networkx.algorithms import community

# Function to read CSV files, calculate edge weights, and create networks with edge weight filter
def create_network_from_csv(file_path, min_edge_weight=120):
    """Read CSV file and create network based on co-occurrence with edge weight filtering"""
    df = pd.read_csv(file_path)
    
    # Create co-occurrence matrix by grouping entities that appear in the same articles
    # Group by Article_ID and get list of entities per article
    article_entities = df.groupby('Article_ID')['Entity'].apply(list).reset_index()
    
    # Create edge list from co-occurrences
    edges = []
    edge_weights = {}
    
    for _, row in article_entities.iterrows():
        entities = row['Entity']
        # Create edges between all pairs of entities in the same article
        for i in range(len(entities)):
            for j in range(i + 1, len(entities)):
                entity1, entity2 = entities[i], entities[j]
                edge = tuple(sorted([entity1, entity2]))
                
                if edge in edge_weights:
                    edge_weights[edge] += 1
                else:
                    edge_weights[edge] = 1
    
    # Filter edges by minimum weight
    filtered_edges = [(e[0], e[1], w) for e, w in edge_weights.items() if w >= min_edge_weight]
    
    # Create network
    G = nx.Graph()
    G.add_weighted_edges_from(filtered_edges)
    
    # Add node attributes (entity type and total occurrences)
    node_attributes = df.groupby('Entity').agg({
        'Occurrences': 'sum',
        'Entity_Type': 'first'
    }).to_dict()
    
    for node in G.nodes():
        if node in node_attributes['Occurrences']:
            G.nodes[node]['total_occurrences'] = node_attributes['Occurrences'][node]
            G.nodes[node]['entity_type'] = node_attributes['Entity_Type'][node]
        else:
            G.nodes[node]['total_occurrences'] = 0
            G.nodes[node]['entity_type'] = 'UNKNOWN'
    
    return G

# Create networks for each period with higher threshold for ~50 nodes
print("Creating networks for each period...")
G_pre = create_network_from_csv('pre_crimea.csv', min_edge_weight=120)
G_post = create_network_from_csv('post_crimea.csv', min_edge_weight=120)
G_covid = create_network_from_csv('covid.csv', min_edge_weight=120)
G_war = create_network_from_csv('war.csv', min_edge_weight=120)

print(f"Network sizes (nodes, edges):")
print(f"Pre-Crimea: ({G_pre.number_of_nodes()}, {G_pre.number_of_edges()})")
print(f"Post-Crimea: ({G_post.number_of_nodes()}, {G_post.number_of_edges()})")
print(f"Covid: ({G_covid.number_of_nodes()}, {G_covid.number_of_edges()})")
print(f"War: ({G_war.number_of_nodes()}, {G_war.number_of_edges()})")

# Define academic color palettes for communities
def get_community_colors(num_communities):
    """Generate distinct academic colors for communities"""
    # Use more professional color schemes
    if num_communities <= 8:
        colors = plt.cm.Dark2(np.linspace(0, 1, num_communities))
    else:
        colors = plt.cm.tab20(np.linspace(0, 1, num_communities))
    return colors

def detect_louvain_communities(G):
    """Detect Louvain communities and return community mapping"""
    if G.number_of_nodes() == 0:
        return {}
    
    communities = community.greedy_modularity_communities(G, weight='weight')
    
    # Create mapping from node to community
    node_to_community = {}
    for i, comm in enumerate(communities):
        for node in comm:
            node_to_community[node] = i
    
    return node_to_community, len(communities)

def draw_labels_with_background(G, pos, ax, font_size=8):
    """Academic-style labels with smart positioning to avoid overlap"""
    import math
    
    # Sort nodes by degree centrality for priority labeling
    degree_centrality = nx.degree_centrality(G)
    sorted_nodes = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)
    
    # Track label positions to avoid overlap
    label_positions = []
    min_distance = 0.15  # Minimum distance between labels
    
    for node, centrality in sorted_nodes:
        if node in pos:
            x, y = pos[node]
            
            # Clean academic labeling
            label = str(node)[:12] + "..." if len(str(node)) > 12 else str(node)
            
            # Find best position for label (try different offsets)
            offsets = [
                (0, -0.15),     # Below node
                (0, 0.15),      # Above node  
                (0.15, 0),      # Right of node
                (-0.15, 0),     # Left of node
                (0.1, -0.1),    # Bottom-right
                (-0.1, -0.1),   # Bottom-left
                (0.1, 0.1),     # Top-right
                (-0.1, 0.1),    # Top-left
            ]
            
            best_pos = None
            for dx, dy in offsets:
                test_x, test_y = x + dx, y + dy
                
                # Check if this position conflicts with existing labels
                conflict = False
                for prev_x, prev_y in label_positions:
                    distance = math.sqrt((test_x - prev_x)**2 + (test_y - prev_y)**2)
                    if distance < min_distance:
                        conflict = True
                        break
                
                if not conflict:
                    best_pos = (test_x, test_y)
                    break
            
            # Use best position or fallback to below node
            if best_pos:
                label_x, label_y = best_pos
            else:
                label_x, label_y = x, y - 0.15
            
            # Draw label
            ax.text(label_x, label_y, s=label, fontsize=font_size, fontfamily='serif',
                   ha='center', va='center', color='black', weight='normal',
                   bbox=dict(facecolor='white', edgecolor='black', alpha=0.9, 
                           boxstyle='round,pad=0.15', linewidth=0.5))
            
            # Record this label position
            label_positions.append((label_x, label_y))

def draw_louvain_network(ax, G, period_name, title):
    """Academic-style network with Louvain communities"""
    
    if G.number_of_nodes() == 0:
        ax.text(0.5, 0.5, f"Insufficient network data\n(minimum edge weight: 120)", 
               ha='center', va='center', transform=ax.transAxes, fontsize=14,
               fontfamily='serif')
        ax.set_title(title, fontsize=16, fontweight='normal', pad=20, fontfamily='serif')
        ax.axis('off')
        return
    
    # Detect communities
    node_to_community, num_communities = detect_louvain_communities(G)
    
    # Get academic community colors
    community_colors = get_community_colors(num_communities)
    
    # Academic layout with better spacing
    pos = nx.spring_layout(G, k=2.5, iterations=100, seed=42, weight='weight')
    
    # Draw edges with academic styling
    edge_weights = [G[u][v]['weight'] for u, v in G.edges()]
    max_weight = max(edge_weights) if edge_weights else 1
    # Conservative edge thickness for academic presentation
    normalized_weights = [w/max_weight * 3 + 0.3 for w in edge_weights]
    
    nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.6, width=normalized_weights, 
                          edge_color='#696969')  # Dim gray
    
    # Draw nodes colored by community
    node_colors = [community_colors[node_to_community[node]] for node in G.nodes()]
    
    # Conservative node sizing for academic presentation
    node_sizes = []
    for node in G.nodes():
        total_occ = G.nodes[node].get('total_occurrences', 0)
        size = max(250, min(1000, total_occ * 1.5))  # More conservative sizing
        node_sizes.append(size)
    
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, ax=ax, 
                          node_size=node_sizes, alpha=0.9, 
                          linewidths=1.5, edgecolors='black')
    
    # Academic labels for important nodes only
    draw_labels_with_background(G, pos, ax, font_size=9)
    
    # Academic community legend
    legend_elements = []
    for i in range(num_communities):
        legend_elements.append(mpatches.Patch(color=community_colors[i], 
                                            label=f'Community {i+1}'))
    
    if num_communities <= 12:  # Show legend for reasonable number of communities
        legend = ax.legend(handles=legend_elements, loc='upper left', fontsize=10, 
                          framealpha=1.0, fancybox=False, edgecolor='black',
                          ncol=2 if num_communities > 6 else 1)
        # Set serif font for legend
        for text in legend.get_texts():
            text.set_fontfamily('serif')
    
    # Academic title styling
    ax.set_title(title, fontsize=16, fontweight='normal', pad=20, fontfamily='serif')
    ax.axis('off')

# Function to create individual community graphs
def create_community_graph(period_name, save_path=None):
    """Create and optionally save individual period community graph"""
    fig, ax = plt.subplots(1, 1, figsize=(20, 16))
    
    # Get the appropriate graph and data
    graphs = {'pre_crimea': G_pre, 'post_crimea': G_post, 'covid': G_covid, 'war': G_war}
    titles = {
        'pre_crimea': 'Pre-Crimea Period (2012-2014)\nLouvain Community Structure (Edge Weight ≥120)', 
        'post_crimea': 'Post-Crimea Period (2014-2017)\nLouvain Community Structure (Edge Weight ≥120)', 
        'covid': 'COVID-19 Period (2020-2022)\nLouvain Community Structure (Edge Weight ≥120)', 
        'war': 'Ukraine War Period (2022-2024)\nLouvain Community Structure (Edge Weight ≥120)'
    }
    
    draw_louvain_network(ax, graphs[period_name], period_name, titles[period_name])
    
    plt.tight_layout()
    
    if save_path:
        # Save both PNG and PDF for academic use
        png_path = save_path
        pdf_path = save_path.replace('.png', '.pdf')
        plt.savefig(png_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
        plt.savefig(pdf_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
        print(f"Saved: {png_path} and {pdf_path}")
    
    plt.show()

# Create all four community graphs
print("\nGenerating Louvain community graphs...")
create_community_graph('pre_crimea', 'pre_crimea_communities.png')
create_community_graph('post_crimea', 'post_crimea_communities.png')
create_community_graph('covid', 'covid_communities.png')
create_community_graph('war', 'war_communities.png')

# Print summary statistics
print("\nCommunity Detection Summary:")
print("=" * 50)

for period_name, G in [('Pre-Crimea', G_pre), ('Post-Crimea', G_post), ('COVID', G_covid), ('War', G_war)]:
    if G.number_of_nodes() > 0:
        node_to_community, num_communities = detect_louvain_communities(G)
        modularity_score = community.modularity(G, [set(c) for c in community.greedy_modularity_communities(G, weight='weight')])
        
        print(f"\n{period_name}:")
        print(f"  Nodes: {G.number_of_nodes()}")
        print(f"  Edges: {G.number_of_edges()}")
        print(f"  Communities: {num_communities}")
        print(f"  Modularity: {modularity_score:.3f}")
        
        # Show largest communities
        comm_sizes = {}
        for node, comm in node_to_community.items():
            comm_sizes[comm] = comm_sizes.get(comm, 0) + 1
        
        sorted_comms = sorted(comm_sizes.items(), key=lambda x: x[1], reverse=True)
        print(f"  Largest communities: {[f'C{c+1}({s})' for c, s in sorted_comms[:5]]}")
    else:
        print(f"\n{period_name}: No network (insufficient edge weights ≥120)")

print("\nDone!")
