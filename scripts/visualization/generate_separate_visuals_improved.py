#!/usr/bin/env python3
"""
Generate Improved Separate Visualizations - One Graph Per File
Based on refined dataset: Dmitriev_Node_Sheet_092025_SH_AF_102025.xlsx

IMPROVEMENTS:
- Minimalistic, clean styling
- Pie charts combine small slices into "Other"
- Better visibility and readability
- Replaced stacked area charts with bar charts for trends
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from collections import Counter, defaultdict
import networkx as nx
import warnings
import os
from pathlib import Path

# Try to import python-louvain, fallback to networkx if not available
try:
    import community.community_louvain as community_louvain
    LOUVAIN_AVAILABLE = True
except ImportError:
    LOUVAIN_AVAILABLE = False
    print("Warning: python-louvain not available, using networkx fallback")

warnings.filterwarnings('ignore')

# Configuration
OUTPUT_DIR = Path('separate_visuals')
OUTPUT_DIR.mkdir(exist_ok=True)

# Minimalistic style settings
plt.style.use('default')
sns.set_palette("Set2")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 11
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.spines.top'] = False
plt.rcParams['axes.spines.right'] = False
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.3
plt.rcParams['grid.linewidth'] = 0.5

# Period definitions
PERIODS = ['Pre-Crimea', 'Post-Crimea', 'COVID', 'War']
PERIOD_FILES = {
    'Pre-Crimea': 'pre_crimea.csv',
    'Post-Crimea': 'post_crimea.csv',
    'COVID': 'covid.csv',
    'War': 'war.csv'
}

# Minimalistic color scheme
COLORS = {
    'Pre-Crimea': '#4A90E2',
    'Post-Crimea': '#E24A4A',
    'COVID': '#F5A623',
    'War': '#7B68EE'
}

# ============================================================================
# DATA LOADING AND PREPARATION
# ============================================================================

def load_refined_attributes():
    """Load refined attributes from Excel file"""
    print("Loading refined attributes from Excel...")
    df_refined = pd.read_excel('Dmitriev_Node_Sheet_092025_SH_AF_102025.xlsx', sheet_name=0)
    # Clean column names
    df_refined.columns = df_refined.columns.str.strip()
    return df_refined

def load_period_data():
    """Load all period CSV files and merge with refined attributes"""
    print("Loading period CSV files...")
    df_refined = load_refined_attributes()
    
    # Create a mapping from Entity to attributes
    entity_attrs = {}
    for _, row in df_refined.iterrows():
        entity = str(row['Entity']).strip()
        entity_attrs[entity] = {
            'Sector': str(row.get('Sector', '')).strip() if pd.notna(row.get('Sector')) else 'Unknown',
            'State/Private': str(row.get('State/Private', '')).strip() if pd.notna(row.get('State/Private')) else 'Unknown',
            'Actor Type': str(row.get('Actor Type', '')).strip() if pd.notna(row.get('Actor Type')) else 'Unknown',
            'Jurisdiction': str(row.get('Jurisdiction', '')).strip() if pd.notna(row.get('Jurisdiction')) else 'Unknown'
        }
    
    period_data = {}
    for period, filename in PERIOD_FILES.items():
        print(f"  Loading {period}...")
        df = pd.read_csv(filename)
        
        # Merge with refined attributes
        df['Sector'] = df['Entity'].map(lambda x: entity_attrs.get(str(x).strip(), {}).get('Sector', 'Unknown'))
        df['State/Private'] = df['Entity'].map(lambda x: entity_attrs.get(str(x).strip(), {}).get('State/Private', 'Unknown'))
        df['Actor Type'] = df['Entity'].map(lambda x: entity_attrs.get(str(x).strip(), {}).get('Actor Type', 'Unknown'))
        df['Jurisdiction'] = df['Entity'].map(lambda x: entity_attrs.get(str(x).strip(), {}).get('Jurisdiction', 'Unknown'))
        
        # Replace empty strings with 'Unknown'
        for col in ['Sector', 'State/Private', 'Actor Type', 'Jurisdiction']:
            df[col] = df[col].replace('', 'Unknown')
        
        period_data[period] = df
        print(f"    Loaded {len(df)} records, {df['Entity'].nunique()} unique entities")
    
    return period_data

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_top_entities(df, n=50):
    """Get top N entities by occurrences"""
    entity_counts = df.groupby('Entity')['Occurrences'].sum().sort_values(ascending=False)
    return entity_counts.head(n).index.tolist()

def combine_small_slices(attr_counts, threshold_pct=3.0):
    """Combine small slices into 'Other' category"""
    total = attr_counts.sum()
    threshold = total * (threshold_pct / 100)
    
    main_slices = attr_counts[attr_counts >= threshold]
    small_slices = attr_counts[attr_counts < threshold]
    
    if len(small_slices) > 0 and small_slices.sum() > 0:
        main_slices['Other'] = small_slices.sum()
    
    return main_slices.sort_values(ascending=False)

# ============================================================================
# ANALYSIS 1: COMPOSITION CHANGES OVER PERIODS
# ============================================================================

def create_pie_chart_per_period(period_data, attribute, period):
    """Create a single pie chart for one period and one attribute with improved styling"""
    df = period_data[period]
    
    # Count attribute values (weighted by occurrences)
    attr_counts = df.groupby(attribute)['Occurrences'].sum().sort_values(ascending=False)
    
    # Combine small slices into "Other"
    attr_counts = combine_small_slices(attr_counts, threshold_pct=3.0)
    
    # Create figure with minimalistic style
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Use a clean color palette
    n_colors = len(attr_counts)
    colors = sns.color_palette("Set2", n_colors)
    
    # Create pie chart with better spacing
    wedges, texts, autotexts = ax.pie(
        attr_counts.values,
        labels=attr_counts.index,
        autopct='%1.1f%%',
        startangle=90,
        colors=colors,
        textprops={'fontsize': 10, 'fontweight': 'normal'},
        pctdistance=0.85,
        labeldistance=1.05,
        wedgeprops={'edgecolor': 'white', 'linewidth': 1.5}
    )
    
    # Format title - minimalistic
    attr_name = attribute.replace('/', ' / ')
    ax.set_title(f'{attr_name}\n{period}',
                fontsize=14, fontweight='bold', pad=15, color='#333333')
    
    # Style percentage text
    for autotext in autotexts:
        autotext.set_color('#333333')
        autotext.set_fontweight('normal')
        autotext.set_fontsize(9)
    
    # Remove axes for cleaner look
    ax.axis('equal')
    
    plt.tight_layout()
    
    # Save
    filename = f'{OUTPUT_DIR}/1_pie_{attribute.replace("/", "_")}_{period.replace(" ", "_")}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  ✓ Saved: {filename}")

def create_evolution_graph(period_data, attribute):
    """Create evolution line graph for one attribute across periods - minimalistic style"""
    # Calculate percentages for each period
    period_stats = {}
    for period in PERIODS:
        df = period_data[period]
        attr_counts = df.groupby(attribute)['Occurrences'].sum()
        total = attr_counts.sum()
        percentages = (attr_counts / total * 100).sort_values(ascending=False)
        period_stats[period] = percentages
    
    # Get all unique values across all periods
    all_values = set()
    for stats in period_stats.values():
        all_values.update(stats.index)
    all_values = sorted(list(all_values))
    
    # Create figure with minimalistic style
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Plot lines for each attribute value
    colors = sns.color_palette("Set2", len(all_values))
    for i, value in enumerate(all_values):
        y_values = []
        for period in PERIODS:
            if value in period_stats[period]:
                y_values.append(period_stats[period][value])
            else:
                y_values.append(0)
        
        ax.plot(PERIODS, y_values, marker='o', linewidth=2, markersize=6, 
               label=value, color=colors[i], alpha=0.8)
    
    ax.set_xlabel('Period', fontsize=12, fontweight='normal', color='#333333')
    ax.set_ylabel('Percentage (%)', fontsize=12, fontweight='normal', color='#333333')
    attr_name = attribute.replace('/', ' / ')
    ax.set_title(f'{attr_name} Evolution Across Periods', 
                fontsize=14, fontweight='bold', pad=15, color='#333333')
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9, frameon=False)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    ax.set_ylim(bottom=0)
    
    # Clean styling
    ax.spines['left'].set_color('#cccccc')
    ax.spines['bottom'].set_color('#cccccc')
    ax.tick_params(colors='#666666')
    
    plt.tight_layout()
    
    # Save
    filename = f'{OUTPUT_DIR}/1_evolution_{attribute.replace("/", "_")}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  ✓ Saved: {filename}")

# ============================================================================
# ANALYSIS 2: TOP 50 VS OVERALL COMPARISON
# ============================================================================

def create_top50_comparison(period_data, attribute, period):
    """Create comparison pie charts: Top 50 vs Overall for one period and attribute"""
    df = period_data[period]
    
    # Get top 50 entities
    top50_entities = get_top_entities(df, n=50)
    df_top50 = df[df['Entity'].isin(top50_entities)]
    
    # Calculate distributions
    overall_counts = df.groupby(attribute)['Occurrences'].sum()
    top50_counts = df_top50.groupby(attribute)['Occurrences'].sum()
    
    # Combine small slices
    overall_counts = combine_small_slices(overall_counts, threshold_pct=3.0)
    top50_counts = combine_small_slices(top50_counts, threshold_pct=3.0)
    
    # Create figure with minimalistic style
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Overall pie chart
    colors1 = sns.color_palette("Set2", len(overall_counts))
    wedges1, texts1, autotexts1 = ax1.pie(
        overall_counts.values,
        labels=overall_counts.index,
        autopct='%1.1f%%',
        startangle=90,
        colors=colors1,
        textprops={'fontsize': 9},
        pctdistance=0.85,
        wedgeprops={'edgecolor': 'white', 'linewidth': 1.5}
    )
    attr_name = attribute.replace('/', ' / ')
    ax1.set_title(f'Overall Network', fontsize=13, fontweight='bold', pad=15, color='#333333')
    for autotext in autotexts1:
        autotext.set_color('#333333')
        autotext.set_fontsize(8)
    ax1.axis('equal')
    
    # Top 50 pie chart
    colors2 = sns.color_palette("Set2", len(top50_counts))
    wedges2, texts2, autotexts2 = ax2.pie(
        top50_counts.values,
        labels=top50_counts.index,
        autopct='%1.1f%%',
        startangle=90,
        colors=colors2,
        textprops={'fontsize': 9},
        pctdistance=0.85,
        wedgeprops={'edgecolor': 'white', 'linewidth': 1.5}
    )
    ax2.set_title(f'Top 50 Actors', fontsize=13, fontweight='bold', pad=15, color='#333333')
    for autotext in autotexts2:
        autotext.set_color('#333333')
        autotext.set_fontsize(8)
    ax2.axis('equal')
    
    fig.suptitle(f'{period} - {attr_name} Comparison', 
                fontsize=15, fontweight='bold', y=1.02, color='#333333')
    plt.tight_layout()
    
    # Save
    filename = f'{OUTPUT_DIR}/2_top50_comparison_{attribute.replace("/", "_")}_{period.replace(" ", "_")}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  ✓ Saved: {filename}")

# ============================================================================
# ANALYSIS 3: SECTOR COMPOSITION AND INSTITUTIONAL REPURPOSING
# ============================================================================

def create_sector_composition_table(period_data):
    """Create sector composition table comparing overall, top 20, and top 50"""
    results = []
    
    for period in PERIODS:
        df = period_data[period]
        top20_entities = get_top_entities(df, n=20)
        top50_entities = get_top_entities(df, n=50)
        
        df_top20 = df[df['Entity'].isin(top20_entities)]
        df_top50 = df[df['Entity'].isin(top50_entities)]
        
        # Calculate sector percentages
        overall_sectors = df.groupby('Sector')['Occurrences'].sum()
        top20_sectors = df_top20.groupby('Sector')['Occurrences'].sum()
        top50_sectors = df_top50.groupby('Sector')['Occurrences'].sum()
        
        total_overall = overall_sectors.sum()
        total_top20 = top20_sectors.sum()
        total_top50 = top50_sectors.sum()
        
        all_sectors = set(overall_sectors.index) | set(top20_sectors.index) | set(top50_sectors.index)
        
        for sector in sorted(all_sectors):
            results.append({
                'Period': period,
                'Sector': sector,
                'Overall %': (overall_sectors.get(sector, 0) / total_overall * 100) if total_overall > 0 else 0,
                'Top 20 %': (top20_sectors.get(sector, 0) / total_top20 * 100) if total_top20 > 0 else 0,
                'Top 50 %': (top50_sectors.get(sector, 0) / total_top50 * 100) if total_top50 > 0 else 0
            })
    
    df_results = pd.DataFrame(results)
    df_results.to_csv(f'{OUTPUT_DIR}/3_sector_composition_table.csv', index=False)
    print(f"  ✓ Saved: {OUTPUT_DIR}/3_sector_composition_table.csv")
    
    return df_results

def create_sector_comparison_chart(period_data, period):
    """Create bar chart comparing sector composition: Overall vs Top 20 vs Top 50"""
    df = period_data[period]
    top20_entities = get_top_entities(df, n=20)
    top50_entities = get_top_entities(df, n=50)
    
    df_top20 = df[df['Entity'].isin(top20_entities)]
    df_top50 = df[df['Entity'].isin(top50_entities)]
    
    # Calculate percentages
    overall_sectors = df.groupby('Sector')['Occurrences'].sum()
    top20_sectors = df_top20.groupby('Sector')['Occurrences'].sum()
    top50_sectors = df_top50.groupby('Sector')['Occurrences'].sum()
    
    total_overall = overall_sectors.sum()
    total_top20 = top20_sectors.sum()
    total_top50 = top50_sectors.sum()
    
    all_sectors = sorted(set(overall_sectors.index) | set(top20_sectors.index) | set(top50_sectors.index))
    
    # Prepare data for plotting
    overall_pct = [(overall_sectors.get(s, 0) / total_overall * 100) if total_overall > 0 else 0 for s in all_sectors]
    top20_pct = [(top20_sectors.get(s, 0) / total_top20 * 100) if total_top20 > 0 else 0 for s in all_sectors]
    top50_pct = [(top50_sectors.get(s, 0) / total_top50 * 100) if total_top50 > 0 else 0 for s in all_sectors]
    
    # Create figure with minimalistic style
    fig, ax = plt.subplots(figsize=(14, 8))
    
    x = np.arange(len(all_sectors))
    width = 0.25
    
    bars1 = ax.bar(x - width, overall_pct, width, label='Overall Network', 
                   color='#4A90E2', alpha=0.8, edgecolor='white', linewidth=0.5)
    bars2 = ax.bar(x, top50_pct, width, label='Top 50', 
                   color='#E24A4A', alpha=0.8, edgecolor='white', linewidth=0.5)
    bars3 = ax.bar(x + width, top20_pct, width, label='Top 20', 
                   color='#F5A623', alpha=0.8, edgecolor='white', linewidth=0.5)
    
    ax.set_xlabel('Sector', fontsize=12, fontweight='normal', color='#333333')
    ax.set_ylabel('Percentage (%)', fontsize=12, fontweight='normal', color='#333333')
    ax.set_title(f'Sector Composition Comparison - {period}',
                fontsize=14, fontweight='bold', pad=15, color='#333333')
    ax.set_xticks(x)
    ax.set_xticklabels(all_sectors, rotation=45, ha='right', fontsize=9)
    ax.legend(fontsize=10, frameon=False)
    ax.grid(True, alpha=0.3, axis='y', linestyle='--', linewidth=0.5)
    ax.set_ylim(bottom=0)
    
    # Clean styling
    ax.spines['left'].set_color('#cccccc')
    ax.spines['bottom'].set_color('#cccccc')
    ax.tick_params(colors='#666666')
    
    plt.tight_layout()
    
    # Save
    filename = f'{OUTPUT_DIR}/3_sector_comparison_{period.replace(" ", "_")}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  ✓ Saved: {filename}")

# ============================================================================
# ANALYSIS 4: TRENDS ACROSS PERIODS (REPLACED STACKED AREA WITH BAR CHART)
# ============================================================================

def create_trend_bar_chart(period_data, attribute):
    """Create grouped bar chart showing trends across periods - replaces stacked area"""
    # Calculate percentages for each period
    period_data_list = []
    for period in PERIODS:
        df = period_data[period]
        attr_counts = df.groupby(attribute)['Occurrences'].sum()
        total = attr_counts.sum()
        percentages = (attr_counts / total * 100).sort_values(ascending=False)
        
        for attr_value, pct in percentages.items():
            period_data_list.append({
                'Period': period,
                'Attribute': attr_value,
                'Percentage': pct
            })
    
    df_plot = pd.DataFrame(period_data_list)
    
    # Get all unique attribute values
    all_attrs = sorted(df_plot['Attribute'].unique())
    
    # Create figure with minimalistic style
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Prepare data for grouped bar chart
    x = np.arange(len(PERIODS))
    width = 0.8 / len(all_attrs)
    
    colors = sns.color_palette("Set2", len(all_attrs))
    
    for i, attr_value in enumerate(all_attrs):
        values = []
        for period in PERIODS:
            row = df_plot[(df_plot['Period'] == period) & (df_plot['Attribute'] == attr_value)]
            values.append(row['Percentage'].values[0] if len(row) > 0 else 0)
        
        offset = (i - len(all_attrs) / 2) * width + width / 2
        ax.bar(x + offset, values, width, label=attr_value, 
              color=colors[i], alpha=0.8, edgecolor='white', linewidth=0.5)
    
    ax.set_xlabel('Period', fontsize=12, fontweight='normal', color='#333333')
    ax.set_ylabel('Percentage (%)', fontsize=12, fontweight='normal', color='#333333')
    attr_name = attribute.replace('/', ' / ')
    ax.set_title(f'{attr_name} Trends Across Periods', 
                fontsize=14, fontweight='bold', pad=15, color='#333333')
    ax.set_xticks(x)
    ax.set_xticklabels(PERIODS, fontsize=10)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9, frameon=False)
    ax.grid(True, alpha=0.3, axis='y', linestyle='--', linewidth=0.5)
    ax.set_ylim(bottom=0)
    
    # Clean styling
    ax.spines['left'].set_color('#cccccc')
    ax.spines['bottom'].set_color('#cccccc')
    ax.tick_params(colors='#666666')
    
    plt.tight_layout()
    
    # Save
    filename = f'{OUTPUT_DIR}/4_trend_{attribute.replace("/", "_")}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  ✓ Saved: {filename}")

# ============================================================================
# ANALYSIS 5: LOUVAIN COMMUNITIES WITH ATTRIBUTES
# ============================================================================

def build_network_from_period_data(df, min_edge_weight=2):
    """Build networkx graph from period data"""
    G = nx.Graph()
    
    # Add nodes with attributes
    for entity, group in df.groupby('Entity'):
        total_occurrences = group['Occurrences'].sum()
        G.add_node(entity,
                  Sector=group['Sector'].iloc[0],
                  State_Private=group['State/Private'].iloc[0],
                  Actor_Type=group['Actor Type'].iloc[0],
                  Jurisdiction=group['Jurisdiction'].iloc[0],
                  Occurrences=total_occurrences)
    
    # Create edges from co-occurrences in articles
    for article_id, article_df in df.groupby('Article_ID'):
        entities = article_df['Entity'].unique()
        # Create edges between all pairs of entities in the same article
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                if G.has_edge(entity1, entity2):
                    G[entity1][entity2]['weight'] += 1
                else:
                    G.add_edge(entity1, entity2, weight=1)
    
    # Filter edges by minimum weight
    edges_to_remove = [(u, v) for u, v, d in G.edges(data=True) if d['weight'] < min_edge_weight]
    G.remove_edges_from(edges_to_remove)
    
    # Remove isolated nodes
    G.remove_nodes_from(list(nx.isolates(G)))
    
    return G

def detect_louvain_communities(G):
    """Detect Louvain communities"""
    if LOUVAIN_AVAILABLE:
        try:
            partition = community_louvain.best_partition(G, weight='weight', random_state=42)
            return partition
        except:
            pass
    
    # Fallback to networkx implementation
    from networkx.algorithms import community
    communities = list(community.louvain_communities(G, weight='weight', seed=42))
    partition = {}
    for i, comm in enumerate(communities):
        for node in comm:
            partition[node] = i
    return partition

def create_louvain_community_visualization(period_data, period, attribute):
    """Create Louvain community network colored by attribute - minimalistic style"""
    df = period_data[period]
    
    # Build network
    G = build_network_from_period_data(df, min_edge_weight=2)
    
    if G.number_of_nodes() == 0:
        print(f"  ⚠ No network data for {period} - {attribute}")
        return
    
    # Detect communities
    partition = detect_louvain_communities(G)
    nx.set_node_attributes(G, partition, 'community')
    
    # Get attribute values for coloring
    attr_key = attribute.replace('/', '_')
    attr_values = [G.nodes[node].get(attr_key, 'Unknown') for node in G.nodes()]
    unique_attrs = sorted(set(attr_values))
    
    # Create color mapping - minimalistic palette
    colors_palette = sns.color_palette("Set2", len(unique_attrs))
    color_map = dict(zip(unique_attrs, colors_palette))
    node_colors = [color_map[attr] for attr in attr_values]
    
    # Create layout
    pos = nx.spring_layout(G, k=1.5, iterations=50, seed=42)
    
    # Create figure with minimalistic style
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Draw edges - subtle
    nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.15, width=0.3, edge_color='#cccccc')
    
    # Draw nodes - clean and visible
    node_sizes = [min(500, max(50, G.nodes[node].get('Occurrences', 1) * 5)) for node in G.nodes()]
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors, 
                          node_size=node_sizes, alpha=0.8, 
                          edgecolors='white', linewidths=0.5)
    
    # Draw labels for top nodes only
    top_nodes = sorted(G.nodes(), key=lambda x: G.nodes[x].get('Occurrences', 0), reverse=True)[:15]
    labels = {node: node[:25] + '...' if len(node) > 25 else node for node in top_nodes}
    nx.draw_networkx_labels(G, pos, labels, ax=ax, font_size=7, 
                            font_weight='normal', font_color='#333333')
    
    # Create legend - minimalistic
    legend_elements = [plt.Line2D([0], [0], marker='o', color='w', 
                                  markerfacecolor=color_map[attr], markersize=8, 
                                  markeredgecolor='white', markeredgewidth=0.5, label=attr)
                      for attr in unique_attrs]
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1, 1), 
             fontsize=9, frameon=False)
    
    attr_name = attribute.replace('/', ' / ')
    ax.set_title(f'Louvain Communities - {period}\nColored by {attr_name}',
                fontsize=13, fontweight='bold', pad=15, color='#333333')
    ax.axis('off')
    
    plt.tight_layout()
    
    # Save
    filename = f'{OUTPUT_DIR}/5_louvain_{attribute.replace("/", "_")}_{period.replace(" ", "_")}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  ✓ Saved: {filename}")

def create_community_composition_table(period_data, period):
    """Create table showing attribute composition of each Louvain community"""
    df = period_data[period]
    G = build_network_from_period_data(df, min_edge_weight=2)
    
    if G.number_of_nodes() == 0:
        return
    
    partition = detect_louvain_communities(G)
    
    # Analyze each community
    results = []
    for comm_id in set(partition.values()):
        comm_nodes = [node for node, cid in partition.items() if cid == comm_id]
        comm_df = df[df['Entity'].isin(comm_nodes)]
        
        # Count attributes
        sector_counts = comm_df.groupby('Sector')['Occurrences'].sum()
        state_private_counts = comm_df.groupby('State/Private')['Occurrences'].sum()
        actor_type_counts = comm_df.groupby('Actor Type')['Occurrences'].sum()
        
        total = comm_df['Occurrences'].sum()
        
        # Get dominant attributes
        dominant_sector = sector_counts.idxmax() if len(sector_counts) > 0 else 'Unknown'
        dominant_state_private = state_private_counts.idxmax() if len(state_private_counts) > 0 else 'Unknown'
        dominant_actor_type = actor_type_counts.idxmax() if len(actor_type_counts) > 0 else 'Unknown'
        
        results.append({
            'Period': period,
            'Community': comm_id,
            'Size': len(comm_nodes),
            'Total_Occurrences': total,
            'Dominant_Sector': dominant_sector,
            'Sector_%': (sector_counts[dominant_sector] / total * 100) if total > 0 else 0,
            'Dominant_State_Private': dominant_state_private,
            'State_Private_%': (state_private_counts[dominant_state_private] / total * 100) if total > 0 else 0,
            'Dominant_Actor_Type': dominant_actor_type,
            'Actor_Type_%': (actor_type_counts[dominant_actor_type] / total * 100) if total > 0 else 0
        })
    
    df_results = pd.DataFrame(results)
    filename = f'{OUTPUT_DIR}/5_louvain_composition_{period.replace(" ", "_")}.csv'
    df_results.to_csv(filename, index=False)
    print(f"  ✓ Saved: {filename}")

# ============================================================================
# ANALYSIS 6: ATTRIBUTE-BASED CLUSTERING
# ============================================================================

def create_attribute_cluster_visualization(period_data, period, attribute):
    """Create network visualization colored by attribute - minimalistic style"""
    df = period_data[period]
    G = build_network_from_period_data(df, min_edge_weight=2)
    
    if G.number_of_nodes() == 0:
        print(f"  ⚠ No network data for {period} - {attribute}")
        return
    
    # Get attribute values
    attr_key = attribute.replace('/', '_')
    attr_values = [G.nodes[node].get(attr_key, 'Unknown') for node in G.nodes()]
    unique_attrs = sorted(set(attr_values))
    
    # Calculate clustering metrics
    internal_edges = 0
    external_edges = 0
    
    for u, v in G.edges():
        u_attr = G.nodes[u].get(attr_key, 'Unknown')
        v_attr = G.nodes[v].get(attr_key, 'Unknown')
        if u_attr == v_attr:
            internal_edges += G[u][v]['weight']
        else:
            external_edges += G[u][v]['weight']
    
    total_edges_weight = internal_edges + external_edges
    cohesion = (internal_edges / total_edges_weight * 100) if total_edges_weight > 0 else 0
    
    # Create color mapping
    colors_palette = sns.color_palette("Set2", len(unique_attrs))
    color_map = dict(zip(unique_attrs, colors_palette))
    node_colors = [color_map[attr] for attr in attr_values]
    
    # Create layout
    pos = nx.spring_layout(G, k=1.5, iterations=50, seed=42)
    
    # Create figure with minimalistic style
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Separate edges by type
    internal_edges_list = []
    external_edges_list = []
    
    for u, v in G.edges():
        u_attr = G.nodes[u].get(attr_key, 'Unknown')
        v_attr = G.nodes[v].get(attr_key, 'Unknown')
        if u_attr == v_attr:
            internal_edges_list.append((u, v))
        else:
            external_edges_list.append((u, v))
    
    # Draw external edges first (background)
    if external_edges_list:
        nx.draw_networkx_edges(G, pos, edgelist=external_edges_list, ax=ax, 
                              alpha=0.1, width=0.3, edge_color='#cccccc')
    
    # Draw internal edges on top (highlighted)
    if internal_edges_list:
        nx.draw_networkx_edges(G, pos, edgelist=internal_edges_list, ax=ax, 
                              alpha=0.2, width=0.5, edge_color='#4CAF50')
    
    # Draw nodes - clean and visible
    node_sizes = [min(500, max(50, G.nodes[node].get('Occurrences', 1) * 5)) for node in G.nodes()]
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors, 
                          node_size=node_sizes, alpha=0.8, 
                          edgecolors='white', linewidths=0.5)
    
    # Draw labels for top nodes only
    top_nodes = sorted(G.nodes(), key=lambda x: G.nodes[x].get('Occurrences', 0), reverse=True)[:15]
    labels = {node: node[:25] + '...' if len(node) > 25 else node for node in top_nodes}
    nx.draw_networkx_labels(G, pos, labels, ax=ax, font_size=7, 
                            font_weight='normal', font_color='#333333')
    
    # Create legend
    legend_elements = [plt.Line2D([0], [0], marker='o', color='w', 
                                  markerfacecolor=color_map[attr], markersize=8, 
                                  markeredgecolor='white', markeredgewidth=0.5, label=attr)
                      for attr in unique_attrs]
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1, 1), 
             fontsize=9, frameon=False)
    
    attr_name = attribute.replace('/', ' / ')
    ax.set_title(f'Attribute-Based Clustering - {period}\n{attr_name}\n'
                f'Cohesion: {cohesion:.1f}%',
                fontsize=13, fontweight='bold', pad=15, color='#333333')
    ax.axis('off')
    
    plt.tight_layout()
    
    # Save
    filename = f'{OUTPUT_DIR}/6_attribute_cluster_{attribute.replace("/", "_")}_{period.replace(" ", "_")}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  ✓ Saved: {filename}")

def create_attribute_clustering_metrics(period_data):
    """Create CSV with clustering metrics for each attribute and period"""
    results = []
    attributes = ['Sector', 'State/Private', 'Actor Type', 'Jurisdiction']
    
    for period in PERIODS:
        df = period_data[period]
        G = build_network_from_period_data(df, min_edge_weight=2)
        
        if G.number_of_nodes() == 0:
            continue
        
        for attribute in attributes:
            attr_key = attribute.replace('/', '_')
            
            # Calculate metrics
            internal_edges = 0
            external_edges = 0
            
            for u, v in G.edges():
                u_attr = G.nodes[u].get(attr_key, 'Unknown')
                v_attr = G.nodes[v].get(attr_key, 'Unknown')
                if u_attr == v_attr:
                    internal_edges += G[u][v]['weight']
                else:
                    external_edges += G[u][v]['weight']
            
            total_edges_weight = internal_edges + external_edges
            cohesion = (internal_edges / total_edges_weight * 100) if total_edges_weight > 0 else 0
            
            results.append({
                'Period': period,
                'Attribute': attribute,
                'Internal_Edges': internal_edges,
                'External_Edges': external_edges,
                'Total_Edge_Weight': total_edges_weight,
                'Cohesion_%': cohesion
            })
    
    df_results = pd.DataFrame(results)
    filename = f'{OUTPUT_DIR}/6_attribute_clustering_metrics.csv'
    df_results.to_csv(filename, index=False)
    print(f"  ✓ Saved: {filename}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    print("="*80)
    print("GENERATING IMPROVED SEPARATE VISUALIZATIONS")
    print("="*80)
    print()
    
    # Load data
    period_data = load_period_data()
    
    attributes = ['Sector', 'State/Private', 'Actor Type', 'Jurisdiction']
    
    print("\n" + "="*80)
    print("ANALYSIS 1: Composition Changes Over Periods")
    print("="*80)
    
    # Create pie charts for each period and attribute
    for attribute in attributes:
        for period in PERIODS:
            create_pie_chart_per_period(period_data, attribute, period)
    
    # Create evolution graphs
    for attribute in attributes:
        create_evolution_graph(period_data, attribute)
    
    print("\n" + "="*80)
    print("ANALYSIS 2: Top 50 vs Overall Comparison")
    print("="*80)
    
    # Create top 50 comparisons
    for attribute in attributes:
        for period in PERIODS:
            create_top50_comparison(period_data, attribute, period)
    
    print("\n" + "="*80)
    print("ANALYSIS 3: Sector Composition and Institutional Repurposing")
    print("="*80)
    
    # Create sector composition table
    create_sector_composition_table(period_data)
    
    # Create sector comparison charts
    for period in PERIODS:
        create_sector_comparison_chart(period_data, period)
    
    print("\n" + "="*80)
    print("ANALYSIS 4: Trends Across Periods (Bar Charts)")
    print("="*80)
    
    # Create trend bar charts (replaced stacked area)
    for attribute in attributes:
        create_trend_bar_chart(period_data, attribute)
    
    print("\n" + "="*80)
    print("ANALYSIS 5: Louvain Communities with Attributes")
    print("="*80)
    
    # Create Louvain community visualizations
    for period in PERIODS:
        for attribute in attributes:
            create_louvain_community_visualization(period_data, period, attribute)
        create_community_composition_table(period_data, period)
    
    print("\n" + "="*80)
    print("ANALYSIS 6: Attribute-Based Clustering")
    print("="*80)
    
    # Create attribute-based clustering visualizations
    for period in PERIODS:
        for attribute in attributes:
            create_attribute_cluster_visualization(period_data, period, attribute)
    
    # Create clustering metrics table
    create_attribute_clustering_metrics(period_data)
    
    print("\n" + "="*80)
    print("VISUALIZATION GENERATION COMPLETE!")
    print("="*80)
    print(f"\nAll visualizations saved to: {OUTPUT_DIR}/")
    png_count = len(list(OUTPUT_DIR.glob('*.png')))
    csv_count = len(list(OUTPUT_DIR.glob('*.csv')))
    print(f"Total files created: {png_count} PNG files + {csv_count} CSV files = {png_count + csv_count} files")

if __name__ == '__main__':
    main()

