"""
Robustness Check: Compare Full Network vs. Two National Media Outlets

This script compares network patterns between:
1. Full network (all media outlets)
2. Network with only 2 major national media outlets

The goal is to verify that similar patterns emerge regardless of source selection.
"""

import networkx as nx
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import defaultdict, Counter
import os
import seaborn as sns


class RobustnessChecker:
    """Compare network patterns across different source selections"""
    
    def __init__(self):
        # Select 2 major national media outlets for robustness check
        # Using top outlets: ТАСС and РИА Новости (various sections)
        self.selected_outlets = [
            'ТАСС - Российские новости',
            'РИА Новости. Все Новости'
        ]
        
        # Core entities for classification
        self.core_entities = [
            'Владимир Путин', 'Внешэкономбанк (ВЭБ)', 'Сбербанк', 'Банк ВТБ',
            'ОАО «Газпром»', 'Роснефть', 'ОАО «РЖД»', 'Министерство финансов',
            'Совет Федерации', 'Московская биржа', 'Дмитрий Медведев',
            'Федеральная антимонопольная служба (ФАС)', 'МВД', 'Банк России'
        ]
    
    def classify_node_category(self, entity_name, jurisdiction=None):
        """Classify nodes into categories based on entity name and jurisdiction"""
        entity_lower = entity_name.lower()
        
        # Check if it's a stable core entity
        if any(core.lower() in entity_lower or entity_lower in core.lower() 
               for core in self.core_entities):
            return 'stable_core'
        
        # Use jurisdiction if available (more reliable)
        if jurisdiction:
            russian_jurisdictions = ['RUS', 'Russia', 'RU', 'Russian Federation']
            if jurisdiction in russian_jurisdictions:
                return 'domestic'
            elif jurisdiction not in ['Unknown', None, '']:
                return 'international'
        
        # Fallback to name-based classification
        russian_indicators = [
            'российский', 'russia', 'moscow', 'москва', 'санкт-петербург',
            'минфин', 'министерство', 'федеральн', 'госуд', 'рос', 'мин',
            'дума', 'совет', 'банк', 'фонд', 'роснефть', 'газпром'
        ]
        
        if any(indicator in entity_lower for indicator in russian_indicators):
            return 'domestic'
        
        # Default to international if not clearly Russian
        return 'international'
    
    def create_network_from_dataframe(self, df, min_edge_weight=20):
        """Create network from DataFrame"""
        article_entities = df.groupby('Article_ID')['Entity'].apply(list).reset_index()
        
        edge_weights = {}
        for _, row in article_entities.iterrows():
            entities = row['Entity']
            if len(entities) < 2:
                continue
                
            for i in range(len(entities)):
                for j in range(i + 1, len(entities)):
                    entity1, entity2 = entities[i], entities[j]
                    edge = tuple(sorted([entity1, entity2]))
                    edge_weights[edge] = edge_weights.get(edge, 0) + 1
        
        # Filter for significant connections
        filtered_edges = [(e[0], e[1], w) for e, w in edge_weights.items() if w >= min_edge_weight]
        
        G = nx.Graph()
        G.add_weighted_edges_from(filtered_edges)
        
        # Add node attributes
        node_attributes = df.groupby('Entity').agg({
            'Occurrences': 'sum',
            'Entity_Type': 'first',
            'Jurisdiction': 'first'
        }).to_dict()
        
        for node in G.nodes():
            if node in node_attributes['Occurrences']:
                G.nodes[node]['total_occurrences'] = node_attributes['Occurrences'][node]
                G.nodes[node]['entity_type'] = node_attributes['Entity_Type'][node]
                G.nodes[node]['jurisdiction'] = node_attributes['Jurisdiction'][node]
            else:
                G.nodes[node]['total_occurrences'] = 0
                G.nodes[node]['entity_type'] = 'Unknown'
                G.nodes[node]['jurisdiction'] = 'Unknown'
            
            # Use jurisdiction for classification
            jurisdiction = G.nodes[node]['jurisdiction']
            G.nodes[node]['node_category'] = self.classify_node_category(node, jurisdiction)
        
        return G
    
    def calculate_network_metrics(self, G, name=""):
        """Calculate comprehensive network metrics"""
        if len(G.nodes()) == 0:
            return {}
        
        metrics = {
            'name': name,
            'nodes': G.number_of_nodes(),
            'edges': G.number_of_edges(),
            'density': nx.density(G),
            'avg_clustering': nx.average_clustering(G),
            'is_connected': nx.is_connected(G),
        }
        
        # Connected components
        components = list(nx.connected_components(G))
        metrics['num_components'] = len(components)
        if components:
            metrics['largest_component_size'] = len(max(components, key=len))
            metrics['largest_component_pct'] = len(max(components, key=len)) / len(G.nodes()) * 100
        else:
            metrics['largest_component_size'] = 0
            metrics['largest_component_pct'] = 0
        
        # Centrality measures
        try:
            degrees = dict(G.degree())
            metrics['avg_degree'] = np.mean(list(degrees.values()))
            metrics['max_degree'] = max(degrees.values())
            
            # Top nodes by degree
            top_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:10]
            metrics['top_10_nodes'] = [node for node, _ in top_nodes]
            
            # Betweenness centrality (sample for large networks)
            if len(G.nodes()) <= 100:
                betweenness = nx.betweenness_centrality(G)
            else:
                betweenness = nx.betweenness_centrality(G, k=min(100, len(G.nodes())))
            metrics['avg_betweenness'] = np.mean(list(betweenness.values()))
            metrics['max_betweenness'] = max(betweenness.values())
            
        except Exception as e:
            print(f"Warning calculating centrality for {name}: {e}")
            metrics['avg_degree'] = 0
            metrics['max_degree'] = 0
        
        # Category distribution
        categories = Counter([G.nodes[node]['node_category'] for node in G.nodes()])
        metrics['stable_core_count'] = categories.get('stable_core', 0)
        metrics['domestic_count'] = categories.get('domestic', 0)
        metrics['international_count'] = categories.get('international', 0)
        
        return metrics
    
    def compare_networks(self, df_full, df_filtered, min_edge_weight=20):
        """Compare full network vs filtered network"""
        
        print("=" * 80)
        print("ROBUSTNESS CHECK: Full Network vs. Two National Media Outlets")
        print("=" * 80)
        
        print(f"\nSelected outlets for robustness check:")
        for outlet in self.selected_outlets:
            print(f"  - {outlet}")
        
        print(f"\nFull dataset: {len(df_full):,} rows, {df_full['Article_ID'].nunique():,} articles")
        print(f"Filtered dataset: {len(df_filtered):,} rows, {df_filtered['Article_ID'].nunique():,} articles")
        print(f"Reduction: {(1 - len(df_filtered)/len(df_full))*100:.1f}% of rows")
        
        # Create networks
        print("\nCreating networks...")
        G_full = self.create_network_from_dataframe(df_full, min_edge_weight=min_edge_weight)
        G_filtered = self.create_network_from_dataframe(df_filtered, min_edge_weight=min_edge_weight)
        
        print(f"Full network: {G_full.number_of_nodes()} nodes, {G_full.number_of_edges()} edges")
        print(f"Filtered network: {G_filtered.number_of_nodes()} nodes, {G_filtered.number_of_edges()} edges")
        
        # Calculate metrics
        print("\nCalculating network metrics...")
        metrics_full = self.calculate_network_metrics(G_full, "Full Network")
        metrics_filtered = self.calculate_network_metrics(G_filtered, "Two Outlets Only")
        
        # Compare metrics
        print("\n" + "=" * 80)
        print("NETWORK METRICS COMPARISON")
        print("=" * 80)
        
        comparison = pd.DataFrame({
            'Full Network': metrics_full,
            'Two Outlets': metrics_filtered
        }).T
        
        # Display key metrics
        key_metrics = ['nodes', 'edges', 'density', 'avg_clustering', 
                      'largest_component_pct', 'avg_degree',
                      'stable_core_count', 'domestic_count', 'international_count']
        
        print("\nKey Metrics:")
        print(comparison[key_metrics].to_string())
        
        # Calculate similarity scores
        print("\n" + "=" * 80)
        print("PATTERN SIMILARITY ANALYSIS")
        print("=" * 80)
        
        # Top nodes overlap
        top_full = set(metrics_full.get('top_10_nodes', []))
        top_filtered = set(metrics_filtered.get('top_10_nodes', []))
        overlap = top_full & top_filtered
        overlap_pct = len(overlap) / len(top_full) * 100 if top_full else 0
        
        print(f"\nTop 10 nodes overlap: {len(overlap)}/{len(top_full)} ({overlap_pct:.1f}%)")
        if overlap:
            print(f"  Overlapping nodes: {', '.join(list(overlap)[:5])}...")
        
        # Category distribution similarity
        cat_full = {
            'stable_core': metrics_full.get('stable_core_count', 0),
            'domestic': metrics_full.get('domestic_count', 0),
            'international': metrics_full.get('international_count', 0)
        }
        cat_filtered = {
            'stable_core': metrics_filtered.get('stable_core_count', 0),
            'domestic': metrics_filtered.get('domestic_count', 0),
            'international': metrics_filtered.get('international_count', 0)
        }
        
        print(f"\nCategory Distribution:")
        print(f"  Full Network - Core: {cat_full['stable_core']}, Domestic: {cat_full['domestic']}, Intl: {cat_full['international']}")
        print(f"  Two Outlets - Core: {cat_filtered['stable_core']}, Domestic: {cat_filtered['domestic']}, Intl: {cat_filtered['international']}")
        
        # Calculate relative differences
        print(f"\nRelative Differences (Two Outlets / Full Network):")
        for metric in ['density', 'avg_clustering', 'largest_component_pct', 'avg_degree']:
            val_full = metrics_full.get(metric, 0)
            val_filtered = metrics_filtered.get(metric, 0)
            if val_full > 0:
                ratio = val_filtered / val_full
                print(f"  {metric}: {ratio:.2f}x ({ratio*100:.1f}%)")
        
        return G_full, G_filtered, metrics_full, metrics_filtered, comparison
    
    def visualize_comparison(self, G_full, G_filtered, metrics_full, metrics_filtered, 
                            save_path=None):
        """Create side-by-side visualization"""
        
        fig = plt.figure(figsize=(20, 10))
        fig.patch.set_facecolor('white')
        
        # Create subplots
        gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)
        
        # Network visualizations
        ax1 = fig.add_subplot(gs[0, 0])
        ax2 = fig.add_subplot(gs[0, 1])
        ax3 = fig.add_subplot(gs[0, 2])
        
        # Metrics comparison
        ax4 = fig.add_subplot(gs[1, :])
        
        # Colors
        colors = {
            'stable_core': '#2c3e50',
            'domestic': '#5b9bd5',
            'international': '#c55a5a'
        }
        
        # Plot full network
        if G_full.number_of_nodes() > 0:
            pos_full = nx.spring_layout(G_full, k=1, iterations=50, seed=42)
            
            # Draw edges
            nx.draw_networkx_edges(G_full, pos_full, ax=ax1, alpha=0.2, 
                                   edge_color='gray', width=0.5)
            
            # Draw nodes by category
            for category, color in colors.items():
                nodes = [n for n in G_full.nodes() 
                        if G_full.nodes[n]['node_category'] == category]
                if nodes:
                    nx.draw_networkx_nodes(G_full, pos_full, nodelist=nodes,
                                          node_color=color, node_size=50,
                                          alpha=0.8, ax=ax1)
            
            ax1.set_title(f'Full Network\n{metrics_full["nodes"]} nodes, {metrics_full["edges"]} edges',
                         fontsize=12, fontweight='bold')
            ax1.axis('off')
        
        # Plot filtered network
        if G_filtered.number_of_nodes() > 0:
            pos_filtered = nx.spring_layout(G_filtered, k=1, iterations=50, seed=42)
            
            # Draw edges
            nx.draw_networkx_edges(G_filtered, pos_filtered, ax=ax2, alpha=0.2,
                                   edge_color='gray', width=0.5)
            
            # Draw nodes by category
            for category, color in colors.items():
                nodes = [n for n in G_filtered.nodes() 
                        if G_filtered.nodes[n]['node_category'] == category]
                if nodes:
                    nx.draw_networkx_nodes(G_filtered, pos_filtered, nodelist=nodes,
                                          node_color=color, node_size=50,
                                          alpha=0.8, ax=ax2)
            
            ax2.set_title(f'Two Outlets Only\n{metrics_filtered["nodes"]} nodes, {metrics_filtered["edges"]} edges',
                         fontsize=12, fontweight='bold')
            ax2.axis('off')
        
        # Category distribution comparison
        categories = ['stable_core', 'domestic', 'international']
        full_counts = [metrics_full.get(f'{cat}_count', 0) for cat in categories]
        filtered_counts = [metrics_filtered.get(f'{cat}_count', 0) for cat in categories]
        
        x = np.arange(len(categories))
        width = 0.35
        
        ax3.bar(x - width/2, full_counts, width, label='Full Network', 
               color='#34495e', alpha=0.8)
        ax3.bar(x + width/2, filtered_counts, width, label='Two Outlets', 
               color='#e74c3c', alpha=0.8)
        ax3.set_xlabel('Category', fontsize=11)
        ax3.set_ylabel('Count', fontsize=11)
        ax3.set_title('Category Distribution Comparison', fontsize=12, fontweight='bold')
        ax3.set_xticks(x)
        ax3.set_xticklabels(['Stable Core', 'Domestic', 'International'])
        ax3.legend()
        ax3.grid(axis='y', alpha=0.3)
        
        # Metrics comparison bar chart
        metrics_to_compare = ['density', 'avg_clustering', 'largest_component_pct', 'avg_degree']
        metric_labels = ['Density', 'Avg Clustering', 'Largest Component %', 'Avg Degree']
        
        full_vals = [metrics_full.get(m, 0) for m in metrics_to_compare]
        filtered_vals = [metrics_filtered.get(m, 0) for m in metrics_to_compare]
        
        # Normalize for comparison (show as percentage of full network)
        normalized_vals = []
        for i, m in enumerate(metrics_to_compare):
            if full_vals[i] > 0:
                normalized_vals.append(filtered_vals[i] / full_vals[i] * 100)
            else:
                normalized_vals.append(0)
        
        x_metrics = np.arange(len(metrics_to_compare))
        ax4.bar(x_metrics, normalized_vals, color='#3498db', alpha=0.8)
        ax4.axhline(y=100, color='r', linestyle='--', linewidth=2, label='100% (Full Network)')
        ax4.set_xlabel('Metric', fontsize=11)
        ax4.set_ylabel('Percentage of Full Network', fontsize=11)
        ax4.set_title('Network Metrics: Two Outlets as % of Full Network', 
                     fontsize=12, fontweight='bold')
        ax4.set_xticks(x_metrics)
        ax4.set_xticklabels(metric_labels, rotation=45, ha='right')
        ax4.legend()
        ax4.grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for i, val in enumerate(normalized_vals):
            ax4.text(i, val + 2, f'{val:.1f}%', ha='center', va='bottom', fontsize=10)
        
        plt.suptitle('Robustness Check: Full Network vs. Two National Media Outlets',
                    fontsize=16, fontweight='bold', y=0.98)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.savefig(save_path.replace('.png', '.pdf'), dpi=300, bbox_inches='tight', 
                       facecolor='white')
            print(f"\n✓ Saved visualization: {save_path}")
        
        plt.close()
        return fig


def main():
    """Run robustness check"""
    
    # Load data
    print("Loading data...")
    df_full = pd.read_csv('data/periods/final_nodes_edges.csv')
    print(f"Loaded {len(df_full):,} rows from full dataset")
    
    # Filter to selected outlets
    checker = RobustnessChecker()
    df_filtered = df_full[df_full['Source'].isin(checker.selected_outlets)].copy()
    print(f"Filtered to {len(df_filtered):,} rows from selected outlets")
    
    # Run comparison
    G_full, G_filtered, metrics_full, metrics_filtered, comparison = checker.compare_networks(
        df_full, df_filtered, min_edge_weight=20
    )
    
    # Save comparison table
    output_dir = "final visuals"
    os.makedirs(output_dir, exist_ok=True)
    
    comparison_file = os.path.join(output_dir, "robustness_check_comparison.csv")
    comparison.to_csv(comparison_file, encoding='utf-8-sig')
    print(f"\n✓ Saved comparison table: {comparison_file}")
    
    # Create visualization
    print("\nCreating visualization...")
    viz_file = os.path.join(output_dir, "robustness_check_comparison.png")
    checker.visualize_comparison(G_full, G_filtered, metrics_full, metrics_filtered, 
                                save_path=viz_file)
    
    # Save detailed report
    report_file = os.path.join(output_dir, "robustness_check_report.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("ROBUSTNESS CHECK REPORT\n")
        f.write("Full Network vs. Two National Media Outlets\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("Selected Outlets:\n")
        for outlet in checker.selected_outlets:
            f.write(f"  - {outlet}\n")
        f.write("\n")
        
        f.write("Data Summary:\n")
        f.write(f"  Full dataset: {len(df_full):,} rows, {df_full['Article_ID'].nunique():,} articles\n")
        f.write(f"  Filtered dataset: {len(df_filtered):,} rows, {df_filtered['Article_ID'].nunique():,} articles\n")
        f.write(f"  Reduction: {(1 - len(df_filtered)/len(df_full))*100:.1f}% of rows\n\n")
        
        f.write("Network Metrics:\n")
        f.write(comparison.to_string())
        f.write("\n\n")
        
        f.write("Conclusion:\n")
        f.write("=" * 80 + "\n")
        f.write("The robustness check compares network patterns between the full dataset\n")
        f.write("and a subset using only two major national media outlets.\n")
        f.write("Similar patterns suggest the findings are robust to source selection.\n")
    
    print(f"✓ Saved report: {report_file}")
    
    print("\n" + "=" * 80)
    print("✓ Robustness check complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
