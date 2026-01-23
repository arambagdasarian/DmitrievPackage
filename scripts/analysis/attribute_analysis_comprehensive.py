#!/usr/bin/env python3
"""
Comprehensive Attribute Analysis for Dmitriev Network
Generates all requested visualizations
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from collections import Counter, defaultdict
import warnings
warnings.filterwarnings('ignore')

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (15, 10)
plt.rcParams['font.size'] = 10

# Load network data
print("Loading network data...")
with open('network_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

nodes = data['nodes']
edges = data['edges']

print(f"Loaded {len(nodes)} nodes and {len(edges)} edges")

# Convert to DataFrame for easier analysis
df = pd.DataFrame(nodes)

# Define period order
PERIODS = ['Pre-Crimea', 'Post-Crimea', 'COVID', 'War']
PERIOD_COLORS = {
    'Pre-Crimea': '#3498db',
    'Post-Crimea': '#e74c3c', 
    'COVID': '#f39c12',
    'War': '#2c3e50'
}

# ============================================================================
# ANALYSIS 1: COMPOSITION CHANGES OVER FOUR PERIODS
# ============================================================================
print("\n" + "="*80)
print("ANALYSIS 1: Composition Changes Over Four Periods")
print("="*80)

def create_period_compositions():
    """Create pie charts for each period and evolution graphs"""
    
    attributes = ['sector', 'state_private', 'actor_type', 'jurisdiction']
    
    for attr in attributes:
        print(f"\nAnalyzing {attr}...")
        
        # Create figure with subplots for pie charts
        fig, axes = plt.subplots(2, 2, figsize=(20, 16))
        fig.suptitle(f'{attr.replace("_", " ").title()} Composition Across Periods', 
                     fontsize=20, fontweight='bold', y=0.995)
        
        axes = axes.flatten()
        
        period_data = {}
        
        for idx, period in enumerate(PERIODS):
            # Get nodes active in this period
            period_nodes = [n for n in nodes if period in n['periods']]
            
            # Count attribute values
            attr_counts = Counter([n[attr] for n in period_nodes])
            period_data[period] = attr_counts
            
            # Create pie chart
            ax = axes[idx]
            colors = sns.color_palette("husl", len(attr_counts))
            
            wedges, texts, autotexts = ax.pie(
                attr_counts.values(),
                labels=attr_counts.keys(),
                autopct='%1.1f%%',
                startangle=90,
                colors=colors,
                textprops={'fontsize': 10}
            )
            
            ax.set_title(f'{period}\n({len(period_nodes)} entities)', 
                        fontsize=14, fontweight='bold')
            
            # Make percentage text bold
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(9)
        
        plt.tight_layout()
        plt.savefig(f'visuals/1_composition_pie_{attr}.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Saved pie charts: visuals/1_composition_pie_{attr}.png")
        
        # Create evolution graph
        fig, ax = plt.subplots(figsize=(16, 10))
        
        # Get all unique values for this attribute
        all_values = sorted(set([n[attr] for n in nodes]))
        
        # Create data for line plot
        evolution_data = {val: [] for val in all_values}
        
        for period in PERIODS:
            period_nodes = [n for n in nodes if period in n['periods']]
            total = len(period_nodes)
            
            for val in all_values:
                count = sum(1 for n in period_nodes if n[attr] == val)
                percentage = (count / total * 100) if total > 0 else 0
                evolution_data[val].append(percentage)
        
        # Plot lines
        for val, percentages in evolution_data.items():
            ax.plot(PERIODS, percentages, marker='o', linewidth=3, 
                   markersize=10, label=val)
        
        ax.set_xlabel('Period', fontsize=14, fontweight='bold')
        ax.set_ylabel('Percentage of Network (%)', fontsize=14, fontweight='bold')
        ax.set_title(f'Evolution of {attr.replace("_", " ").title()} Across Periods', 
                    fontsize=18, fontweight='bold')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=11)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, max([max(v) for v in evolution_data.values()]) * 1.1)
        
        plt.tight_layout()
        plt.savefig(f'visuals/1_evolution_line_{attr}.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Saved evolution graph: visuals/1_evolution_line_{attr}.png")

# ============================================================================
# ANALYSIS 2: TOP 50 VS OVERALL NETWORK
# ============================================================================
print("\n" + "="*80)
print("ANALYSIS 2: Top 50 vs Overall Network Composition")
print("="*80)

def create_top50_comparison():
    """Create comparative pie charts for top 50 vs overall network"""
    
    attributes = ['sector', 'state_private', 'actor_type', 'jurisdiction']
    
    for period in PERIODS:
        print(f"\nAnalyzing {period}...")
        
        # Get nodes active in this period
        period_nodes = [n for n in nodes if period in n['periods']]
        
        # Get top 50 by mentions in this period
        period_nodes_sorted = sorted(period_nodes, 
                                    key=lambda x: x['period_counts'].get(period, 0), 
                                    reverse=True)
        top50 = period_nodes_sorted[:50]
        
        # Create figure with subplots
        fig, axes = plt.subplots(len(attributes), 2, figsize=(20, 6*len(attributes)))
        fig.suptitle(f'{period}: Top 50 vs Overall Network Composition', 
                     fontsize=20, fontweight='bold')
        
        for idx, attr in enumerate(attributes):
            # Overall network
            overall_counts = Counter([n[attr] for n in period_nodes])
            ax1 = axes[idx, 0]
            colors = sns.color_palette("husl", len(overall_counts))
            
            wedges, texts, autotexts = ax1.pie(
                overall_counts.values(),
                labels=overall_counts.keys(),
                autopct='%1.1f%%',
                startangle=90,
                colors=colors,
                textprops={'fontsize': 9}
            )
            
            ax1.set_title(f'{attr.replace("_", " ").title()} - Overall Network ({len(period_nodes)} entities)', 
                         fontsize=12, fontweight='bold')
            
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
            
            # Top 50
            top50_counts = Counter([n[attr] for n in top50])
            ax2 = axes[idx, 1]
            
            wedges, texts, autotexts = ax2.pie(
                top50_counts.values(),
                labels=top50_counts.keys(),
                autopct='%1.1f%%',
                startangle=90,
                colors=colors,
                textprops={'fontsize': 9}
            )
            
            ax2.set_title(f'{attr.replace("_", " ").title()} - Top 50 Actors', 
                         fontsize=12, fontweight='bold')
            
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
        
        plt.tight_layout()
        plt.savefig(f'visuals/2_top50_comparison_{period}.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Saved comparison: visuals/2_top50_comparison_{period}.png")

# ============================================================================
# ANALYSIS 3: SECTOR COMPOSITION & INSTITUTIONAL REPURPOSING
# ============================================================================
print("\n" + "="*80)
print("ANALYSIS 3: Sector Composition & Institutional Repurposing")
print("="*80)

def analyze_sector_composition():
    """Analyze sector composition and institutional repurposing"""
    
    # Create comprehensive table
    print("\nCreating sector composition tables...")
    
    results = []
    
    for period in PERIODS:
        period_nodes = [n for n in nodes if period in n['periods']]
        period_nodes_sorted = sorted(period_nodes, 
                                    key=lambda x: x['period_counts'].get(period, 0), 
                                    reverse=True)
        
        # Overall network
        overall_sectors = Counter([n['sector'] for n in period_nodes])
        
        # Top 20
        top20 = period_nodes_sorted[:20]
        top20_sectors = Counter([n['sector'] for n in top20])
        
        # Top 50
        top50 = period_nodes_sorted[:50]
        top50_sectors = Counter([n['sector'] for n in top50])
        
        for sector in set([n['sector'] for n in nodes]):
            results.append({
                'Period': period,
                'Sector': sector,
                'Overall_Count': overall_sectors.get(sector, 0),
                'Overall_Pct': (overall_sectors.get(sector, 0) / len(period_nodes) * 100),
                'Top20_Count': top20_sectors.get(sector, 0),
                'Top20_Pct': (top20_sectors.get(sector, 0) / 20 * 100),
                'Top50_Count': top50_sectors.get(sector, 0),
                'Top50_Pct': (top50_sectors.get(sector, 0) / 50 * 100)
            })
    
    results_df = pd.DataFrame(results)
    results_df.to_csv('visuals/3_sector_composition_table.csv', index=False)
    print(f"  ✓ Saved table: visuals/3_sector_composition_table.csv")
    
    # Create visualization
    fig, axes = plt.subplots(2, 2, figsize=(24, 16))
    fig.suptitle('Sector Composition: Overall vs Top20 vs Top50', 
                 fontsize=20, fontweight='bold')
    
    axes = axes.flatten()
    
    for idx, period in enumerate(PERIODS):
        ax = axes[idx]
        period_data = results_df[results_df['Period'] == period]
        
        x = np.arange(len(period_data['Sector'].unique()))
        width = 0.25
        
        sectors = sorted(period_data['Sector'].unique())
        overall_pcts = [period_data[period_data['Sector'] == s]['Overall_Pct'].values[0] 
                       for s in sectors]
        top20_pcts = [period_data[period_data['Sector'] == s]['Top20_Pct'].values[0] 
                     for s in sectors]
        top50_pcts = [period_data[period_data['Sector'] == s]['Top50_Pct'].values[0] 
                     for s in sectors]
        
        ax.bar(x - width, overall_pcts, width, label='Overall Network', alpha=0.8)
        ax.bar(x, top20_pcts, width, label='Top 20', alpha=0.8)
        ax.bar(x + width, top50_pcts, width, label='Top 50', alpha=0.8)
        
        ax.set_xlabel('Sector', fontsize=12, fontweight='bold')
        ax.set_ylabel('Percentage (%)', fontsize=12, fontweight='bold')
        ax.set_title(period, fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(sectors, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig('visuals/3_sector_composition_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Saved visualization: visuals/3_sector_composition_comparison.png")

# ============================================================================
# ANALYSIS 4: CLUSTERING TRENDS - STATE VS PRIVATE
# ============================================================================
print("\n" + "="*80)
print("ANALYSIS 4: Clustering Trends - State vs Private/Economic Actors")
print("="*80)

def analyze_clustering_trends():
    """Analyze trends in state vs private/economic clustering"""
    
    # Evolution of state/private composition
    fig, axes = plt.subplots(2, 2, figsize=(20, 16))
    fig.suptitle('Clustering Trends: Evolution of Actor Attributes', 
                 fontsize=20, fontweight='bold')
    
    attributes = ['state_private', 'actor_type', 'sector', 'jurisdiction']
    axes = axes.flatten()
    
    for idx, attr in enumerate(attributes):
        ax = axes[idx]
        
        # Calculate weighted percentages (by mentions)
        all_values = sorted(set([n[attr] for n in nodes]))
        
        evolution_data = {val: [] for val in all_values}
        
        for period in PERIODS:
            period_nodes = [n for n in nodes if period in n['periods']]
            
            # Weight by mentions in period
            total_mentions = sum(n['period_counts'].get(period, 0) for n in period_nodes)
            
            for val in all_values:
                val_mentions = sum(n['period_counts'].get(period, 0) 
                                  for n in period_nodes if n[attr] == val)
                percentage = (val_mentions / total_mentions * 100) if total_mentions > 0 else 0
                evolution_data[val].append(percentage)
        
        # Plot stacked area chart
        ax.stackplot(PERIODS, evolution_data.values(), 
                    labels=evolution_data.keys(),
                    alpha=0.8)
        
        ax.set_xlabel('Period', fontsize=12, fontweight='bold')
        ax.set_ylabel('Weighted Percentage (%)', fontsize=12, fontweight='bold')
        ax.set_title(f'{attr.replace("_", " ").title()} (weighted by mentions)', 
                    fontsize=14, fontweight='bold')
        ax.legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize=9)
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('visuals/4_clustering_trends_stacked.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Saved visualization: visuals/4_clustering_trends_stacked.png")
    
    # Create detailed state vs private analysis
    fig, axes = plt.subplots(1, 2, figsize=(20, 8))
    
    # Count-based
    ax1 = axes[0]
    state_counts = []
    private_counts = []
    mixed_counts = []
    
    for period in PERIODS:
        period_nodes = [n for n in nodes if period in n['periods']]
        state_counts.append(sum(1 for n in period_nodes if n['state_private'] == 'State'))
        private_counts.append(sum(1 for n in period_nodes if n['state_private'] == 'Private'))
        mixed_counts.append(sum(1 for n in period_nodes 
                               if n['state_private'] not in ['State', 'Private']))
    
    x = np.arange(len(PERIODS))
    width = 0.25
    
    ax1.bar(x - width, state_counts, width, label='State', alpha=0.8)
    ax1.bar(x, private_counts, width, label='Private', alpha=0.8)
    ax1.bar(x + width, mixed_counts, width, label='Mixed/Other', alpha=0.8)
    
    ax1.set_xlabel('Period', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Number of Entities', fontsize=12, fontweight='bold')
    ax1.set_title('State vs Private: Entity Count', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(PERIODS)
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Mention-weighted
    ax2 = axes[1]
    state_mentions = []
    private_mentions = []
    mixed_mentions = []
    
    for period in PERIODS:
        period_nodes = [n for n in nodes if period in n['periods']]
        total = sum(n['period_counts'].get(period, 0) for n in period_nodes)
        
        state = sum(n['period_counts'].get(period, 0) for n in period_nodes 
                   if n['state_private'] == 'State')
        private = sum(n['period_counts'].get(period, 0) for n in period_nodes 
                     if n['state_private'] == 'Private')
        mixed = sum(n['period_counts'].get(period, 0) for n in period_nodes 
                   if n['state_private'] not in ['State', 'Private'])
        
        state_mentions.append(state / total * 100 if total > 0 else 0)
        private_mentions.append(private / total * 100 if total > 0 else 0)
        mixed_mentions.append(mixed / total * 100 if total > 0 else 0)
    
    ax2.bar(x - width, state_mentions, width, label='State', alpha=0.8)
    ax2.bar(x, private_mentions, width, label='Private', alpha=0.8)
    ax2.bar(x + width, mixed_mentions, width, label='Mixed/Other', alpha=0.8)
    
    ax2.set_xlabel('Period', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Percentage of Mentions (%)', fontsize=12, fontweight='bold')
    ax2.set_title('State vs Private: Mention Share', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(PERIODS)
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig('visuals/4_state_private_evolution.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Saved visualization: visuals/4_state_private_evolution.png")

# Create output directory
import os
os.makedirs('visuals', exist_ok=True)

# Run all analyses
create_period_compositions()
create_top50_comparison()
analyze_sector_composition()
analyze_clustering_trends()

print("\n" + "="*80)
print("✅ Analysis complete! Check the 'visuals/' directory for outputs.")
print("="*80)



