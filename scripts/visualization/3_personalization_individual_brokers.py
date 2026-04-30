"""
Personalization: Individual Brokers Visualization

Shows percentage of Individual actors (brokers) across periods.
"""

import os
import sys
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from date_utils import parse_dates_vectorized, assign_period_vectorized


def create_personalization_visualization(output_dir='final visuals'):
    """Create Personalization: Individual Brokers visualization"""
    
    print("Creating Personalization: Individual Brokers visualization...")

    # Use the four period CSVs from data/periods
    period_files = {
        'Pre-Crimea': 'data/periods/pre_crimea.csv',
        'Post-Crimea': 'data/periods/post_crimea.csv',
        'COVID': 'data/periods/covid.csv',
        'War': 'data/periods/war.csv',
    }

    periods = ['Pre-Crimea', 'Post-Crimea', 'COVID', 'War']
    individual_percentages = []
    
    for period_name in periods:
        file_path = period_files.get(period_name)
        if not os.path.exists(file_path):
            print(f"⚠ Warning: {file_path} not found for {period_name}, skipping...")
            individual_percentages.append(0)
            continue

        df = pd.read_csv(file_path)

        # Check which column exists for entity type
        if 'Entity_Type' in df.columns:
            entity_type_col = 'Entity_Type'
        elif 'Actor Type' in df.columns:
            entity_type_col = 'Actor Type'
        else:
            print(f"⚠ Warning: No entity type column in {file_path}, skipping...")
            individual_percentages.append(0)
            continue

        # Check if Occurrences column exists
        if 'Occurrences' not in df.columns:
            print(f"⚠ Warning: 'Occurrences' column missing in {file_path}, skipping...")
            individual_percentages.append(0)
            continue

        # Use OCCURRENCE-WEIGHTED approach: sum occurrences per entity type
        # This captures network ACTIVITY rather than just roster composition
        df_agg = df.groupby(['Entity', entity_type_col])['Occurrences'].sum().reset_index()
        
        if df_agg.empty:
            individual_percentages.append(0)
            continue

        # Calculate weighted percentages by entity type
        per_occs = df_agg[df_agg[entity_type_col] == 'PER']['Occurrences'].sum()
        org_occs = df_agg[df_agg[entity_type_col] == 'ORG']['Occurrences'].sum()
        total_occs = per_occs + org_occs
        
        if total_occs > 0:
            individual_pct = (per_occs / total_occs * 100)
            individual_percentages.append(individual_pct)
            print(f"✓ {period_name}: {individual_pct:.1f}% (weighted by {int(per_occs):,} occurrences)")
        else:
            individual_percentages.append(0)
    
    # Create visualization (area chart in light pink)
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('white')
    
    # Light pink colors
    fill_color = '#FFB6C1'  # Light pink for fill
    line_color = '#FF69B4'  # Hot pink for line
    
    ax.fill_between(periods, 0, individual_percentages, alpha=0.5, color=fill_color)
    ax.plot(periods, individual_percentages, marker='o', linewidth=3, markersize=10,
           color=line_color, alpha=0.9)
    
    ax.set_xlabel('Period', fontsize=12, fontweight='bold')
    ax.set_ylabel('Percentage (%)', fontsize=12, fontweight='bold')
    ax.set_title('Personalization: Individual Brokers', fontsize=14, fontweight='bold', pad=15)
    ax.set_ylim(0, 50)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Add value labels
    for i, val in enumerate(individual_percentages):
        ax.text(i, val + 2, f'{val:.1f}%', ha='center', va='bottom', 
               fontsize=11, fontweight='bold', color=line_color)
    
    plt.tight_layout()
    
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'personalization_individual_brokers.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.savefig(output_file.replace('.png', '.pdf'), dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"✓ Saved: {output_file}")
    return fig


if __name__ == "__main__":
    create_personalization_visualization()
