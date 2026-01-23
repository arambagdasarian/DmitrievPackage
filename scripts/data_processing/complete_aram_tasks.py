#!/usr/bin/env python3
"""
Complete Aram's Tasks from Finalization Document
This script addresses all visualization and analysis tasks assigned to Aram.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import networkx as nx
from collections import Counter, defaultdict
from matplotlib.patches import Circle
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')

# Configuration
OUTPUT_DIR = Path('deliverables')
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.joinpath('visuals').mkdir(exist_ok=True)
OUTPUT_DIR.joinpath('data').mkdir(exist_ok=True)
OUTPUT_DIR.joinpath('analysis').mkdir(exist_ok=True)
OUTPUT_DIR.joinpath('documentation').mkdir(exist_ok=True)

# Period files
PERIOD_FILES = {
    'pre_crimea': 'pre_crimea.csv',
    'post_crimea': 'post_crimea.csv',
    'covid': 'covid.csv',
    'war': 'war.csv'
}

# ============================================================================
# TASK 1: Academic Core Structure WITHOUT labels/badges
# ============================================================================

def create_academic_core_structure_no_labels():
    """Create conceptual visualization of core-periphery structure without any labels"""
    from NewVisuals.academic_network_visualizer import AcademicNetworkVisualizer
    
    visualizer = AcademicNetworkVisualizer()
    
    # Load networks
    periods_data = {}
    for period_name, file_path in PERIOD_FILES.items():
        try:
            G = visualizer.create_network_from_csv(file_path, min_edge_weight=20)
            periods_data[period_name] = G
        except Exception as e:
            print(f"Error loading {period_name}: {e}")
            continue
    
    # Create modified version without labels
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    fig.patch.set_facecolor('white')
    
    # Combine all periods to identify persistent actors
    all_nodes = set()
    node_periods = defaultdict(set)
    node_total_degree = defaultdict(int)
    
    for period, G in periods_data.items():
        all_nodes.update(G.nodes())
        degrees = dict(G.degree())
        for node in G.nodes():
            node_periods[node].add(period)
            node_total_degree[node] += degrees[node]
    
    # Classify by persistence
    total_periods = len(periods_data)
    persistent_nodes = {node for node, periods in node_periods.items() 
                      if len(periods) >= total_periods - 1}
    
    # Get top actors by category
    persistent_by_category = {'stable_core': [], 'domestic': [], 'international': []}
    
    for node in persistent_nodes:
        for G in periods_data.values():
            if node in G.nodes():
                category = G.nodes[node].get('node_category', 'domestic')
                if category in persistent_by_category:
                    persistent_by_category[category].append((node, node_total_degree[node]))
                break
    
    # Sort and take top actors
    for category in persistent_by_category:
        persistent_by_category[category] = sorted(
            persistent_by_category[category], 
            key=lambda x: x[1], reverse=True
        )[:8]
    
    # Create hierarchical layout
    pos = {}
    colors = {
        'stable_core': '#E74C3C',
        'domestic': '#3498DB',
        'international': '#2ECC71'
    }
    
    # Core in center
    core_actors = [item[0] for item in persistent_by_category['stable_core']]
    if core_actors:
        if len(core_actors) == 1:
            pos[core_actors[0]] = (0, 0)
        else:
            angles = np.linspace(0, 2*np.pi, len(core_actors), endpoint=False)
            for i, actor in enumerate(core_actors):
                pos[actor] = (0.2 * np.cos(angles[i]), 0.2 * np.sin(angles[i]))
    
    # Domestic in middle ring
    domestic_actors = [item[0] for item in persistent_by_category['domestic']]
    if domestic_actors:
        angles = np.linspace(0, 2*np.pi, len(domestic_actors), endpoint=False)
        for i, actor in enumerate(domestic_actors):
            pos[actor] = (0.5 * np.cos(angles[i]), 0.5 * np.sin(angles[i]))
    
    # International in outer ring
    intl_actors = [item[0] for item in persistent_by_category['international']]
    if intl_actors:
        angles = np.linspace(0, 2*np.pi, len(intl_actors), endpoint=False)
        for i, actor in enumerate(intl_actors):
            pos[actor] = (0.8 * np.cos(angles[i]), 0.8 * np.sin(angles[i]))
    
    # Find connections
    all_key_actors = core_actors + domestic_actors + intl_actors
    connections = defaultdict(int)
    for G in periods_data.values():
        for actor1 in all_key_actors:
            for actor2 in all_key_actors:
                if actor1 != actor2 and G.has_edge(actor1, actor2):
                    edge = tuple(sorted([actor1, actor2]))
                    connections[edge] += G[actor1][actor2]['weight']
    
    # Draw connections
    max_connection = max(connections.values()) if connections else 1
    for (actor1, actor2), weight in connections.items():
        if actor1 in pos and actor2 in pos:
            alpha = 0.2 + (weight / max_connection) * 0.4
            width = 0.5 + (weight / max_connection) * 1.5
            ax.plot([pos[actor1][0], pos[actor2][0]], 
                   [pos[actor1][1], pos[actor2][1]], 
                   color='#cccccc', alpha=alpha, linewidth=width, zorder=1)
    
    # Draw nodes - NO LABELS
    if core_actors:
        core_sizes = [400 + item[1] * 0.1 for item in persistent_by_category['stable_core']]
        ax.scatter([pos[actor][0] for actor in core_actors], 
                  [pos[actor][1] for actor in core_actors],
                  s=core_sizes, c=colors['stable_core'], 
                  alpha=0.9, edgecolors='white', linewidths=2, zorder=3)
    
    if domestic_actors:
        domestic_sizes = [250 + item[1] * 0.05 for item in persistent_by_category['domestic']]
        ax.scatter([pos[actor][0] for actor in domestic_actors], 
                  [pos[actor][1] for actor in domestic_actors],
                  s=domestic_sizes, c=colors['domestic'], 
                  alpha=0.8, edgecolors='white', linewidths=1.5, zorder=2)
    
    if intl_actors:
        intl_sizes = [200 + item[1] * 0.05 for item in persistent_by_category['international']]
        ax.scatter([pos[actor][0] for actor in intl_actors], 
                  [pos[actor][1] for actor in intl_actors],
                  s=intl_sizes, c=colors['international'], 
                  alpha=0.8, edgecolors='white', linewidths=1.5, zorder=2)
    
    # Draw hierarchy circles
    circles = [
        Circle((0, 0), 0.3, fill=False, linestyle='-', color=colors['stable_core'], 
              linewidth=2, alpha=0.6),
        Circle((0, 0), 0.6, fill=False, linestyle='--', color=colors['domestic'], 
              linewidth=1.5, alpha=0.5),
        Circle((0, 0), 0.9, fill=False, linestyle=':', color=colors['international'], 
              linewidth=1.5, alpha=0.4)
    ]
    
    for circle in circles:
        ax.add_patch(circle)
    
    # Only legend - NO name labels
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=colors['stable_core'], 
                  markersize=12, markeredgecolor='white', markeredgewidth=2, 
                  label='Stable Core'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=colors['domestic'], 
                  markersize=10, markeredgecolor='white', markeredgewidth=1.5, 
                  label='Persistent Domestic'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=colors['international'], 
                  markersize=8, markeredgecolor='white', markeredgewidth=1.5, 
                  label='International Partners')
    ]
    
    ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.98, 0.98), 
             fontsize=12, frameon=True, fancybox=True, shadow=True)
    
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-1.2, 1.2)
    ax.set_aspect('equal')
    ax.axis('off')
    
    ax.set_title('Institutional Core-Periphery Structure', fontsize=16, fontweight='bold', pad=20)
    
    plt.tight_layout()
    
    filename = OUTPUT_DIR / 'visuals' / 'academic_core_structure_no_labels.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
    plt.savefig(str(filename).replace('.png', '.pdf'), dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  ✓ Saved: {filename}")

# ============================================================================
# TASK 2: INTEGRUM Media Outlets List
# ============================================================================

def extract_integrum_media_outlets():
    """Extract list of all INTEGRUM media outlets with years"""
    df = pd.read_csv('final_nodes.csv')
    
    # Extract unique sources and their date ranges
    source_data = []
    for source, group in df.groupby('Source'):
        dates = pd.to_datetime(group['Date'], format='%d.%m.%Y %H:%M', errors='coerce')
        dates = dates.dropna()
        
        if len(dates) > 0:
            source_data.append({
                'Media_Outlet': source,
                'First_Article_Date': dates.min().strftime('%Y-%m-%d'),
                'Last_Article_Date': dates.max().strftime('%Y-%m-%d'),
                'Year_Range': f"{dates.min().year}-{dates.max().year}",
                'Total_Articles': len(group['Article_ID'].unique()),
                'Total_Mentions': group['Occurrences'].sum()
            })
    
    df_sources = pd.DataFrame(source_data).sort_values('Media_Outlet')
    
    # Save as CSV
    csv_path = OUTPUT_DIR / 'analysis' / 'integrum_media_outlets.csv'
    df_sources.to_csv(csv_path, index=False)
    print(f"  ✓ Saved: {csv_path}")
    
    # Create LaTeX appendix format
    latex_path = OUTPUT_DIR / 'documentation' / 'integrum_media_outlets_appendix.tex'
    with open(latex_path, 'w', encoding='utf-8') as f:
        f.write("\\section{INTEGRUM Media Outlets}\n")
        f.write("\\label{app:integrum_outlets}\n\n")
        f.write("The following table lists all media outlets included in the INTEGRUM dataset:\n\n")
        f.write("\\begin{longtable}{p{6cm}cccp{2cm}}\n")
        f.write("\\toprule\n")
        f.write("Media Outlet & First Date & Last Date & Year Range & Articles\\\\\n")
        f.write("\\midrule\n")
        f.write("\\endfirsthead\n")
        f.write("\\multicolumn{5}{c}{\\textit{Continued from previous page}}\\\\\n")
        f.write("\\toprule\n")
        f.write("Media Outlet & First Date & Last Date & Year Range & Articles\\\\\n")
        f.write("\\midrule\n")
        f.write("\\endhead\n")
        f.write("\\midrule\n")
        f.write("\\multicolumn{5}{r}{\\textit{Continued on next page}}\\\\\n")
        f.write("\\endfoot\n")
        f.write("\\bottomrule\n")
        f.write("\\endlastfoot\n")
        
        for _, row in df_sources.iterrows():
            outlet = row['Media_Outlet'].replace('&', '\\&').replace('_', '\\_')
            f.write(f"{outlet} & {row['First_Article_Date']} & {row['Last_Article_Date']} & "
                   f"{row['Year_Range']} & {row['Total_Articles']}\\\\\n")
        
        f.write("\\end{longtable}\n")
    
    print(f"  ✓ Saved: {latex_path}")
    return df_sources

# ============================================================================
# TASK 3: Top 50 Actors Table (All Periods Combined)
# ============================================================================

def create_top50_table_all_periods():
    """Create Top 50 Actors by Composite Score - All Periods Combined"""
    from graphing.top20overall import load_and_prepare_data, combine_all_periods, build_cooccurrence_graph, centrality_metrics, add_composite_score
    
    data = load_and_prepare_data()
    combined = combine_all_periods(data)
    
    if combined.empty:
        print("  ⚠ No data available")
        return
    
    # Build graph and calculate metrics
    g = build_cooccurrence_graph(combined)
    metrics = centrality_metrics(g, combined)
    metrics = add_composite_score(metrics)
    
    # Filter out RDIF/Dmitriev
    rdif_keywords = ['РФПИ', 'RDIF', 'Российский фонд прямых инвестиций', 'Russian Direct Investment Fund', 
                     'Дмитриев', 'Dmitriev', 'Кирилл Дмитриев', 'Kirill Dmitriev']
    mask = ~metrics['Entity'].str.contains('|'.join(rdif_keywords), case=False, na=False)
    filtered_metrics = metrics[mask]
    
    # Get top 50
    top50 = filtered_metrics.nlargest(50, 'Composite_Score').reset_index(drop=True)
    
    # Create display table
    table = pd.DataFrame({
        'Rank': range(1, len(top50) + 1),
        'Actor': top50['Entity'],
        'Composite_Score': top50['Composite_Score'].round(4),
        'Degree': top50['Degree'].round(4),
        'Closeness': top50['Closeness'].round(4),
        'Occurrences': top50['Occurrences'].astype(int),
        'Edge_Count': top50['Edge_Count'].astype(int)
    })
    
    # Save as CSV
    csv_path = OUTPUT_DIR / 'analysis' / 'top50_actors_all_periods.csv'
    table.to_csv(csv_path, index=False)
    print(f"  ✓ Saved: {csv_path}")
    
    # Create LaTeX table
    from graphing.comptable import _escape_latex
    
    latex_path = OUTPUT_DIR / 'analysis' / 'top50_actors_all_periods.tex'
    with open(latex_path, 'w', encoding='utf-8') as f:
        f.write("\\documentclass[11pt,a4paper]{article}\n")
        f.write("\\usepackage{booktabs,longtable,array,geometry,caption,siunitx}\n")
        f.write("\\geometry{margin=1in}\n")
        f.write("\\captionsetup{labelfont=bf}\n")
        f.write("\\title{Top 50 Actors by Composite Score -- All Periods Combined}\n")
        f.write("\\author{Network Analysis}\n")
        f.write("\\date{\\today}\n")
        f.write("\\begin{document}\n")
        f.write("\\maketitle\n")
        f.write("\\section{Methodology}\n")
        f.write("Composite score: $0.4\\times\\text{Degree} + 0.3\\times\\text{Closeness} + ")
        f.write("0.2\\times\\text{Norm. Occurrences} + 0.1\\times\\text{Edge Count}$. ")
        f.write("RDIF and Dmitriev entities excluded.\n")
        f.write("\\section{Results}\n")
        f.write("\\begin{longtable}{rlS[table-format=1.4]S[table-format=1.4]S[table-format=1.4]rr}\n")
        f.write("\\caption{Top 50 actors by composite score -- All periods combined}\n")
        f.write("\\label{tab:top50overall}\\\\\n")
        f.write("\\toprule\n")
        f.write("Rank & Actor & {Composite} & {Degree} & {Closeness} & Occurrences & {Edge Count}\\\\\n")
        f.write("\\midrule\n")
        f.write("\\endfirsthead\n")
        f.write("\\multicolumn{7}{c}{\\textit{Continued from previous page}}\\\\\n")
        f.write("\\toprule\n")
        f.write("Rank & Actor & {Composite} & {Degree} & {Closeness} & Occurrences & {Edge Count}\\\\\n")
        f.write("\\midrule\n")
        f.write("\\endhead\n")
        f.write("\\midrule\n")
        f.write("\\multicolumn{7}{r}{\\textit{Continued on next page}}\\\\\n")
        f.write("\\endfoot\n")
        f.write("\\bottomrule\n")
        f.write("\\endlastfoot\n")
        
        for _, row in table.iterrows():
            actor = _escape_latex(str(row['Actor']))
            f.write(f"{row['Rank']} & {actor} & {row['Composite_Score']:.4f} & ")
            f.write(f"{row['Degree']:.4f} & {row['Closeness']:.4f} & ")
            f.write(f"{row['Occurrences']} & {row['Edge_Count']} \\\\\n")
        
        f.write("\\end{longtable}\n")
        f.write("\\end{document}\n")
    
    print(f"  ✓ Saved: {latex_path}")
    return table

# ============================================================================
# TASK 4: Evolution of Jurisdictions (excluding Russia)
# ============================================================================

def create_jurisdiction_evolution_no_russia():
    """Create evolution graph for jurisdictions excluding Russia"""
    from generate_visuals_final import load_period_data
    
    period_data = load_period_data()
    
    # Calculate percentages for each period, excluding Russia
    period_stats = {}
    for period in ['Pre-Crimea', 'Post-Crimea', 'COVID', 'War']:
        df = period_data[period]
        # Filter out Russia (check for various Russia codes)
        df_no_rus = df[~df['Jurisdiction'].isin(['RUS', 'Russia', 'RU', 'Russian Federation'])]
        if len(df_no_rus) == 0:
            continue
        attr_counts = df_no_rus.groupby('Jurisdiction')['Occurrences'].sum()
        total = attr_counts.sum()
        if total > 0:
            percentages = (attr_counts / total * 100).sort_values(ascending=False)
            period_stats[period] = percentages
    
    all_values = sorted(set().union(*[set(stats.index) for stats in period_stats.values()]))
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E', 
              '#E63946', '#457B9D', '#7209B7', '#3A86FF', '#06A77D'] * 3
    
    for i, value in enumerate(all_values):
        y_values = [period_stats[period].get(value, 0) for period in ['Pre-Crimea', 'Post-Crimea', 'COVID', 'War']]
        ax.plot(['Pre-Crimea', 'Post-Crimea', 'COVID', 'War'], y_values, 
               marker='o', linewidth=2.5, markersize=7, 
               label=value, color=colors[i], alpha=0.85, 
               markerfacecolor='white', markeredgewidth=2, markeredgecolor=colors[i])
    
    ax.set_xlabel('Period', fontsize=12, fontweight='normal', color='#333333')
    ax.set_ylabel('Percentage (%)', fontsize=12, fontweight='normal', color='#333333')
    ax.set_title('Jurisdiction Evolution (Excluding Russia)', fontsize=14, fontweight='bold', 
                pad=20, color='#1a1a1a')
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9, frameon=False, ncol=1)
    ax.set_ylim(bottom=0)
    ax.spines['left'].set_color('#cccccc')
    ax.spines['bottom'].set_color('#cccccc')
    
    plt.tight_layout()
    filename = OUTPUT_DIR / 'visuals' / 'jurisdiction_evolution_no_russia.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  ✓ Saved: {filename}")

# ============================================================================
# TASK 5: Evolution of Sectors (non-financial zoom)
# ============================================================================

def create_sector_evolution_non_financial():
    """Create sector evolution graph excluding Finance sector"""
    from generate_visuals_final import load_period_data
    
    period_data = load_period_data()
    
    period_stats = {}
    for period in ['Pre-Crimea', 'Post-Crimea', 'COVID', 'War']:
        df = period_data[period]
        # Filter out Finance
        df_no_finance = df[df['Sector'] != 'Finance']
        attr_counts = df_no_finance.groupby('Sector')['Occurrences'].sum()
        total = attr_counts.sum()
        percentages = (attr_counts / total * 100).sort_values(ascending=False)
        period_stats[period] = percentages
    
    all_values = sorted(set().union(*[set(stats.index) for stats in period_stats.values()]))
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E', 
              '#E63946', '#457B9D', '#7209B7', '#3A86FF', '#06A77D'] * 3
    
    for i, value in enumerate(all_values):
        y_values = [period_stats[period].get(value, 0) for period in ['Pre-Crimea', 'Post-Crimea', 'COVID', 'War']]
        ax.plot(['Pre-Crimea', 'Post-Crimea', 'COVID', 'War'], y_values, 
               marker='o', linewidth=2.5, markersize=7, 
               label=value, color=colors[i], alpha=0.85, 
               markerfacecolor='white', markeredgewidth=2, markeredgecolor=colors[i])
    
    ax.set_xlabel('Period', fontsize=12, fontweight='normal', color='#333333')
    ax.set_ylabel('Percentage (%)', fontsize=12, fontweight='normal', color='#333333')
    ax.set_title('Sector Evolution (Non-Financial Sectors)', fontsize=14, fontweight='bold', 
                pad=20, color='#1a1a1a')
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9, frameon=False, ncol=1)
    ax.set_ylim(bottom=0)
    ax.spines['left'].set_color('#cccccc')
    ax.spines['bottom'].set_color('#cccccc')
    
    plt.tight_layout()
    filename = OUTPUT_DIR / 'visuals' / 'sector_evolution_non_financial.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  ✓ Saved: {filename}")

# ============================================================================
# TASK 6: Fix Pie Chart "Fund" Bug
# ============================================================================

def check_fund_bug():
    """Check if there's a bug with Actor Type 'Fund' in pie charts"""
    from generate_visuals_final import load_period_data
    
    period_data = load_period_data()
    
    # Check Actor Type distribution
    for period in ['Pre-Crimea', 'Post-Crimea', 'COVID', 'War']:
        df = period_data[period]
        actor_counts = df.groupby('Actor Type')['Occurrences'].sum().sort_values(ascending=False)
        print(f"\n{period} - Actor Type distribution:")
        print(actor_counts.head(10))
        
        # Check if Fund is unusually high
        if 'Fund' in actor_counts.index:
            fund_pct = (actor_counts['Fund'] / actor_counts.sum() * 100)
            print(f"  Fund percentage: {fund_pct:.2f}%")
            if fund_pct > 50:
                print(f"  ⚠ WARNING: Fund is {fund_pct:.2f}% - possible bug!")
    
    # The issue might be that RDIF is being counted as "Fund"
    # We should exclude RDIF from Actor Type analysis or verify the data

# ============================================================================
# TASK 7: Workflow Chart
# ============================================================================

def create_workflow_chart():
    """Create Python pipeline workflow chart"""
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.axis('off')
    
    # Define workflow steps
    steps = [
        ('Data Collection', 'INTEGRUM Articles', (1, 9)),
        ('NER Processing', 'Entity Extraction', (3, 9)),
        ('Data Cleaning', 'Deduplication\\nNormalization', (5, 9)),
        ('Period Splitting', '2010-2013\\n2014-2017\\n2020-2022\\n2022-2025', (7, 9)),
        ('Attribute Merging', 'Excel Attributes\\n(Sector, State/Private, etc.)', (9, 9)),
        ('Network Building', 'Co-occurrence\\nGraphs', (11, 9)),
        ('Analysis', 'Centrality\\nCommunities\\nClustering', (13, 9)),
        ('Visualization', 'Charts\\nNetworks\\nTables', (15, 9))
    ]
    
    # Draw boxes
    box_width = 1.8
    box_height = 1.2
    
    for i, (title, desc, (x, y)) in enumerate(steps):
        # Draw box
        rect = plt.Rectangle((x - box_width/2, y - box_height/2), box_width, box_height,
                            facecolor='#E8F4F8', edgecolor='#2E86AB', linewidth=2)
        ax.add_patch(rect)
        
        # Add text
        ax.text(x, y + 0.3, title, ha='center', va='center', 
               fontsize=12, fontweight='bold', color='#1a1a1a')
        ax.text(x, y - 0.2, desc, ha='center', va='center', 
               fontsize=9, color='#333333')
        
        # Draw arrow
        if i < len(steps) - 1:
            ax.arrow(x + box_width/2, y, 0.3, 0, head_width=0.15, head_length=0.1,
                    fc='#2E86AB', ec='#2E86AB', linewidth=2)
    
    ax.set_xlim(0, 17)
    ax.set_ylim(7, 11)
    ax.set_title('Python Pipeline Workflow', fontsize=16, fontweight='bold', pad=20)
    
    plt.tight_layout()
    filename = OUTPUT_DIR / 'documentation' / 'python_pipeline_workflow.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  ✓ Saved: {filename}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    print("="*80)
    print("COMPLETING ARAM'S TASKS")
    print("="*80)
    print()
    
    print("\nTASK 1: Creating academic core structure (no labels)...")
    try:
        create_academic_core_structure_no_labels()
    except Exception as e:
        print(f"  ⚠ Error: {e}")
    
    print("\nTASK 2: Extracting INTEGRUM media outlets...")
    try:
        extract_integrum_media_outlets()
    except Exception as e:
        print(f"  ⚠ Error: {e}")
    
    print("\nTASK 3: Creating Top 50 actors table...")
    try:
        create_top50_table_all_periods()
    except Exception as e:
        print(f"  ⚠ Error: {e}")
    
    print("\nTASK 4: Creating jurisdiction evolution (no Russia)...")
    try:
        create_jurisdiction_evolution_no_russia()
    except Exception as e:
        print(f"  ⚠ Error: {e}")
    
    print("\nTASK 5: Creating sector evolution (non-financial)...")
    try:
        create_sector_evolution_non_financial()
    except Exception as e:
        print(f"  ⚠ Error: {e}")
    
    print("\nTASK 6: Checking Fund bug...")
    try:
        check_fund_bug()
    except Exception as e:
        print(f"  ⚠ Error: {e}")
    
    print("\nTASK 7: Creating workflow chart...")
    try:
        create_workflow_chart()
    except Exception as e:
        print(f"  ⚠ Error: {e}")
    
    print("\n" + "="*80)
    print("ARAM'S TASKS COMPLETED!")
    print("="*80)

if __name__ == '__main__':
    main()

