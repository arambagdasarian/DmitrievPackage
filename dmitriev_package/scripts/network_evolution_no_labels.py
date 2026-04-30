"""
Network Evolution Visualization (No Labels)

Creates a 2x2 grid showing network evolution across four periods
with NO node labels - only colors and structure to show core stability
and international flexibility.
"""

import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from collections import defaultdict
import os


class NetworkEvolutionNoLabels:
    """Create network evolution visualization without labels"""
    
    def __init__(self):
        # Define stable domestic core entities
        self.core_entities = [
            'Владимир Путин', 'Внешэкономбанк (ВЭБ)', 'Сбербанк', 'Банк ВТБ',
            'ОАО «Газпром»', 'Роснефть', 'ОАО «РЖД»', 'Министерство финансов',
            'Совет Федерации', 'Московская биржа', 'Дмитрий Медведев',
            'Федеральная антимонопольная служба (ФАС)', 'МВД', 'Банк России'
        ]
        
        # Academic color palette
        self.colors = {
            'stable_core': '#2c3e50',        # Dark grey (stable institutions)
            'domestic': '#5b9bd5',           # Light blue (domestic actors)
            'international': '#c55a5a',      # Reddish-brown (international partners)
            'edges': '#d3d3d3'               # Light gray (connections)
        }
    
    def classify_node_category(self, entity_name, jurisdiction=None):
        """Classify nodes into categories"""
        entity_lower = entity_name.lower()
        
        # Check if it's a stable core entity
        if any(core.lower() in entity_lower or entity_lower in core.lower() 
               for core in self.core_entities):
            return 'stable_core'
        
        # Use jurisdiction if available
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
        
        return 'international'
    
    def create_network_from_csv(self, file_path, min_edge_weight=20):
        """Create network from CSV file"""
        df = pd.read_csv(file_path)
        
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
        
        # Filter for significant connections only
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
    
    def get_top_nodes_by_category(self, G, n_per_category=6):
        """Get top nodes by category for cleaner visualization"""
        stable_core_nodes = []
        domestic_nodes = []
        international_nodes = []
        
        # Separate nodes by category and get degree centrality
        degrees = dict(G.degree())
        
        for node in G.nodes():
            category = G.nodes[node]['node_category']
            if category == 'stable_core':
                stable_core_nodes.append((node, degrees[node]))
            elif category == 'domestic':
                domestic_nodes.append((node, degrees[node]))
            elif category == 'international':
                international_nodes.append((node, degrees[node]))
        
        # Sort by degree and take top N
        stable_core_nodes = sorted(stable_core_nodes, key=lambda x: x[1], reverse=True)[:n_per_category]
        domestic_nodes = sorted(domestic_nodes, key=lambda x: x[1], reverse=True)[:n_per_category]
        international_nodes = sorted(international_nodes, key=lambda x: x[1], reverse=True)[:n_per_category]
        
        return ([n[0] for n in stable_core_nodes], 
                [n[0] for n in domestic_nodes], 
                [n[0] for n in international_nodes])
    
    def create_network_evolution_no_labels(self, periods_data, save_path=None):
        """
        Create network evolution visualization in 2x2 grid - NO LABELS
        """
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.patch.set_facecolor('white')
        
        periods = ['pre_crimea', 'post_crimea', 'covid', 'war']
        period_names = ['Pre-Crimea\n(2012-2014)', 'Post-Crimea\n(2014-2017)', 
                       'COVID-19\n(2020-2022)', 'War Period\n(2022-2024)']
        
        for idx, (period, period_name) in enumerate(zip(periods, period_names)):
            row, col = idx // 2, idx % 2
            ax = axes[row, col]
            
            if period not in periods_data:
                ax.text(0.5, 0.5, 'No data available', ha='center', va='center', 
                       transform=ax.transAxes, fontsize=12)
                ax.set_title(period_name, fontsize=14, fontweight='bold')
                ax.axis('off')
                continue
            
            G = periods_data[period]
            
            # Get top nodes by category for cleaner visualization
            stable_core, domestic, international = self.get_top_nodes_by_category(G, n_per_category=6)
            
            # Create subgraph with only these key nodes
            key_nodes = stable_core + domestic + international
            if key_nodes:
                G_sub = G.subgraph(key_nodes).copy()
            else:
                G_sub = G.copy()
            
            if G_sub.number_of_nodes() == 0:
                ax.text(0.5, 0.5, 'No significant\nconnections', ha='center', va='center', 
                       transform=ax.transAxes, fontsize=12)
                ax.set_title(period_name, fontsize=14, fontweight='bold')
                ax.axis('off')
                continue
            
            # Use spring layout with good spacing
            pos = nx.spring_layout(G_sub, k=3, iterations=50, seed=42)
            
            # Draw edges with weight-based thickness
            if G_sub.number_of_edges() > 0:
                edge_weights = [G_sub[u][v]['weight'] for u, v in G_sub.edges()]
                max_weight = max(edge_weights)
                edge_widths = [0.5 + (w/max_weight) * 2 for w in edge_weights]
                
                nx.draw_networkx_edges(G_sub, pos, ax=ax, edge_color=self.colors['edges'], 
                                     alpha=0.6, width=edge_widths)
            
            # Draw nodes by category - NO LABELS
            degrees = dict(G_sub.degree())
            max_degree = max(degrees.values()) if degrees else 1
            
            # Stable core nodes (largest, dark grey)
            stable_in_sub = [n for n in stable_core if n in G_sub.nodes()]
            if stable_in_sub:
                core_sizes = [300 + (degrees.get(n, 0) / max_degree) * 200 for n in stable_in_sub]
                nx.draw_networkx_nodes(G_sub, pos, nodelist=stable_in_sub, 
                                     node_color=self.colors['stable_core'],
                                     node_size=core_sizes, alpha=0.9, ax=ax,
                                     edgecolors='white', linewidths=2)
            
            # Domestic nodes (medium, light blue)
            domestic_in_sub = [n for n in domestic if n in G_sub.nodes()]
            if domestic_in_sub:
                domestic_sizes = [200 + (degrees.get(n, 0) / max_degree) * 150 for n in domestic_in_sub]
                nx.draw_networkx_nodes(G_sub, pos, nodelist=domestic_in_sub,
                                     node_color=self.colors['domestic'],
                                     node_size=domestic_sizes, alpha=0.8, ax=ax,
                                     edgecolors='white', linewidths=1.5)
            
            # International nodes (medium, reddish-brown)
            intl_in_sub = [n for n in international if n in G_sub.nodes()]
            if intl_in_sub:
                intl_sizes = [250 + (degrees.get(n, 0) / max_degree) * 150 for n in intl_in_sub]
                nx.draw_networkx_nodes(G_sub, pos, nodelist=intl_in_sub,
                                     node_color=self.colors['international'],
                                     node_size=intl_sizes, alpha=0.8, ax=ax,
                                     edgecolors='white', linewidths=1.5)
            
            # NO LABELS - just the network structure
            
            # Clean title (with proper padding)
            ax.set_title(period_name, fontsize=13, fontweight='bold', pad=10)
            ax.axis('off')
            
            # Add network stats (no entity names) - positioned to avoid overlap
            stats_text = f"Nodes: {G_sub.number_of_nodes()}\nCore: {len(stable_in_sub)}\nIntl: {len(intl_in_sub)}"
            ax.text(0.02, 0.95, stats_text, transform=ax.transAxes, fontsize=9, 
                   va='top', ha='left', 
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.9, 
                           edgecolor='gray', linewidth=1))
        
        # Add main title (with more space)
        fig.suptitle('Network Repurposing: Core Stability with International Flexibility', 
                    fontsize=18, fontweight='bold', y=0.98)
        
        # Add legend
        legend_elements = [
            plt.scatter([], [], c=self.colors['stable_core'], s=150, alpha=0.9, 
                       edgecolors='white', linewidths=2, label='Stable Core'),
            plt.scatter([], [], c=self.colors['domestic'], s=120, alpha=0.8, 
                       edgecolors='white', linewidths=1.5, label='Domestic Network'),
            plt.scatter([], [], c=self.colors['international'], s=130, alpha=0.8, 
                       edgecolors='white', linewidths=1.5, label='International Partners')
        ]
        
        fig.legend(handles=legend_elements, loc='lower center', ncol=3, 
                  fontsize=12, bbox_to_anchor=(0.5, 0.01), frameon=True, fancybox=True)
        
        # Adjust spacing to prevent overlap
        plt.tight_layout(rect=[0, 0.05, 1, 0.96])
        plt.subplots_adjust(hspace=0.25, wspace=0.25, top=0.94, bottom=0.08)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white', 
                       pad_inches=0.2)
            plt.savefig(save_path.replace('.png', '.pdf'), dpi=300, bbox_inches='tight', 
                       facecolor='white', pad_inches=0.2)
            print(f"✓ Saved network evolution (no labels): {save_path}")
        
        plt.close()
        return fig


def main():
    """Create network evolution visualization without labels"""
    
    visualizer = NetworkEvolutionNoLabels()
    
    # Load networks from period files
    periods_data = {}
    period_files = {
        'pre_crimea': 'data/periods/pre_crimea.csv',
        'post_crimea': 'data/periods/post_crimea.csv', 
        'covid': 'data/periods/covid.csv',
        'war': 'data/periods/war.csv'
    }
    
    print("Loading networks for evolution visualization...")
    for period_name, file_path in period_files.items():
        try:
            if not os.path.exists(file_path):
                print(f"⚠ Warning: {file_path} not found, skipping...")
                continue
            G = visualizer.create_network_from_csv(file_path, min_edge_weight=20)
            periods_data[period_name] = G
            print(f"✓ {period_name}: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        except Exception as e:
            print(f"✗ Error loading {period_name}: {e}")
            continue
    
    if not periods_data:
        print("❌ No period data loaded. Cannot create visualization.")
        return
    
    print("\nCreating network evolution visualization (NO LABELS)...")
    
    # Create output directory
    output_dir = "final visuals"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create the visualization
    save_path = os.path.join(output_dir, "network_evolution_no_labels.png")
    visualizer.create_network_evolution_no_labels(periods_data, save_path)
    
    print(f"\n✅ Network evolution visualization completed!")
    print(f"   → Saved to: {save_path}")
    print(f"   → NO labels, badges, or names - purely structural")
    print(f"   → Shows core stability and international flexibility across periods")


if __name__ == "__main__":
    main()
