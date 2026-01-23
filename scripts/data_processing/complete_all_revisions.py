#!/usr/bin/env python3
"""
Complete All Remaining Revision Tasks from Finalization Document
Based on reading of both the Finalization document and the current paper PDF
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
import sys

warnings.filterwarnings('ignore')

# Import from generate_visuals_final
sys.path.insert(0, '.')
from generate_visuals_final import load_period_data, build_network_from_period_data

# Configuration
OUTPUT_DIR = Path('deliverables')
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.joinpath('visuals').mkdir(exist_ok=True)

PERIODS = ['Pre-Crimea', 'Post-Crimea', 'COVID', 'War']

# ============================================================================
# TASK: Louvain Communities WITHOUT Name Labels
# ============================================================================

def create_louvain_communities_no_labels():
    """Create Louvain community visualizations for all four periods without name labels"""
    from generate_visuals_final import detect_louvain_communities
    
    period_data = load_period_data()
    attributes = ['Sector', 'State/Private', 'Actor Type', 'Jurisdiction']
    PALETTE = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E', 
               '#E63946', '#457B9D', '#7209B7', '#3A86FF', '#06A77D']
    
    for period in PERIODS:
        df = period_data[period]
        G = build_network_from_period_data(df, min_edge_weight=2)
        
        if G.number_of_nodes() == 0:
            print(f"  ⚠ No network data for {period}")
            continue
        
        # Detect communities using the same method as generate_visuals_final
        partition = detect_louvain_communities(G)
        nx.set_node_attributes(G, partition, 'community')
        
        for attribute in attributes:
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
            
            # Draw nodes - NO LABELS
            node_sizes = [min(400, max(30, G.nodes[node].get('Occurrences', 1) * 4)) for node in G.nodes()]
            nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors, 
                                  node_size=node_sizes, alpha=0.85, 
                                  edgecolors='white', linewidths=1)
            
            # NO NAME LABELS - REMOVED
            
            # Clean legend
            legend_elements = [plt.Line2D([0], [0], marker='o', color='w', 
                                         markerfacecolor=color_map[attr], 
                                         markersize=10, markeredgecolor='white',
                                         markeredgewidth=1, label=attr)
                              for attr in unique_attrs[:10]]  # Limit legend items
            
            ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1),
                     fontsize=9, frameon=True, fancybox=True, shadow=False, ncol=1)
            
            ax.set_title(f'Louvain Communities - {period}\n{attribute}', 
                        fontsize=14, fontweight='bold', pad=20)
            ax.axis('off')
            
            plt.tight_layout()
            
            filename = OUTPUT_DIR / 'visuals' / f'5_louvain_{attr_key}_{period.replace(" ", "_")}_NO_LABELS.png'
            plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            print(f"  ✓ Saved: {filename}")

# ============================================================================
# TASK: Evolution of Core/Domestic/International WITHOUT Labels
# ============================================================================

def create_core_domestic_international_evolution_no_labels():
    """Create evolution visualization of core, domestic, and international partners without labels"""
    period_data = load_period_data()
    
    # Classify actors as core, domestic, or international for each period
    period_stats = {}
    
    for period in PERIODS:
        df = period_data[period]
        G = build_network_from_period_data(df, min_edge_weight=2)
        
        if G.number_of_nodes() == 0:
            continue
        
        # Calculate centrality to identify core
        degrees = dict(G.degree())
        top_central = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:20]
        core_actors = set([actor for actor, _ in top_central])
        
        # Classify by jurisdiction
        domestic = []
        international = []
        core = []
        
        for node in G.nodes():
            jurisdiction = G.nodes[node].get('Jurisdiction', 'Unknown')
            occurrences = G.nodes[node].get('Occurrences', 0)
            
            if node in core_actors:
                core.append(occurrences)
            elif jurisdiction in ['RUS', 'Russia', 'RU', 'Russian Federation']:
                domestic.append(occurrences)
            else:
                international.append(occurrences)
        
        period_stats[period] = {
            'Core': sum(core),
            'Domestic': sum(domestic),
            'International': sum(international)
        }
    
    # Create visualization
    fig, ax = plt.subplots(figsize=(12, 7))
    
    periods_short = ['Pre-Crimea', 'Post-Crimea', 'COVID', 'War']
    core_vals = [period_stats[p]['Core'] for p in periods_short]
    domestic_vals = [period_stats[p]['Domestic'] for p in periods_short]
    intl_vals = [period_stats[p]['International'] for p in periods_short]
    
    x = np.arange(len(periods_short))
    width = 0.25
    
    bars1 = ax.bar(x - width, core_vals, width, label='Stable Core', color='#E74C3C', alpha=0.85)
    bars2 = ax.bar(x, domestic_vals, width, label='Persistent Domestic', color='#3498DB', alpha=0.85)
    bars3 = ax.bar(x + width, intl_vals, width, label='International Partners', color='#2ECC71', alpha=0.85)
    
    ax.set_xlabel('Period', fontsize=12, fontweight='normal', color='#333333')
    ax.set_ylabel('Total Occurrences', fontsize=12, fontweight='normal', color='#333333')
    ax.set_title('Evolution of Core, Domestic Network and International Partners', 
                fontsize=14, fontweight='bold', pad=20, color='#1a1a1a')
    ax.set_xticks(x)
    ax.set_xticklabels(periods_short)
    ax.legend(loc='upper left', fontsize=11, frameon=True, fancybox=True)
    ax.spines['left'].set_color('#cccccc')
    ax.spines['bottom'].set_color('#cccccc')
    
    plt.tight_layout()
    filename = OUTPUT_DIR / 'visuals' / 'evolution_core_domestic_international_NO_LABELS.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  ✓ Saved: {filename}")

# ============================================================================
# TASK: Period-Specific Visuals with "Gone" and "Newly Joined" Tables
# ============================================================================

def create_period_actor_changes():
    """For each period, create visual and table showing actors that left (gone) and newly joined"""
    period_data = load_period_data()
    
    # Track actors across periods
    period_actors = {}
    for period in PERIODS:
        df = period_data[period]
        G = build_network_from_period_data(df, min_edge_weight=2)
        period_actors[period] = set(G.nodes())
    
    # For each period (except first), identify gone and newly joined
    for i, period in enumerate(PERIODS[1:], 1):
        prev_period = PERIODS[i-1]
        
        gone_actors = period_actors[prev_period] - period_actors[period]
        new_actors = period_actors[period] - period_actors[prev_period]
        
        # Filter to significant actors (top 20 by occurrences)
        df_current = period_data[period]
        df_prev = period_data[prev_period]
        
        # Get occurrences for classification
        gone_with_occ = []
        for actor in gone_actors:
            prev_occ = df_prev[df_prev['Entity'] == actor]['Occurrences'].sum()
            if prev_occ > 0:
                gone_with_occ.append((actor, prev_occ))
        
        new_with_occ = []
        for actor in new_actors:
            curr_occ = df_current[df_current['Entity'] == actor]['Occurrences'].sum()
            if curr_occ > 0:
                new_with_occ.append((actor, curr_occ))
        
        # Sort and take top
        gone_sorted = sorted(gone_with_occ, key=lambda x: x[1], reverse=True)[:15]
        new_sorted = sorted(new_with_occ, key=lambda x: x[1], reverse=True)[:15]
        
        # Create visualization
        G_current = build_network_from_period_data(df_current, min_edge_weight=2)
        
        if G_current.number_of_nodes() == 0:
            continue
        
        # Color nodes: red for gone, green for new, gray for persistent
        node_colors = []
        for node in G_current.nodes():
            if node in new_actors:
                node_colors.append('#2ECC71')  # Green for new
            elif node in gone_actors:
                node_colors.append('#E74C3C')  # Red for gone
            else:
                node_colors.append('#95A5A6')  # Gray for persistent
        
        pos = nx.spring_layout(G_current, k=1.5, iterations=50, seed=42)
        
        fig, ax = plt.subplots(figsize=(14, 10))
        
        # Draw edges
        nx.draw_networkx_edges(G_current, pos, ax=ax, alpha=0.1, width=0.2, edge_color='#cccccc')
        
        # Draw nodes - NO LABELS
        node_sizes = [min(400, max(30, G_current.nodes[node].get('Occurrences', 1) * 4)) 
                     for node in G_current.nodes()]
        nx.draw_networkx_nodes(G_current, pos, ax=ax, node_color=node_colors, 
                              node_size=node_sizes, alpha=0.85, 
                              edgecolors='white', linewidths=1)
        
        # Legend for colors
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#2ECC71', 
                      markersize=12, markeredgecolor='white', label='Newly Joined'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#E74C3C', 
                      markersize=12, markeredgecolor='white', label='Gone'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#95A5A6', 
                      markersize=12, markeredgecolor='white', label='Persistent')
        ]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=11)
        
        ax.set_title(f'Actor Changes: {prev_period} → {period}\n(No Name Labels)', 
                    fontsize=14, fontweight='bold', pad=20)
        ax.axis('off')
        
        plt.tight_layout()
        filename = OUTPUT_DIR / 'visuals' / f'actor_changes_{period.replace(" ", "_")}_NO_LABELS.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        print(f"  ✓ Saved: {filename}")
        
        # Create LaTeX table for gone and newly joined actors
        latex_table = create_actor_changes_table(gone_sorted, new_sorted, period, prev_period)
        latex_path = OUTPUT_DIR / 'analysis' / f'actor_changes_{period.replace(" ", "_")}.tex'
        latex_path.write_text(latex_table, encoding='utf-8')
        print(f"  ✓ Saved: {latex_path}")

def create_actor_changes_table(gone, new, period, prev_period):
    """Create LaTeX table for actor changes"""
    def escape_latex(text):
        return str(text).replace('&', '\\&').replace('_', '\\_').replace('%', '\\%')
    
    latex = f"""\\begin{{table}}[htbp]
\\centering
\\caption{{Actors Leaving and Joining: {prev_period} → {period}}}
\\label{{tab:actor_changes_{period.replace(" ", "_").lower()}}}
\\begin{{tabular}}{{p{{6cm}}cp{{6cm}}c}}
\\toprule
\\multicolumn{{2}}{{c}}{{Gone Actors}} & \\multicolumn{{2}}{{c}}{{Newly Joined Actors}} \\\\
\\midrule
"""
    
    max_len = max(len(gone), len(new))
    for i in range(max_len):
        if i < len(gone):
            actor_gone = escape_latex(gone[i][0][:50])
            occ_gone = gone[i][1]
            latex += f"{actor_gone} & {occ_gone}"
        else:
            latex += " & "
        
        latex += " & "
        
        if i < len(new):
            actor_new = escape_latex(new[i][0][:50])
            occ_new = new[i][1]
            latex += f"{actor_new} & {occ_new}"
        else:
            latex += " & "
        
        latex += " \\\\\n"
    
    latex += """\\bottomrule
\\end{tabular}
\\end{table}
"""
    return latex

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    print("="*80)
    print("COMPLETING ALL REMAINING REVISION TASKS")
    print("="*80)
    print()
    
    print("\nTASK 1: Creating Louvain communities WITHOUT name labels...")
    try:
        create_louvain_communities_no_labels()
    except Exception as e:
        print(f"  ⚠ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nTASK 2: Creating core/domestic/international evolution WITHOUT labels...")
    try:
        create_core_domestic_international_evolution_no_labels()
    except Exception as e:
        print(f"  ⚠ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nTASK 3: Creating period-specific actor changes (gone/newly joined)...")
    try:
        create_period_actor_changes()
    except Exception as e:
        print(f"  ⚠ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("ALL REMAINING TASKS COMPLETED!")
    print("="*80)

if __name__ == '__main__':
    main()

