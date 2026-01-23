import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as mpatches
import pandas as pd

# Function to read CSV files and calculate composite score, then get top 50 actors
def get_top_50_actors(file_path):
    """Read CSV file, calculate composite score from Occurrences, and return top 50 actors by composite score from Entity column"""
    df = pd.read_csv(file_path)
    
    # Calculate composite score by summing occurrences for each entity
    composite_scores = df.groupby('Entity')['Occurrences'].sum().reset_index()
    composite_scores.rename(columns={'Occurrences': 'CompositeScore'}, inplace=True)
    
    # Sort by composite score in descending order and take top 50
    df_top = composite_scores.sort_values('CompositeScore', ascending=False).head(50)
    
    # Return set of entity names (real actor names)
    return set(df_top['Entity'].astype(str))

# Read actual data from CSV files and get top 50 actors for each period
pre_crimea_actors = get_top_50_actors('pre_crimea.csv')
post_crimea_actors = get_top_50_actors('post_crimea.csv')
covid_actors = get_top_50_actors('covid.csv')
war_actors = get_top_50_actors('war.csv')

# Create network graphs for each period
def create_network_graph(actors_set, density=0.1, seed=42):
    """Create a network graph from a set of actors"""
    actors_list = list(actors_set)
    n_nodes = len(actors_list)
    
    # Create random graph structure (replace with your actual network data)
    G = nx.gnp_random_graph(n_nodes, density, seed=seed)
    
    # Map node indices to actor names (now real entity names)
    mapping = {i: actors_list[i] for i in range(n_nodes)}
    G = nx.relabel_nodes(G, mapping)
    
    return G

# Create graphs for each period
G_pre = create_network_graph(pre_crimea_actors, seed=1)
G_post = create_network_graph(post_crimea_actors, seed=2)
G_covid = create_network_graph(covid_actors, seed=3)
G_war = create_network_graph(war_actors, seed=4)

# Define color scheme for each period
colors = {
    'pre_crimea': 'black',
    'post_crimea': 'orange', 
    'covid': 'purple',
    'war': 'green'
}

def get_node_colors_and_lost_nodes(current_actors, period_name, all_periods_data):
    """
    Determine node colors based on when actors first appeared and identify lost nodes
    """
    node_colors = []
    lost_nodes = []
    
    # Get all previous periods up to current one
    period_order = ['pre_crimea', 'post_crimea', 'covid', 'war']
    current_index = period_order.index(period_name)
    
    # Determine color for each node based on when it first appeared
    for actor in current_actors:
        color_assigned = False
        for i in range(current_index + 1):
            period = period_order[i]
            if actor in all_periods_data[period]:
                node_colors.append(colors[period])
                color_assigned = True
                break
        if not color_assigned:
            node_colors.append(colors[period_name])  # Default to current period color
    
    # Find lost nodes from all previous periods
    if current_index > 0:
        all_previous_actors = set()
        for i in range(current_index):
            period = period_order[i]
            all_previous_actors.update(all_periods_data[period])
        lost_nodes = list(all_previous_actors - current_actors)
    
    return node_colors, lost_nodes

def draw_labels_with_white_shield(G, pos, ax, font_size=8, font_weight='bold'):
    """Draw labels below nodes with white shield background for better visibility"""
    for node, (x, y) in pos.items():
        # Position labels below nodes - now showing real entity names
        ax.text(x, y - 0.08, s=str(node), fontsize=font_size, fontweight=font_weight,
                ha='center', va='top', color='black',
                bbox=dict(facecolor='white', edgecolor='lightgray', alpha=0.9, 
                         boxstyle='round,pad=0.2', linewidth=0.5))

def draw_stylized_network(ax, G, period_name, all_periods_data, title):
    """Draw a stylized network graph with proper coloring and lost nodes display"""
    
    # Get node colors and lost nodes
    current_actors = set(G.nodes())
    node_colors, lost_nodes = get_node_colors_and_lost_nodes(current_actors, period_name, all_periods_data)
    
    # Create layout with better spacing for visibility
    pos = nx.spring_layout(G, k=2.5, iterations=50, seed=42)
    
    # Draw edges with subtle styling
    nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.3, width=0.8, edge_color='gray')
    
    # Draw nodes with period-specific colors and larger size
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, ax=ax, 
                          node_size=600, alpha=0.9, linewidths=2, edgecolors='white')
    
    # Draw labels with white shield underneath nodes (real entity names)
    draw_labels_with_white_shield(G, pos, ax, font_size=9, font_weight='bold')
    
    # Create legend
    legend_elements = []
    period_order = ['pre_crimea', 'post_crimea', 'covid', 'war']
    current_index = period_order.index(period_name)
    
    for i in range(current_index + 1):
        period = period_order[i]
        label = period.replace('_', '-').title()
        legend_elements.append(mpatches.Patch(color=colors[period], label=label))
    
    ax.legend(handles=legend_elements, loc='upper left', fontsize=12, framealpha=0.9)
    
    # Set title
    ax.set_title(title, fontsize=18, fontweight='bold', pad=20)
    ax.axis('off')
    
    # Display lost nodes only if not pre_crimea period (real entity names)
    if period_name != 'pre_crimea':
        if lost_nodes:
            lost_text = "Lost Nodes:\n" + "\n".join([f"• {node}" for node in lost_nodes])
        else:
            lost_text = "No lost nodes"
        
        # Add text box for lost nodes with better positioning
        ax.text(1.02, 0.98, lost_text, transform=ax.transAxes, fontsize=10, 
                verticalalignment='top', bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.8))

# Prepare all periods data with real entity names
all_periods_data = {
    'pre_crimea': pre_crimea_actors,
    'post_crimea': post_crimea_actors,
    'covid': covid_actors,
    'war': war_actors
}

# Function to create individual full-page network graphs
def create_individual_period_graph(period_name, save_path=None):
    """Create and optionally save individual period graph"""
    fig, ax = plt.subplots(1, 1, figsize=(18, 14))
    
    # Get the appropriate graph and data
    graphs = {'pre_crimea': G_pre, 'post_crimea': G_post, 'covid': G_covid, 'war': G_war}
    titles = {'pre_crimea': 'Pre-Crimea Period', 'post_crimea': 'Post-Crimea Period', 
             'covid': 'COVID Period', 'war': 'War Period'}
    
    draw_stylized_network(ax, graphs[period_name], period_name, all_periods_data, titles[period_name])
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    plt.show()

# Create all four individual graphs with real entity names
create_individual_period_graph('pre_crimea', 'pre_crimea_network.png')
create_individual_period_graph('post_crimea', 'post_crimea_network.png')
create_individual_period_graph('covid', 'covid_network.png')
create_individual_period_graph('war', 'war_network.png')
