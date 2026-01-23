#!/usr/bin/env python3
"""
Generate Final Polished Visualizations - Ultra Minimalistic & Clear
Based on refined dataset: Dmitriev_Node_Sheet_092025_SH_AF_102025.xlsx

IMPROVEMENTS:
- Ultra minimalistic, ultra clean styling
- Maximum clarity and readability
- Better text sizes and positioning
- Simplified legends
- Cleaner network visualizations
- Better color choices
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

# Try to import python-louvain
try:
    import community.community_louvain as community_louvain
    LOUVAIN_AVAILABLE = True
except ImportError:
    LOUVAIN_AVAILABLE = False

warnings.filterwarnings('ignore')

# Configuration
OUTPUT_DIR = Path('separate_visuals')
OUTPUT_DIR.mkdir(exist_ok=True)

# Ultra minimalistic style settings
plt.style.use('default')
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 12
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
plt.rcParams['axes.spines.top'] = False
plt.rcParams['axes.spines.right'] = False
plt.rcParams['axes.spines.left'] = True
plt.rcParams['axes.spines.bottom'] = True
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.2
plt.rcParams['grid.linewidth'] = 0.5
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['axes.linewidth'] = 0.8
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['xtick.color'] = '#666666'
plt.rcParams['ytick.color'] = '#666666'
plt.rcParams['axes.labelcolor'] = '#333333'
plt.rcParams['text.color'] = '#333333'

# Period definitions
PERIODS = ['Pre-Crimea', 'Post-Crimea', 'COVID', 'War']
PERIOD_FILES = {
    'Pre-Crimea': 'pre_crimea.csv',
    'Post-Crimea': 'post_crimea.csv',
    'COVID': 'covid.csv',
    'War': 'war.csv'
}

# Clean, minimal color palette
PALETTE = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E', 
           '#E63946', '#457B9D', '#7209B7', '#3A86FF', '#06A77D']

# ============================================================================
# DATA LOADING
# ============================================================================

def load_refined_attributes():
    """Load refined attributes from Excel file"""
    print("Loading refined attributes from Excel...")
    df_refined = pd.read_excel('Dmitriev_Node_Sheet_092025_SH_AF_102025.xlsx', sheet_name=0)
    df_refined.columns = df_refined.columns.str.strip()
    return df_refined

def load_period_data():
    """Load all period CSV files and merge with refined attributes"""
    print("Loading period CSV files...")
    df_refined = load_refined_attributes()
    
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
        
        for col in ['Sector', 'State/Private', 'Actor Type', 'Jurisdiction']:
            df[col] = df['Entity'].map(lambda x: entity_attrs.get(str(x).strip(), {}).get(col, 'Unknown'))
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

def combine_small_slices(attr_counts, threshold_pct=5.0, max_categories=8):
    """Combine small slices into 'Other' category, limit to max categories"""
    total = attr_counts.sum()
    threshold = total * (threshold_pct / 100)
    
    main_slices = attr_counts[attr_counts >= threshold].head(max_categories)
    small_slices = attr_counts[attr_counts < threshold]
    
    # If we have too many main slices, keep only top max_categories
    if len(main_slices) >= max_categories:
        main_slices = attr_counts.head(max_categories)
        small_slices = attr_counts.iloc[max_categories:]
    
    if len(small_slices) > 0 and small_slices.sum() > 0:
        main_slices['Other'] = small_slices.sum()
    
    return main_slices.sort_values(ascending=False)

# ============================================================================
# ANALYSIS 1: COMPOSITION CHANGES OVER PERIODS
# ============================================================================

def create_pie_chart_per_period(period_data, attribute, period):
    """Create clean, minimal pie chart"""
    df = period_data[period]
    attr_counts = df.groupby(attribute)['Occurrences'].sum().sort_values(ascending=False)
    attr_counts = combine_small_slices(attr_counts, threshold_pct=5.0, max_categories=7)
    
    fig, ax = plt.subplots(figsize=(9, 7))
    
    # Use clean palette
    n_colors = len(attr_counts)
    colors = PALETTE[:n_colors] if n_colors <= len(PALETTE) else sns.color_palette("husl", n_colors)
    
    wedges, texts, autotexts = ax.pie(
        attr_counts.values,
        labels=None,  # No labels on pie
        autopct='%1.1f%%',
        startangle=90,
        colors=colors,
        textprops={'fontsize': 11, 'fontweight': 'normal', 'color': '#333333'},
        pctdistance=0.88,
        wedgeprops={'edgecolor': 'white', 'linewidth': 2, 'alpha': 0.9}
    )
    
    # Create legend outside
    legend_labels = [f'{label}' for label in attr_counts.index]
    ax.legend(wedges, legend_labels, loc='center left', bbox_to_anchor=(1, 0.5), 
             fontsize=10, frameon=False)
    
    attr_name = attribute.replace('/', ' / ')
    ax.set_title(f'{attr_name}\n{period}', fontsize=14, fontweight='bold', 
                pad=20, color='#1a1a1a')
    ax.axis('equal')
    
    plt.tight_layout()
    filename = f'{OUTPUT_DIR}/1_pie_{attribute.replace("/", "_")}_{period.replace(" ", "_")}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()
    print(f"  ✓ Saved: {filename}")

def create_evolution_graph(period_data, attribute):
    """Create clean evolution line graph"""
    period_stats = {}
    for period in PERIODS:
        df = period_data[period]
        attr_counts = df.groupby(attribute)['Occurrences'].sum()
        total = attr_counts.sum()
        percentages = (attr_counts / total * 100).sort_values(ascending=False)
        period_stats[period] = percentages
    
    all_values = sorted(set().union(*[set(stats.index) for stats in period_stats.values()]))
    
    fig, ax = plt.subplots(figsize=(11, 7))
    
    colors = PALETTE * ((len(all_values) // len(PALETTE)) + 1)
    for i, value in enumerate(all_values):
        y_values = [period_stats[period].get(value, 0) for period in PERIODS]
        ax.plot(PERIODS, y_values, marker='o', linewidth=2.5, markersize=7, 
               label=value, color=colors[i], alpha=0.85, markerfacecolor='white',
               markeredgewidth=2, markeredgecolor=colors[i])
    
    ax.set_xlabel('Period', fontsize=12, fontweight='normal', color='#333333')
    ax.set_ylabel('Percentage (%)', fontsize=12, fontweight='normal', color='#333333')
    attr_name = attribute.replace('/', ' / ')
    ax.set_title(f'{attr_name} Evolution', fontsize=14, fontweight='bold', 
                pad=20, color='#1a1a1a')
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9, 
             frameon=False, ncol=1)
    ax.set_ylim(bottom=0)
    ax.spines['left'].set_color('#cccccc')
    ax.spines['bottom'].set_color('#cccccc')
    
    plt.tight_layout()
    filename = f'{OUTPUT_DIR}/1_evolution_{attribute.replace("/", "_")}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()
    print(f"  ✓ Saved: {filename}")

# ============================================================================
# ANALYSIS 2: TOP 50 VS OVERALL COMPARISON
# ============================================================================

def create_top50_comparison(period_data, attribute, period):
    """Create side-by-side comparison"""
    df = period_data[period]
    top50_entities = get_top_entities(df, n=50)
    df_top50 = df[df['Entity'].isin(top50_entities)]
    
    overall_counts = df.groupby(attribute)['Occurrences'].sum()
    top50_counts = df_top50.groupby(attribute)['Occurrences'].sum()
    
    overall_counts = combine_small_slices(overall_counts, threshold_pct=5.0, max_categories=7)
    top50_counts = combine_small_slices(top50_counts, threshold_pct=5.0, max_categories=7)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    
    # Overall
    colors1 = PALETTE[:len(overall_counts)] if len(overall_counts) <= len(PALETTE) else sns.color_palette("husl", len(overall_counts))
    wedges1, texts1, autotexts1 = ax1.pie(
        overall_counts.values, labels=None, autopct='%1.1f%%', startangle=90,
        colors=colors1, textprops={'fontsize': 11, 'color': '#333333'},
        pctdistance=0.88, wedgeprops={'edgecolor': 'white', 'linewidth': 2, 'alpha': 0.9}
    )
    ax1.legend(wedges1, overall_counts.index, loc='center left', bbox_to_anchor=(1, 0.5), 
              fontsize=9, frameon=False)
    attr_name = attribute.replace('/', ' / ')
    ax1.set_title('Overall Network', fontsize=13, fontweight='bold', pad=15, color='#1a1a1a')
    ax1.axis('equal')
    
    # Top 50
    colors2 = PALETTE[:len(top50_counts)] if len(top50_counts) <= len(PALETTE) else sns.color_palette("husl", len(top50_counts))
    wedges2, texts2, autotexts2 = ax2.pie(
        top50_counts.values, labels=None, autopct='%1.1f%%', startangle=90,
        colors=colors2, textprops={'fontsize': 11, 'color': '#333333'},
        pctdistance=0.88, wedgeprops={'edgecolor': 'white', 'linewidth': 2, 'alpha': 0.9}
    )
    ax2.legend(wedges2, top50_counts.index, loc='center left', bbox_to_anchor=(1, 0.5), 
              fontsize=9, frameon=False)
    ax2.set_title('Top 50 Actors', fontsize=13, fontweight='bold', pad=15, color='#1a1a1a')
    ax2.axis('equal')
    
    fig.suptitle(f'{period} - {attr_name}', fontsize=15, fontweight='bold', 
                y=1.02, color='#1a1a1a')
    plt.tight_layout()
    
    filename = f'{OUTPUT_DIR}/2_top50_comparison_{attribute.replace("/", "_")}_{period.replace(" ", "_")}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()
    print(f"  ✓ Saved: {filename}")

# ============================================================================
# ANALYSIS 3: SECTOR COMPOSITION
# ============================================================================

def create_sector_composition_table(period_data):
    """Create sector composition table"""
    results = []
    for period in PERIODS:
        df = period_data[period]
        top20_entities = get_top_entities(df, n=20)
        top50_entities = get_top_entities(df, n=50)
        
        df_top20 = df[df['Entity'].isin(top20_entities)]
        df_top50 = df[df['Entity'].isin(top50_entities)]
        
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
                'Overall %': round((overall_sectors.get(sector, 0) / total_overall * 100) if total_overall > 0 else 0, 2),
                'Top 20 %': round((top20_sectors.get(sector, 0) / total_top20 * 100) if total_top20 > 0 else 0, 2),
                'Top 50 %': round((top50_sectors.get(sector, 0) / total_top50 * 100) if total_top50 > 0 else 0, 2)
            })
    
    df_results = pd.DataFrame(results)
    df_results.to_csv(f'{OUTPUT_DIR}/3_sector_composition_table.csv', index=False)
    print(f"  ✓ Saved: {OUTPUT_DIR}/3_sector_composition_table.csv")
    return df_results

def create_sector_comparison_chart(period_data, period):
    """Create clean bar chart"""
    df = period_data[period]
    top20_entities = get_top_entities(df, n=20)
    top50_entities = get_top_entities(df, n=50)
    
    df_top20 = df[df['Entity'].isin(top20_entities)]
    df_top50 = df[df['Entity'].isin(top50_entities)]
    
    overall_sectors = df.groupby('Sector')['Occurrences'].sum()
    top20_sectors = df_top20.groupby('Sector')['Occurrences'].sum()
    top50_sectors = df_top50.groupby('Sector')['Occurrences'].sum()
    
    total_overall = overall_sectors.sum()
    total_top20 = top20_sectors.sum()
    total_top50 = top50_sectors.sum()
    
    all_sectors = sorted(set(overall_sectors.index) | set(top20_sectors.index) | set(top50_sectors.index))
    
    # Limit to top sectors for clarity
    top_sectors = overall_sectors.nlargest(10).index.tolist()
    if 'Other' not in top_sectors:
        other_sum = overall_sectors[~overall_sectors.index.isin(top_sectors)].sum()
        if other_sum > 0:
            top_sectors.append('Other')
    
    overall_pct = [(overall_sectors.get(s, 0) / total_overall * 100) if total_overall > 0 else 0 for s in top_sectors]
    top20_pct = [(top20_sectors.get(s, 0) / total_top20 * 100) if total_top20 > 0 else 0 for s in top_sectors]
    top50_pct = [(top50_sectors.get(s, 0) / total_top50 * 100) if total_top50 > 0 else 0 for s in top_sectors]
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    x = np.arange(len(top_sectors))
    width = 0.25
    
    bars1 = ax.bar(x - width, overall_pct, width, label='Overall', 
                   color='#2E86AB', alpha=0.85, edgecolor='white', linewidth=1)
    bars2 = ax.bar(x, top50_pct, width, label='Top 50', 
                   color='#A23B72', alpha=0.85, edgecolor='white', linewidth=1)
    bars3 = ax.bar(x + width, top20_pct, width, label='Top 20', 
                   color='#F18F01', alpha=0.85, edgecolor='white', linewidth=1)
    
    ax.set_xlabel('Sector', fontsize=12, fontweight='normal', color='#333333')
    ax.set_ylabel('Percentage (%)', fontsize=12, fontweight='normal', color='#333333')
    ax.set_title(f'Sector Composition - {period}', fontsize=14, fontweight='bold', 
                pad=20, color='#1a1a1a')
    ax.set_xticks(x)
    ax.set_xticklabels(top_sectors, rotation=45, ha='right', fontsize=10)
    ax.legend(fontsize=10, frameon=False, loc='upper right')
    ax.set_ylim(bottom=0)
    ax.spines['left'].set_color('#cccccc')
    ax.spines['bottom'].set_color('#cccccc')
    
    plt.tight_layout()
    filename = f'{OUTPUT_DIR}/3_sector_comparison_{period.replace(" ", "_")}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()
    print(f"  ✓ Saved: {filename}")

# ============================================================================
# ANALYSIS 4: TRENDS (BAR CHARTS)
# ============================================================================

def create_trend_bar_chart(period_data, attribute):
    """Create clean grouped bar chart"""
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
    all_attrs = sorted(df_plot['Attribute'].unique())
    
    # Limit to top attributes
    top_attrs = df_plot.groupby('Attribute')['Percentage'].mean().nlargest(8).index.tolist()
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    x = np.arange(len(PERIODS))
    width = 0.8 / len(top_attrs)
    
    colors = PALETTE[:len(top_attrs)]
    
    for i, attr_value in enumerate(top_attrs):
        values = [df_plot[(df_plot['Period'] == period) & (df_plot['Attribute'] == attr_value)]['Percentage'].values[0] 
                 if len(df_plot[(df_plot['Period'] == period) & (df_plot['Attribute'] == attr_value)]) > 0 else 0 
                 for period in PERIODS]
        
        offset = (i - len(top_attrs) / 2) * width + width / 2
        ax.bar(x + offset, values, width, label=attr_value, 
              color=colors[i], alpha=0.85, edgecolor='white', linewidth=1)
    
    ax.set_xlabel('Period', fontsize=12, fontweight='normal', color='#333333')
    ax.set_ylabel('Percentage (%)', fontsize=12, fontweight='normal', color='#333333')
    attr_name = attribute.replace('/', ' / ')
    ax.set_title(f'{attr_name} Trends', fontsize=14, fontweight='bold', 
                pad=20, color='#1a1a1a')
    ax.set_xticks(x)
    ax.set_xticklabels(PERIODS, fontsize=11)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9, frameon=False, ncol=1)
    ax.set_ylim(bottom=0)
    ax.spines['left'].set_color('#cccccc')
    ax.spines['bottom'].set_color('#cccccc')
    
    plt.tight_layout()
    filename = f'{OUTPUT_DIR}/4_trend_{attribute.replace("/", "_")}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()
    print(f"  ✓ Saved: {filename}")

# ============================================================================
# ANALYSIS 5: LOUVAIN COMMUNITIES
# ============================================================================

def build_network_from_period_data(df, min_edge_weight=2):
    """Build networkx graph from period data"""
    G = nx.Graph()
    
    for entity, group in df.groupby('Entity'):
        total_occurrences = group['Occurrences'].sum()
        G.add_node(entity,
                  Sector=group['Sector'].iloc[0],
                  State_Private=group['State/Private'].iloc[0],
                  Actor_Type=group['Actor Type'].iloc[0],
                  Jurisdiction=group['Jurisdiction'].iloc[0],
                  Occurrences=total_occurrences)
    
    for article_id, article_df in df.groupby('Article_ID'):
        entities = article_df['Entity'].unique()
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                if G.has_edge(entity1, entity2):
                    G[entity1][entity2]['weight'] += 1
                else:
                    G.add_edge(entity1, entity2, weight=1)
    
    edges_to_remove = [(u, v) for u, v, d in G.edges(data=True) if d['weight'] < min_edge_weight]
    G.remove_edges_from(edges_to_remove)
    G.remove_nodes_from(list(nx.isolates(G)))
    
    return G

def detect_louvain_communities(G):
    """Detect Louvain communities"""
    if LOUVAIN_AVAILABLE:
        try:
            return community_louvain.best_partition(G, weight='weight', random_state=42)
        except:
            pass
    
    from networkx.algorithms import community
    communities = list(community.louvain_communities(G, weight='weight', seed=42))
    partition = {}
    for i, comm in enumerate(communities):
        for node in comm:
            partition[node] = i
    return partition

def create_louvain_community_visualization(period_data, period, attribute):
    """Create clean Louvain visualization"""
    df = period_data[period]
    G = build_network_from_period_data(df, min_edge_weight=2)
    
    if G.number_of_nodes() == 0:
        print(f"  ⚠ No network data for {period} - {attribute}")
        return
    
    partition = detect_louvain_communities(G)
    nx.set_node_attributes(G, partition, 'community')
    
    attr_key = attribute.replace('/', '_')
    attr_values = [G.nodes[node].get(attr_key, 'Unknown') for node in G.nodes()]
    unique_attrs = sorted(set(attr_values))
    
    colors_palette = PALETTE * ((len(unique_attrs) // len(PALETTE)) + 1)
    color_map = dict(zip(unique_attrs, colors_palette[:len(unique_attrs)]))
    node_colors = [color_map[attr] for attr in attr_values]
    
    pos = nx.spring_layout(G, k=1.8, iterations=60, seed=42)
    
    fig, ax = plt.subplots(figsize=(13, 10))
    
    # Draw edges - very subtle
    nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.1, width=0.2, edge_color='#cccccc')
    
    # Draw nodes
    node_sizes = [min(400, max(30, G.nodes[node].get('Occurrences', 1) * 4)) for node in G.nodes()]
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors, 
                          node_size=node_sizes, alpha=0.85, 
                          edgecolors='white', linewidths=1)
    
    # Labels for top 10 nodes only
    top_nodes = sorted(G.nodes(), key=lambda x: G.nodes[x].get('Occurrences', 0), reverse=True)[:10]
    labels = {node: node[:20] + '...' if len(node) > 20 else node for node in top_nodes}
    nx.draw_networkx_labels(G, pos, labels, ax=ax, font_size=8, 
                            font_weight='normal', font_color='#1a1a1a',
                            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                                     edgecolor='none', alpha=0.7))
    
    # Clean legend
    legend_elements = [plt.Line2D([0], [0], marker='o', color='w', 
                                  markerfacecolor=color_map[attr], markersize=10, 
                                  markeredgecolor='white', markeredgewidth=1, label=attr)
                      for attr in unique_attrs]
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1, 1), 
             fontsize=9, frameon=False, title=attribute.replace('/', ' / '), 
             title_fontsize=10)
    
    attr_name = attribute.replace('/', ' / ')
    ax.set_title(f'Louvain Communities - {period}\nColored by {attr_name}',
                fontsize=13, fontweight='bold', pad=20, color='#1a1a1a')
    ax.axis('off')
    
    plt.tight_layout()
    filename = f'{OUTPUT_DIR}/5_louvain_{attribute.replace("/", "_")}_{period.replace(" ", "_")}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()
    print(f"  ✓ Saved: {filename}")

def create_community_composition_table(period_data, period):
    """Create community composition table"""
    df = period_data[period]
    G = build_network_from_period_data(df, min_edge_weight=2)
    
    if G.number_of_nodes() == 0:
        return
    
    partition = detect_louvain_communities(G)
    results = []
    
    for comm_id in set(partition.values()):
        comm_nodes = [node for node, cid in partition.items() if cid == comm_id]
        comm_df = df[df['Entity'].isin(comm_nodes)]
        
        sector_counts = comm_df.groupby('Sector')['Occurrences'].sum()
        state_private_counts = comm_df.groupby('State/Private')['Occurrences'].sum()
        actor_type_counts = comm_df.groupby('Actor Type')['Occurrences'].sum()
        
        total = comm_df['Occurrences'].sum()
        
        dominant_sector = sector_counts.idxmax() if len(sector_counts) > 0 else 'Unknown'
        dominant_state_private = state_private_counts.idxmax() if len(state_private_counts) > 0 else 'Unknown'
        dominant_actor_type = actor_type_counts.idxmax() if len(actor_type_counts) > 0 else 'Unknown'
        
        results.append({
            'Period': period,
            'Community': comm_id,
            'Size': len(comm_nodes),
            'Total_Occurrences': total,
            'Dominant_Sector': dominant_sector,
            'Sector_%': round((sector_counts[dominant_sector] / total * 100) if total > 0 else 0, 2),
            'Dominant_State_Private': dominant_state_private,
            'State_Private_%': round((state_private_counts[dominant_state_private] / total * 100) if total > 0 else 0, 2),
            'Dominant_Actor_Type': dominant_actor_type,
            'Actor_Type_%': round((actor_type_counts[dominant_actor_type] / total * 100) if total > 0 else 0, 2)
        })
    
    df_results = pd.DataFrame(results)
    filename = f'{OUTPUT_DIR}/5_louvain_composition_{period.replace(" ", "_")}.csv'
    df_results.to_csv(filename, index=False)
    print(f"  ✓ Saved: {filename}")

# ============================================================================
# ANALYSIS 6: ATTRIBUTE-BASED CLUSTERING
# ============================================================================

def create_attribute_cluster_visualization(period_data, period, attribute):
    """Create clean attribute clustering visualization"""
    df = period_data[period]
    G = build_network_from_period_data(df, min_edge_weight=2)
    
    if G.number_of_nodes() == 0:
        print(f"  ⚠ No network data for {period} - {attribute}")
        return
    
    attr_key = attribute.replace('/', '_')
    attr_values = [G.nodes[node].get(attr_key, 'Unknown') for node in G.nodes()]
    unique_attrs = sorted(set(attr_values))
    
    internal_edges = sum(G[u][v]['weight'] for u, v in G.edges() 
                        if G.nodes[u].get(attr_key, 'Unknown') == G.nodes[v].get(attr_key, 'Unknown'))
    external_edges = sum(G[u][v]['weight'] for u, v in G.edges() 
                        if G.nodes[u].get(attr_key, 'Unknown') != G.nodes[v].get(attr_key, 'Unknown'))
    
    total_edges_weight = internal_edges + external_edges
    cohesion = (internal_edges / total_edges_weight * 100) if total_edges_weight > 0 else 0
    
    colors_palette = PALETTE * ((len(unique_attrs) // len(PALETTE)) + 1)
    color_map = dict(zip(unique_attrs, colors_palette[:len(unique_attrs)]))
    node_colors = [color_map[attr] for attr in attr_values]
    
    pos = nx.spring_layout(G, k=1.8, iterations=60, seed=42)
    
    fig, ax = plt.subplots(figsize=(13, 10))
    
    # Separate edges
    internal_edges_list = [(u, v) for u, v in G.edges() 
                          if G.nodes[u].get(attr_key, 'Unknown') == G.nodes[v].get(attr_key, 'Unknown')]
    external_edges_list = [(u, v) for u, v in G.edges() 
                          if G.nodes[u].get(attr_key, 'Unknown') != G.nodes[v].get(attr_key, 'Unknown')]
    
    if external_edges_list:
        nx.draw_networkx_edges(G, pos, edgelist=external_edges_list, ax=ax, 
                              alpha=0.08, width=0.2, edge_color='#cccccc')
    
    if internal_edges_list:
        nx.draw_networkx_edges(G, pos, edgelist=internal_edges_list, ax=ax, 
                              alpha=0.25, width=0.4, edge_color='#4CAF50')
    
    node_sizes = [min(400, max(30, G.nodes[node].get('Occurrences', 1) * 4)) for node in G.nodes()]
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors, 
                          node_size=node_sizes, alpha=0.85, 
                          edgecolors='white', linewidths=1)
    
    top_nodes = sorted(G.nodes(), key=lambda x: G.nodes[x].get('Occurrences', 0), reverse=True)[:10]
    labels = {node: node[:20] + '...' if len(node) > 20 else node for node in top_nodes}
    nx.draw_networkx_labels(G, pos, labels, ax=ax, font_size=8, 
                            font_weight='normal', font_color='#1a1a1a',
                            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                                     edgecolor='none', alpha=0.7))
    
    legend_elements = [plt.Line2D([0], [0], marker='o', color='w', 
                                  markerfacecolor=color_map[attr], markersize=10, 
                                  markeredgecolor='white', markeredgewidth=1, label=attr)
                      for attr in unique_attrs]
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1, 1), 
             fontsize=9, frameon=False, title=attribute.replace('/', ' / '), 
             title_fontsize=10)
    
    attr_name = attribute.replace('/', ' / ')
    ax.set_title(f'Attribute Clustering - {period}\n{attr_name}\nCohesion: {cohesion:.1f}%',
                fontsize=13, fontweight='bold', pad=20, color='#1a1a1a')
    ax.axis('off')
    
    plt.tight_layout()
    filename = f'{OUTPUT_DIR}/6_attribute_cluster_{attribute.replace("/", "_")}_{period.replace(" ", "_")}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()
    print(f"  ✓ Saved: {filename}")

def create_attribute_clustering_metrics(period_data):
    """Create clustering metrics CSV"""
    results = []
    attributes = ['Sector', 'State/Private', 'Actor Type', 'Jurisdiction']
    
    for period in PERIODS:
        df = period_data[period]
        G = build_network_from_period_data(df, min_edge_weight=2)
        
        if G.number_of_nodes() == 0:
            continue
        
        for attribute in attributes:
            attr_key = attribute.replace('/', '_')
            
            internal_edges = sum(G[u][v]['weight'] for u, v in G.edges() 
                               if G.nodes[u].get(attr_key, 'Unknown') == G.nodes[v].get(attr_key, 'Unknown'))
            external_edges = sum(G[u][v]['weight'] for u, v in G.edges() 
                               if G.nodes[u].get(attr_key, 'Unknown') != G.nodes[v].get(attr_key, 'Unknown'))
            
            total_edges_weight = internal_edges + external_edges
            cohesion = (internal_edges / total_edges_weight * 100) if total_edges_weight > 0 else 0
            
            results.append({
                'Period': period,
                'Attribute': attribute,
                'Internal_Edges': internal_edges,
                'External_Edges': external_edges,
                'Total_Edge_Weight': total_edges_weight,
                'Cohesion_%': round(cohesion, 2)
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
    print("GENERATING FINAL POLISHED VISUALIZATIONS")
    print("="*80)
    print()
    
    period_data = load_period_data()
    attributes = ['Sector', 'State/Private', 'Actor Type', 'Jurisdiction']
    
    print("\n" + "="*80)
    print("ANALYSIS 1: Composition Changes Over Periods")
    print("="*80)
    for attribute in attributes:
        for period in PERIODS:
            create_pie_chart_per_period(period_data, attribute, period)
        create_evolution_graph(period_data, attribute)
    
    print("\n" + "="*80)
    print("ANALYSIS 2: Top 50 vs Overall Comparison")
    print("="*80)
    for attribute in attributes:
        for period in PERIODS:
            create_top50_comparison(period_data, attribute, period)
    
    print("\n" + "="*80)
    print("ANALYSIS 3: Sector Composition and Institutional Repurposing")
    print("="*80)
    create_sector_composition_table(period_data)
    for period in PERIODS:
        create_sector_comparison_chart(period_data, period)
    
    print("\n" + "="*80)
    print("ANALYSIS 4: Trends Across Periods")
    print("="*80)
    for attribute in attributes:
        create_trend_bar_chart(period_data, attribute)
    
    print("\n" + "="*80)
    print("ANALYSIS 5: Louvain Communities with Attributes")
    print("="*80)
    for period in PERIODS:
        for attribute in attributes:
            create_louvain_community_visualization(period_data, period, attribute)
        create_community_composition_table(period_data, period)
    
    print("\n" + "="*80)
    print("ANALYSIS 6: Attribute-Based Clustering")
    print("="*80)
    for period in PERIODS:
        for attribute in attributes:
            create_attribute_cluster_visualization(period_data, period, attribute)
    create_attribute_clustering_metrics(period_data)
    
    print("\n" + "="*80)
    print("VISUALIZATION GENERATION COMPLETE!")
    print("="*80)
    png_count = len(list(OUTPUT_DIR.glob('*.png')))
    csv_count = len(list(OUTPUT_DIR.glob('*.csv')))
    print(f"\nTotal files created: {png_count} PNG files + {csv_count} CSV files = {png_count + csv_count} files")

if __name__ == '__main__':
    main()


