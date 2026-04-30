"""
Statization of Network Visualization

Shows the evolution of State vs Private percentage across periods.
"""

import os
import sys
import pandas as pd
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['font.family'] = 'DejaVu Sans'
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from date_utils import parse_dates_vectorized, assign_period_vectorized


def create_statization_visualization(output_dir='final visuals'):
    """Create Statization of Network visualization"""
    
    print("Creating Statization of Network visualization...")

    # Use the four period CSVs from data/periods
    period_files = {
        'Pre-Crimea': 'data/periods/pre_crimea.csv',
        'Post-Crimea': 'data/periods/post_crimea.csv',
        'COVID': 'data/periods/covid.csv',
        'War': 'data/periods/war.csv',
    }

    periods = ['Pre-Crimea', 'Post-Crimea', 'COVID', 'War']
    period_stats = {}

    for period_name in periods:
        file_path = period_files.get(period_name)
        if not os.path.exists(file_path):
            print(f"⚠ Warning: {file_path} not found for {period_name}, skipping...")
            continue

        df = pd.read_csv(file_path)

        if 'State/Private' not in df.columns:
            print(f"⚠ Warning: 'State/Private' column missing in {file_path}, skipping...")
            continue

        # We want UNIQUE ENTITIES within this period file
        df = df[['Entity', 'State/Private']].copy()
        df = df[df['State/Private'].notna()].copy()
        df = df.drop_duplicates(subset=['Entity'])

        if df.empty:
            continue

        state_private_counts = df['State/Private'].value_counts()
        total = state_private_counts.sum()

        if total > 0:
            percentages = (state_private_counts / total * 100)
            period_stats[period_name] = {
                'State': percentages.get('State', 0),
                'Private': percentages.get('Private', 0)
            }
    
    # Create visualization
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('white')
    
    state_values = [period_stats.get(p, {}).get('State', 0) for p in periods]
    private_values = [period_stats.get(p, {}).get('Private', 0) for p in periods]
    
    ax.plot(periods, state_values, marker='o', linewidth=3, markersize=10,
           label='State', color='#e74c3c', alpha=0.9)
    ax.plot(periods, private_values, marker='o', linewidth=3, markersize=10,
           label='Private', color='#2ecc71', alpha=0.9)
    
    ax.set_xlabel('Period', fontsize=12, fontweight='bold')
    ax.set_ylabel('Percentage (%)', fontsize=12, fontweight='bold')
    ax.set_title('Statization of Network', fontsize=14, fontweight='bold', pad=15)
    ax.set_ylim(0, 100)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='best', fontsize=11, frameon=True, fancybox=True)
    
    # Add value labels
    for i, (s, p) in enumerate(zip(state_values, private_values)):
        ax.text(i, s + 2, f'{s:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold', color='#e74c3c')
        ax.text(i, p - 2, f'{p:.1f}%', ha='center', va='top', fontsize=10, fontweight='bold', color='#2ecc71')
    
    plt.tight_layout()
    
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'statization_of_network.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.savefig(output_file.replace('.png', '.pdf'), dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"✓ Saved: {output_file}")
    return fig


if __name__ == "__main__":
    create_statization_visualization()
