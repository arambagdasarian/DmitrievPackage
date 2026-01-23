import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as mpatches
import pandas as pd
from networkx.algorithms import community
import re

def identify_diplomatic_actors(df):
    """
    Strictly identify core diplomatic actors - targeting ~50 most relevant entities
    """
    
    # Core diplomatic entities (high-level government and financial institutions)
    core_diplomatic_entities = [
        # Key persons
        'Кирилл Дмитриев', 'Владимир Путин', 'Дмитрий Медведев', 'Сергей Лавров',
        'Антон Силуанов', 'Максим Орешкин', 'Игорь Шувалов', 'Андрей Костин',
        'Герман Греф', 'Сергей Чемезов', 'Алексей Миллер', 'Игорь Сечин',
        
        # Core financial institutions
        'Российский фонд прямых инвестиций (РФПИ)', 'РФПИ',
        'Внешэкономбанк (ВЭБ)', 'ВЭБ', 'Сбербанк', 'Банк ВТБ',
        'Газпромбанк', 'ОАО «Газпром»', 'Новатэк', 'Роснефть',
        
        # International partners
        'China Investment Corporation', 'Public Investment Fund (PIF)',
        'Saudi Arabia', 'Deutsche Bank', 'Goldman Sachs', 'JP Morgan',
        'Mubadala Investment Company', 'Japan Bank for International Cooperation',
        
        # Government institutions
        'Министерство финансов', 'Минэкономразвития', 'Центральный банк',
        'Российский экспортный центр', 'Фонд национального благосостояния (ФНБ)',
        'Московская биржа', 'Российский союз промышленников и предпринимателей (РСПП)'
    ]
    
    # Diplomatic role indicators (strict)
    high_level_roles = [
        'министр', 'minister', 'президент', 'president', 'премьер', 'premier',
        'председатель', 'chairman', 'генеральный директор', 'ceo', 'глава', 'head'
    ]
    
    diplomatic_actors = set()
    entity_scores = {}
    
    # Score entities based on diplomatic relevance
    for _, row in df.iterrows():
        entity = str(row['Entity'])
        entity_type = row.get('Entity_Type', '')
        occurrences = row.get('Occurrences', 0)
        context = str(row.get('Context_Text', '')).lower()
        
        score = 0
        
        # Highest priority: Core known entities
        if any(core in entity for core in core_diplomatic_entities):
            score += 100
            
        # High priority: Government/financial role in name
        if entity_type == 'PER':
            if any(role in entity.lower() for role in high_level_roles):
                score += 50
                
        if entity_type == 'ORG':
            org_indicators = ['фонд', 'fund', 'банк', 'bank', 'министерство', 'ministry', 'корпорация', 'corporation']
            if any(indicator in entity.lower() for indicator in org_indicators):
                score += 30
                
        # Medium priority: Diplomatic context
        diplomatic_context_words = [
            'инвестиц', 'investment', 'соглашение', 'agreement', 'переговоры', 'negotiations',
            'сотрудничество', 'cooperation', 'партнерство', 'partnership', 'саммит', 'summit'
        ]
        context_score = sum(2 for word in diplomatic_context_words if word in context)
        score += min(context_score, 20)  # Cap context contribution
        
        # Frequency boost
        if occurrences > 100:
            score += 10
        elif occurrences > 50:
            score += 5
            
        if score > 0:
            if entity in entity_scores:
                entity_scores[entity] = max(entity_scores[entity], score)
            else:
                entity_scores[entity] = score
    
    # Select top ~50 diplomatic actors
    sorted_entities = sorted(entity_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Take top 50, but ensure minimum score threshold
    min_score = 25
    for entity, score in sorted_entities[:60]:  # Check top 60 but filter by score
        if score >= min_score:
            diplomatic_actors.add(entity)
        if len(diplomatic_actors) >= 50:
            break
    
    return diplomatic_actors

def create_diplomatic_network(file_path, diplomatic_actors, min_edge_weight=15):
    """Create network focusing on diplomatic actors with lower edge weight threshold"""
    df = pd.read_csv(file_path)
    
    # Filter to only diplomatic actors
    df_diplomatic = df[df['Entity'].isin(diplomatic_actors)]
    
    if df_diplomatic.empty:
        return nx.Graph()
    
    # Create co-occurrence matrix
    article_entities = df_diplomatic.groupby('Article_ID')['Entity'].apply(list).reset_index()
    
    edge_weights = {}
    for _, row in article_entities.iterrows():
        entities = row['Entity']
        for i in range(len(entities)):
            for j in range(i + 1, len(entities)):
                entity1, entity2 = entities[i], entities[j]
                edge = tuple(sorted([entity1, entity2]))
                edge_weights[edge] = edge_weights.get(edge, 0) + 1
    
    # Filter edges by minimum weight
    filtered_edges = [(e[0], e[1], w) for e, w in edge_weights.items() if w >= min_edge_weight]
    
    # Create network
    G = nx.Graph()
    G.add_weighted_edges_from(filtered_edges)
    
    # Add node attributes
    node_attributes = df_diplomatic.groupby('Entity').agg({
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

def get_node_colors_for_changes(current_nodes, previous_nodes, period_name):
    """
    Academic color scheme for diplomatic network analysis
    """
    colors = []
    core_diplomatic = ['Кирилл Дмитриев', 'РФПИ', 'Российский фонд прямых инвестиций']
    
    for node in current_nodes:
        # Core diplomatic actors (related to Kirill Dmitriev) - Dark red
        if any(core in str(node) for core in core_diplomatic):
            colors.append('#8B0000')  # Dark red for RDIF core
        # New actors (not in previous period) - Dark green
        elif previous_nodes is None or node not in previous_nodes:
            colors.append('#2F4F2F')  # Dark green for new entrants
        # Continuing actors - Dark blue
        else:
            colors.append('#191970')  # Midnight blue for continuing
    
    return colors

def draw_diplomatic_network(ax, G, period_name, previous_nodes, title):
    """Academic-style diplomatic network visualization"""
    
    if G.number_of_nodes() == 0:
        ax.text(0.5, 0.5, f"Insufficient diplomatic network data\n(minimum edge weight: 15)", 
               ha='center', va='center', transform=ax.transAxes, fontsize=12, 
               fontfamily='serif')
        ax.set_title(title, fontsize=14, fontweight='normal', pad=20, fontfamily='serif')
        ax.axis('off')
        return set(), []
    
    current_nodes = set(G.nodes())
    
    # Detect communities using Louvain algorithm
    if G.number_of_edges() > 0:
        communities = community.greedy_modularity_communities(G, weight='weight')
        node_to_community = {}
        for i, comm in enumerate(communities):
            for node in comm:
                node_to_community[node] = i
        num_communities = len(communities)
    else:
        node_to_community = {node: 0 for node in G.nodes()}
        num_communities = 1 if G.number_of_nodes() > 0 else 0
    
    # Academic layout with better spacing
    pos = nx.spring_layout(G, k=1.5, iterations=100, seed=42, 
                          weight='weight' if G.number_of_edges() > 0 else None)
    
    # Draw edges with academic styling
    if G.number_of_edges() > 0:
        edge_weights = [G[u][v]['weight'] for u, v in G.edges()]
        max_weight = max(edge_weights) if edge_weights else 1
        # More conservative edge thickness
        normalized_weights = [w/max_weight * 2 + 0.3 for w in edge_weights]
        nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.6, width=normalized_weights, 
                              edge_color='#696969')  # Dim gray
    
    # Get academic node colors
    node_colors = get_node_colors_for_changes(current_nodes, previous_nodes, period_name)
    
    # Conservative node sizing
    node_sizes = []
    for node in G.nodes():
        total_occ = G.nodes[node].get('total_occurrences', 0)
        # Smaller, more uniform sizing for academic presentation
        size = max(200, min(800, total_occ * 0.3))
        node_sizes.append(size)
    
    # Draw nodes with academic styling
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, ax=ax, 
                          node_size=node_sizes, alpha=0.9, 
                          linewidths=1.5, edgecolors='black')
    
    # Selective labeling for clarity (only most important nodes)
    degree_centrality = nx.degree_centrality(G)
    top_nodes = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)
    important_nodes = dict(top_nodes[:min(15, len(top_nodes))])  # Max 15 labels
    
    for node in important_nodes:
        if node in pos:
            x, y = pos[node]
            # Clean, academic labeling
            label = str(node)[:25] + "..." if len(str(node)) > 25 else str(node)
            ax.text(x, y - 0.12, s=label, fontsize=8, fontfamily='serif',
                   ha='center', va='top', color='black', weight='normal',
                   bbox=dict(facecolor='white', edgecolor='black', alpha=0.9, 
                           boxstyle='round,pad=0.2', linewidth=0.5))
    
    # Academic legend
    legend_elements = [
        mpatches.Patch(color='#8B0000', label='RDIF Core Network'),
        mpatches.Patch(color='#2F4F2F', label='New Entrants'),
        mpatches.Patch(color='#191970', label='Continuing Actors')
    ]
    
    legend = ax.legend(handles=legend_elements, loc='upper left', fontsize=10, 
                      framealpha=1.0, fancybox=False, edgecolor='black')
    # Set font family for legend text
    for text in legend.get_texts():
        text.set_fontfamily('serif')
    
    # Calculate removed actors
    removed_actors = []
    if previous_nodes is not None:
        removed_actors = list(previous_nodes - current_nodes)
    
    # Calculate modularity for analysis but don't display
    modularity_score = 0
    if G.number_of_edges() > 0 and num_communities > 1:
        modularity_score = community.modularity(G, communities, weight='weight')
    
    # Academic presentation of removed actors
    if removed_actors and len(removed_actors) > 0:
        # Show only top removed actors by centrality from previous period
        removed_text = f"Departed (n={len(removed_actors)}):\n"
        display_removed = removed_actors[:6]  # Show max 6
        for actor in display_removed:
            short_name = actor[:20] + "..." if len(actor) > 20 else actor
            removed_text += f"• {short_name}\n"
        if len(removed_actors) > 6:
            removed_text += f"• (+{len(removed_actors) - 6} others)"
    else:
        removed_text = "No departures"
    
    ax.text(1.02, 0.98, removed_text, transform=ax.transAxes, fontsize=9, 
           fontfamily='serif', verticalalignment='top', 
           bbox=dict(boxstyle="round,pad=0.4", facecolor="white", 
                    edgecolor='black', alpha=0.9, linewidth=1))
    
    # Academic title styling
    ax.set_title(title, fontsize=14, fontweight='normal', pad=20, fontfamily='serif')
    ax.axis('off')
    
    return current_nodes, removed_actors

# Read final_nodes.csv to identify all diplomatic actors
print("Identifying diplomatic actors from final_nodes.csv...")
df_all = pd.read_csv('final_nodes.csv')
diplomatic_actors = identify_diplomatic_actors(df_all)
print(f"Identified {len(diplomatic_actors)} diplomatic actors")

# Create networks for each period with stricter thresholds
print("Creating diplomatic networks for each period...")
G_pre = create_diplomatic_network('pre_crimea.csv', diplomatic_actors, min_edge_weight=15)
G_post = create_diplomatic_network('post_crimea.csv', diplomatic_actors, min_edge_weight=15)
G_covid = create_diplomatic_network('covid.csv', diplomatic_actors, min_edge_weight=15)
G_war = create_diplomatic_network('war.csv', diplomatic_actors, min_edge_weight=15)

print(f"Diplomatic network sizes (nodes, edges):")
print(f"Pre-Crimea: ({G_pre.number_of_nodes()}, {G_pre.number_of_edges()})")
print(f"Post-Crimea: ({G_post.number_of_nodes()}, {G_post.number_of_edges()})")
print(f"Covid: ({G_covid.number_of_nodes()}, {G_covid.number_of_edges()})")
print(f"War: ({G_war.number_of_nodes()}, {G_war.number_of_edges()})")

# Function to create individual diplomatic network graphs
def create_individual_diplomatic_graph(period_name, G, title, previous_nodes, save_prefix):
    """Create and save individual diplomatic network graph"""
    fig, ax = plt.subplots(1, 1, figsize=(14, 12))
    
    current_nodes, removed = draw_diplomatic_network(ax, G, period_name, previous_nodes, title)
    
    plt.tight_layout()
    
    # Save both PNG and PDF
    png_path = f'{save_prefix}_{period_name}_diplomatic_network.png'
    pdf_path = f'{save_prefix}_{period_name}_diplomatic_network.pdf'
    
    plt.savefig(png_path, dpi=300, bbox_inches='tight', 
               facecolor='white', edgecolor='none')
    plt.savefig(pdf_path, dpi=300, bbox_inches='tight', 
               facecolor='white', edgecolor='none')
    
    print(f"Saved: {png_path} and {pdf_path}")
    plt.show()
    
    return current_nodes, removed

# Create individual graphs for each period
print("Creating individual diplomatic community visualizations...")

# Track nodes across periods for change detection
previous_nodes = None
all_removed = []

# Period data
periods = [
    ('pre_crimea', G_pre, 'Pre-Crimea Period (2012-2014)\nBaseline Diplomatic Network\nLouvain Community Analysis'),
    ('post_crimea', G_post, 'Post-Crimea Period (2014-2017)\nSanctions & Pivot to East\nLouvain Community Analysis'),
    ('covid', G_covid, 'COVID-19 Period (2020-2022)\nPandemic Diplomacy Networks\nLouvain Community Analysis'),
    ('war', G_war, 'Ukraine War Period (2022-2024)\nWartime Diplomatic Networks\nLouvain Community Analysis')
]

for period_name, G, title in periods:
    current_nodes, removed = create_individual_diplomatic_graph(
        period_name, G, title, previous_nodes, 'diplomatic_communities'
    )
    previous_nodes = current_nodes
    all_removed.extend(removed)

# Print detailed analysis
print("\n" + "="*60)
print("DIPLOMATIC COMMUNITY ANALYSIS")
print("="*60)

print(f"\nTotal diplomatic actors identified: {len(diplomatic_actors)}")
print("\nSample diplomatic actors:")
for actor in list(diplomatic_actors)[:10]:
    print(f"  • {actor}")

print(f"\nEvolution Summary:")
for i, (period_name, G, _) in enumerate(periods):
    print(f"\n{period_name.upper()}:")
    print(f"  Active diplomatic actors: {G.number_of_nodes()}")
    print(f"  Diplomatic connections: {G.number_of_edges()}")
    
    if G.number_of_nodes() > 0:
        # Find most connected actors
        degree_centrality = nx.degree_centrality(G)
        top_actors = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:5]
        print("  Most connected actors:")
        for actor, centrality in top_actors:
            print(f"    - {actor[:30]}... (centrality: {centrality:.3f})")

print("\nDone!")
