"""
Sector Evolution Visualizations

Creates two visualizations:
1. Full sector evolution (including Finance) - shows dominance of finance
2. Sector evolution excluding Finance - zoomed view of non-financial sectors
"""

import os
import sys
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from date_utils import parse_dates_vectorized, assign_period_vectorized


def create_sector_evolution(input_file='data/periods/final_nodes_edges.csv',
                            output_dir='final visuals',
                            exclude_finance=False,
                            min_percentage=0.1):
    """
    Create sector evolution chart
    
    Parameters:
    -----------
    input_file : str
        Path to final_nodes_edges.csv
    output_dir : str
        Directory to save output
    exclude_finance : bool
        If True, exclude Finance sector to zoom into non-financial sectors
    min_percentage : float
        Minimum percentage threshold to include sector (default 0.1%)
    """
    
    title_suffix = " (Excluding Finance)" if exclude_finance else ""
    print("=" * 80)
    print(f"Sector Evolution{title_suffix}")
    print("=" * 80)
    
    # Load data
    print(f"\nLoading {input_file}...")
    df = pd.read_csv(input_file)
    print(f"Loaded {len(df):,} rows")
    
    # Filter out rows without Sector
    df = df[df['Sector'].notna()].copy()
    print(f"Rows with Sector data: {len(df):,}")
    
    # Filter out Finance if requested
    if exclude_finance:
        df = df[df['Sector'] != 'Finance'].copy()
        print(f"After excluding Finance: {len(df):,} rows")
    
    # Parse dates and assign periods (vectorized)
    print("\nParsing dates and assigning periods...")
    df['Date'] = parse_dates_vectorized(df['Date'])
    df['Year'] = df['Date'].dt.year
    df['Period'] = assign_period_vectorized(df['Date'])
    
    # Filter out invalid dates/periods
    df = df[df['Period'].notna()].copy()
    print(f"Valid periods: {len(df):,} rows")
    
    # Calculate percentages for each period
    periods = ['Pre-Crimea', 'Post-Crimea', 'COVID', 'War']
    period_stats = {}
    
    print("\nCalculating sector percentages per period...")
    for period in periods:
        period_df = df[df['Period'] == period]
        
        if len(period_df) == 0:
            print(f"  Warning: No data for {period}")
            period_stats[period] = pd.Series(dtype=float)
            continue
        
        # Count occurrences per sector
        sector_counts = period_df.groupby('Sector')['Occurrences'].sum()
        total = sector_counts.sum()
        
        if total > 0:
            percentages = (sector_counts / total * 100).sort_values(ascending=False)
            period_stats[period] = percentages
            print(f"  {period}: {len(percentages)} sectors, total mentions: {total:,}")
        else:
            period_stats[period] = pd.Series(dtype=float)
    
    # Get all sectors that appear in any period
    all_sectors = set()
    for stats in period_stats.values():
        all_sectors.update(stats.index)
    
    # Filter to sectors that meet minimum threshold in at least one period
    significant_sectors = set()
    for sector in all_sectors:
        max_pct = max([stats.get(sector, 0) for stats in period_stats.values()])
        if max_pct >= min_percentage:
            significant_sectors.add(sector)
    
    print(f"\nSignificant sectors (>= {min_percentage}% in at least one period): {len(significant_sectors)}")
    
    # Create visualization
    fig, ax = plt.subplots(figsize=(14, 8))
    fig.patch.set_facecolor('white')
    
    # Color palette for sectors
    # Use distinct colors for major sectors
    major_colors = {
        'Finance': '#e74c3c',        # Red for Finance (dominant)
        'Government': '#3498db',      # Blue for Government
        'Business': '#f39c12',        # Orange for Business
        'Health': '#2ecc71',          # Green for Health
        'Politics': '#9b59b6',        # Purple for Politics
        'Energy': '#e67e22',          # Brown for Energy
        'Diplomacy': '#1abc9c',       # Teal for Diplomacy
        'Military': '#34495e',        # Dark gray for Military
        'Infrastructure': '#16a085',  # Dark teal
        'Tech': '#d35400',            # Dark orange
    }
    
    # Generate colors for other sectors
    other_colors = plt.cm.tab20(np.linspace(0, 1, max(20, len(significant_sectors))))
    color_map = {}
    other_idx = 0
    
    for sector in sorted(significant_sectors):
        if sector in major_colors:
            color_map[sector] = major_colors[sector]
        else:
            color_map[sector] = other_colors[other_idx % len(other_colors)]
            other_idx += 1
    
    # Plot lines for each sector
    plotted_sectors = []
    for sector in sorted(significant_sectors):
        y_values = [period_stats[period].get(sector, 0) for period in periods]
        
        # Only plot if at least one value is above threshold
        if max(y_values) >= min_percentage:
            color = color_map[sector]
            # Make Finance line thicker if included
            linewidth = 3.0 if (sector == 'Finance' and not exclude_finance) else 2.5
            alpha = 0.95 if sector in major_colors else 0.7
            
            ax.plot(periods, y_values, 
                   marker='o', linewidth=linewidth, markersize=7,
                   label=sector, color=color, alpha=alpha,
                   markerfacecolor='white', markeredgewidth=2, 
                   markeredgecolor=color)
            plotted_sectors.append(sector)
    
    # Styling
    ax.set_xlabel('Period', fontsize=13, fontweight='bold', color='#333333')
    ax.set_ylabel('Percentage (%)', fontsize=13, fontweight='bold', color='#333333')
    
    title = 'Sector Evolution' + title_suffix
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20, color='#2c3e50')
    
    # Grid
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    ax.set_axisbelow(True)
    
    # Y-axis formatting
    ax.set_ylim(bottom=0)
    if exclude_finance:
        # Zoom in for non-financial sectors - set max to show detail
        max_val = max([max([period_stats[p].get(s, 0) for s in plotted_sectors]) 
                      for p in periods])
        ax.set_ylim(top=min(max_val * 1.1, 100))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1f}%'))
    
    # Legend - sort by maximum value across periods
    legend_order = sorted(plotted_sectors, 
                         key=lambda s: max([period_stats[p].get(s, 0) for p in periods]),
                         reverse=True)
    
    # Limit legend to top sectors if too many
    max_legend_items = 25
    if len(legend_order) > max_legend_items:
        top_sectors = legend_order[:max_legend_items]
        other_sectors = legend_order[max_legend_items:]
        
        # Create "Others" line (aggregate)
        others_y = []
        for period in periods:
            others_sum = sum([period_stats[period].get(s, 0) for s in other_sectors])
            others_y.append(others_sum)
        
        ax.plot(periods, others_y, marker='o', linewidth=2, markersize=6,
               label=f'Others ({len(other_sectors)} sectors)', 
               color='#95a5a6', alpha=0.6, linestyle='--',
               markerfacecolor='white', markeredgewidth=1.5, markeredgecolor='#95a5a6')
        
        legend_items = top_sectors + [f'Others ({len(other_sectors)} sectors)']
    else:
        legend_items = legend_order
    
    # Create legend with custom order
    handles, labels = ax.get_legend_handles_labels()
    handle_map = {label: handle for handle, label in zip(handles, labels)}
    ordered_handles = [handle_map[label] for label in legend_items if label in handle_map]
    ordered_labels = [label for label in legend_items if label in handle_map]
    
    ax.legend(ordered_handles, ordered_labels, 
             loc='upper left', bbox_to_anchor=(1.02, 1),
             fontsize=10, frameon=True, fancybox=True, shadow=False,
             ncol=1, columnspacing=0.5)
    
    plt.tight_layout()
    
    # Save
    os.makedirs(output_dir, exist_ok=True)
    if exclude_finance:
        output_file = os.path.join(output_dir, 'sector_evolution_no_finance.png')
    else:
        output_file = os.path.join(output_dir, 'sector_evolution.png')
    
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white', pad_inches=0.2)
    plt.savefig(output_file.replace('.png', '.pdf'), dpi=300, bbox_inches='tight', 
               facecolor='white', pad_inches=0.2)
    
    print(f"\n✓ Saved visualization: {output_file}")
    
    # Create summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    
    summary_data = []
    for sector in sorted(plotted_sectors):
        values = [period_stats[period].get(sector, 0) for period in periods]
        summary_data.append({
            'Sector': sector,
            'Pre-Crimea': f"{values[0]:.2f}%",
            'Post-Crimea': f"{values[1]:.2f}%",
            'COVID': f"{values[2]:.2f}%",
            'War': f"{values[3]:.2f}%",
            'Max': f"{max(values):.2f}%",
            'Change (War - Pre)': f"{values[3] - values[0]:.2f}%"
        })
    
    summary_df = pd.DataFrame(summary_data)
    summary_df = summary_df.sort_values('Max', key=lambda x: x.str.rstrip('%').astype(float), 
                                        ascending=False)
    
    # Save summary
    if exclude_finance:
        summary_file = os.path.join(output_dir, 'sector_evolution_no_finance_summary.csv')
    else:
        summary_file = os.path.join(output_dir, 'sector_evolution_summary.csv')
    
    summary_df.to_csv(summary_file, index=False, encoding='utf-8-sig')
    print(f"✓ Saved summary: {summary_file}")
    
    print("\nTop 10 sectors by maximum percentage:")
    print(summary_df.head(10)[['Sector', 'Pre-Crimea', 'Post-Crimea', 'COVID', 'War']].to_string(index=False))
    
    plt.close()
    
    return fig, summary_df


def main():
    """Create both sector evolution visualizations"""
    
    print("Creating Sector Evolution Visualizations")
    print("=" * 80)
    
    # 1. Full sector evolution (with Finance)
    print("\n" + "=" * 80)
    print("1. Creating FULL sector evolution (including Finance)")
    print("=" * 80)
    fig1, summary1 = create_sector_evolution(
        exclude_finance=False,
        min_percentage=0.1
    )
    
    # 2. Sector evolution excluding Finance
    print("\n" + "=" * 80)
    print("2. Creating sector evolution EXCLUDING Finance (zoomed view)")
    print("=" * 80)
    fig2, summary2 = create_sector_evolution(
        exclude_finance=True,
        min_percentage=0.1
    )
    
    print("\n" + "=" * 80)
    print("✓ Both sector evolution visualizations complete!")
    print("=" * 80)
    print("\nFiles created:")
    print("  • sector_evolution.png/pdf - Full evolution (shows Finance dominance)")
    print("  • sector_evolution_no_finance.png/pdf - Zoomed view (excludes Finance)")
    print("  • sector_evolution_summary.csv - Summary statistics (full)")
    print("  • sector_evolution_no_finance_summary.csv - Summary statistics (no Finance)")


if __name__ == "__main__":
    main()
