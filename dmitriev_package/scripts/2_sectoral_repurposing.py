"""
Sectoral Repurposing Visualization

Shows evolution of Finance, Government, Health, and Diplomacy sectors.
"""

import os
import sys
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from date_utils import parse_dates_vectorized, assign_period_vectorized


def create_sectoral_repurposing_visualization(output_dir='final visuals'):
    """Create Sectoral Repurposing visualization"""
    
    print("Creating Sectoral Repurposing visualization...")

    # Use the four period CSVs from data/periods
    period_files = {
        'Pre-Crimea': 'data/periods/pre_crimea.csv',
        'Post-Crimea': 'data/periods/post_crimea.csv',
        'COVID': 'data/periods/covid.csv',
        'War': 'data/periods/war.csv',
    }

    key_sectors = ['Finance', 'Government', 'Health', 'Diplomacy']
    periods = ['Pre-Crimea', 'Post-Crimea', 'COVID', 'War']
    period_stats = {}

    for period_name in periods:
        file_path = period_files.get(period_name)
        if not os.path.exists(file_path):
            print(f"⚠ Warning: {file_path} not found for {period_name}, skipping...")
            continue

        df = pd.read_csv(file_path)

        if 'Sector' not in df.columns:
            print(f"⚠ Warning: 'Sector' column missing in {file_path}, skipping...")
            continue

        # Get UNIQUE ENTITIES with sector info
        df_unique = df[['Entity', 'Sector']].dropna(subset=['Sector']).drop_duplicates(subset=['Entity'])
        
        # Filter to ONLY the 4 key sectors (for sectoral repurposing analysis)
        df_key = df_unique[df_unique['Sector'].isin(key_sectors)]
        
        if df_key.empty:
            continue

        # Count unique entities per sector
        sector_counts = df_key['Sector'].value_counts()
        total_key_sectors = len(df_key)

        if total_key_sectors > 0:
            # Calculate percentages out of ONLY the 4 key sectors
            # (shows how network shifts BETWEEN these strategic sectors)
            period_stats[period_name] = {
                'Finance': (sector_counts.get('Finance', 0) / total_key_sectors * 100),
                'Government': (sector_counts.get('Government', 0) / total_key_sectors * 100),
                'Health': (sector_counts.get('Health', 0) / total_key_sectors * 100),
                'Diplomacy': (sector_counts.get('Diplomacy', 0) / total_key_sectors * 100)
            }
            
            print(f"✓ {period_name}: {total_key_sectors} entities in key sectors")
    
    # Create visualization
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('white')
    
    colors = {
        'Finance': '#3498db',
        'Government': '#f39c12',
        'Health': '#2ecc71',
        'Diplomacy': '#9b59b6'
    }
    
    for sector in key_sectors:
        values = [period_stats.get(p, {}).get(sector, 0) for p in periods]
        ax.plot(periods, values, marker='o', linewidth=2.5, markersize=8,
               label=sector, color=colors[sector], alpha=0.9)
    
    ax.set_xlabel('Period', fontsize=12, fontweight='bold')
    ax.set_ylabel('Percentage (%)', fontsize=12, fontweight='bold')
    ax.set_title('Sectoral Repurposing', fontsize=14, fontweight='bold', pad=15)
    ax.set_ylim(0, 65)  # Increased to show Government sector at ~58%
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='best', fontsize=11, frameon=True, fancybox=True)
    
    plt.tight_layout()
    
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'sectoral_repurposing.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.savefig(output_file.replace('.png', '.pdf'), dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"✓ Saved: {output_file}")
    return fig


if __name__ == "__main__":
    create_sectoral_repurposing_visualization()
