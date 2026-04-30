"""
Jurisdiction Evolution Visualization (Excluding Russia)

Creates a line chart showing how non-Russian jurisdictions evolve across periods,
providing a clearer view of international partner changes over time.
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


def create_jurisdiction_evolution_no_russia(input_file='data/periods/final_nodes_edges.csv',
                                            output_dir='final visuals',
                                            min_percentage=0.1):
    """
    Create jurisdiction evolution chart excluding Russia
    
    Parameters:
    -----------
    input_file : str
        Path to final_nodes_edges.csv
    output_dir : str
        Directory to save output
    min_percentage : float
        Minimum percentage threshold to include jurisdiction (default 0.1%)
    """
    
    print("=" * 80)
    print("Jurisdiction Evolution (Excluding Russia)")
    print("=" * 80)
    
    # Load data
    print(f"\nLoading {input_file}...")
    df = pd.read_csv(input_file)
    print(f"Loaded {len(df):,} rows")
    
    # Parse dates and assign periods (vectorized)
    print("\nParsing dates and assigning periods...")
    df['Date'] = parse_dates_vectorized(df['Date'])
    df['Year'] = df['Date'].dt.year
    df['Period'] = assign_period_vectorized(df['Date'])
    
    # Filter out invalid dates/periods
    df = df[df['Period'].notna()].copy()
    print(f"Valid periods: {len(df):,} rows")
    
    # Filter out Russia (check for various Russia codes)
    russia_codes = ['RUS', 'Russia', 'RU', 'Russian Federation', 'Unknown']
    df_no_russia = df[~df['Jurisdiction'].isin(russia_codes)].copy()
    print(f"After excluding Russia: {len(df_no_russia):,} rows ({len(df_no_russia)/len(df)*100:.1f}%)")
    
    # Calculate percentages for each period
    periods = ['Pre-Crimea', 'Post-Crimea', 'COVID', 'War']
    period_stats = {}
    
    print("\nCalculating jurisdiction percentages per period...")
    for period in periods:
        period_df = df_no_russia[df_no_russia['Period'] == period]
        
        if len(period_df) == 0:
            print(f"  Warning: No data for {period}")
            period_stats[period] = pd.Series(dtype=float)
            continue
        
        # Count occurrences per jurisdiction
        jurisdiction_counts = period_df.groupby('Jurisdiction')['Occurrences'].sum()
        total = jurisdiction_counts.sum()
        
        if total > 0:
            percentages = (jurisdiction_counts / total * 100).sort_values(ascending=False)
            period_stats[period] = percentages
            print(f"  {period}: {len(percentages)} jurisdictions, total mentions: {total:,}")
        else:
            period_stats[period] = pd.Series(dtype=float)
    
    # Get all jurisdictions that appear in any period
    all_jurisdictions = set()
    for stats in period_stats.values():
        all_jurisdictions.update(stats.index)
    
    # Filter to jurisdictions that meet minimum threshold in at least one period
    significant_jurisdictions = set()
    for jurisdiction in all_jurisdictions:
        max_pct = max([stats.get(jurisdiction, 0) for stats in period_stats.values()])
        if max_pct >= min_percentage:
            significant_jurisdictions.add(jurisdiction)
    
    print(f"\nSignificant jurisdictions (>= {min_percentage}% in at least one period): {len(significant_jurisdictions)}")
    
    # Create visualization
    fig, ax = plt.subplots(figsize=(14, 8))
    fig.patch.set_facecolor('white')
    
    # Color palette for jurisdictions
    # Use distinct colors for major jurisdictions
    major_colors = {
        'INT': '#e74c3c',      # Red for International
        'EU': '#3498db',        # Blue for EU
        'USA': '#f39c12',       # Orange for USA
        'UK': '#9b59b6',        # Purple for UK
        'CN': '#e67e22',        # Brown for China
        'UKR': '#2ecc71',       # Green for Ukraine
        'FR': '#1abc9c',         # Teal for France
        'DE': '#34495e',         # Dark gray for Germany
    }
    
    # Generate colors for other jurisdictions
    other_colors = plt.cm.tab20(np.linspace(0, 1, max(20, len(significant_jurisdictions))))
    color_map = {}
    other_idx = 0
    
    for jurisdiction in sorted(significant_jurisdictions):
        if jurisdiction in major_colors:
            color_map[jurisdiction] = major_colors[jurisdiction]
        else:
            color_map[jurisdiction] = other_colors[other_idx % len(other_colors)]
            other_idx += 1
    
    # Plot lines for each jurisdiction
    plotted_jurisdictions = []
    for jurisdiction in sorted(significant_jurisdictions):
        y_values = [period_stats[period].get(jurisdiction, 0) for period in periods]
        
        # Only plot if at least one value is above threshold
        if max(y_values) >= min_percentage:
            color = color_map[jurisdiction]
            linewidth = 2.5 if jurisdiction in major_colors else 2.0
            alpha = 0.9 if jurisdiction in major_colors else 0.7
            
            ax.plot(periods, y_values, 
                   marker='o', linewidth=linewidth, markersize=7,
                   label=jurisdiction, color=color, alpha=alpha,
                   markerfacecolor='white', markeredgewidth=2, 
                   markeredgecolor=color)
            plotted_jurisdictions.append(jurisdiction)
    
    # Styling
    ax.set_xlabel('Period', fontsize=13, fontweight='bold', color='#333333')
    ax.set_ylabel('Percentage (%)', fontsize=13, fontweight='bold', color='#333333')
    ax.set_title('Jurisdiction Evolution (Excluding Russia)', 
                fontsize=16, fontweight='bold', pad=20, color='#2c3e50')
    
    # Grid
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    ax.set_axisbelow(True)
    
    # Y-axis formatting
    ax.set_ylim(bottom=0)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1f}%'))
    
    # Legend - only show significant jurisdictions
    # Sort legend by maximum value across periods
    legend_order = sorted(plotted_jurisdictions, 
                         key=lambda j: max([period_stats[p].get(j, 0) for p in periods]),
                         reverse=True)
    
    # Limit legend to top jurisdictions if too many
    max_legend_items = 20
    if len(legend_order) > max_legend_items:
        # Show top N in legend, rest as "Others"
        top_jurisdictions = legend_order[:max_legend_items]
        other_jurisdictions = legend_order[max_legend_items:]
        
        # Create "Others" line (aggregate)
        others_y = []
        for period in periods:
            others_sum = sum([period_stats[period].get(j, 0) for j in other_jurisdictions])
            others_y.append(others_sum)
        
        ax.plot(periods, others_y, marker='o', linewidth=2, markersize=6,
               label=f'Others ({len(other_jurisdictions)} jurisdictions)', 
               color='#95a5a6', alpha=0.6, linestyle='--',
               markerfacecolor='white', markeredgewidth=1.5, markeredgecolor='#95a5a6')
        
        legend_items = top_jurisdictions + [f'Others ({len(other_jurisdictions)} jurisdictions)']
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
    output_file = os.path.join(output_dir, 'jurisdiction_evolution_no_russia.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white', pad_inches=0.2)
    plt.savefig(output_file.replace('.png', '.pdf'), dpi=300, bbox_inches='tight', 
               facecolor='white', pad_inches=0.2)
    
    print(f"\n✓ Saved visualization: {output_file}")
    
    # Create summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    
    summary_data = []
    for jurisdiction in sorted(plotted_jurisdictions):
        values = [period_stats[period].get(jurisdiction, 0) for period in periods]
        summary_data.append({
            'Jurisdiction': jurisdiction,
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
    summary_file = os.path.join(output_dir, 'jurisdiction_evolution_summary.csv')
    summary_df.to_csv(summary_file, index=False, encoding='utf-8-sig')
    print(f"✓ Saved summary: {summary_file}")
    
    print("\nTop 10 jurisdictions by maximum percentage:")
    print(summary_df.head(10)[['Jurisdiction', 'Pre-Crimea', 'Post-Crimea', 'COVID', 'War']].to_string(index=False))
    
    plt.close()
    
    return fig, summary_df


if __name__ == "__main__":
    fig, summary = create_jurisdiction_evolution_no_russia()
    print("\n" + "=" * 80)
    print("✓ Jurisdiction evolution visualization complete!")
    print("=" * 80)
