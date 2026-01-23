import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from collections import Counter, defaultdict
import seaborn as sns
from matplotlib.patches import Circle, Rectangle, FancyBboxPatch
import matplotlib.patches as mpatches
from matplotlib.patches import ConnectionPatch
import matplotlib.gridspec as gridspec
from sklearn.cluster import KMeans
from scipy.spatial.distance import pdist, squareform

class WholeNetworkVisualizer:
    """
    Creates visualizations of the ENTIRE network to show:
    1. Network repurposing/flexibility (international partnerships change)
    2. Stable domestic core (persistent institutional actors)
    """
    
    def __init__(self):
        # Define stable domestic core entities (persistent across periods)
        self.core_entities = [
            'Владимир Путин', 'Внешэкономбанк (ВЭБ)', 'Сбербанк', 'Банк ВТБ',
            'ОАО «Газпром»', 'Роснефть', 'ОАО «РЖД»', 'Министерство финансов',
            'Совет Федерации', 'Московская биржа', 'Дмитрий Медведев',
            'Федеральная антимонопольная служба (ФАС)', 'МВД', 'Банк России'
        ]
        
        # Clean academic colors
        self.colors = {
            'stable_core': '#2c3e50',        # Dark blue-gray (stable)
            'domestic': '#34495e',           # Medium gray (domestic)
            'international': '#e74c3c',      # Red (international)
            'flexible': '#f39c12',           # Orange (flexible/new)
            'peripheral': '#95a5a6',         # Light gray (peripheral)
            'connections': '#bdc3c7'         # Very light gray (edges)
        }
    
    def create_network_from_csv(self, file_path, min_edge_weight=5):
        """Create network with lower threshold to capture more of the whole network"""
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
            
            G.nodes[node]['node_category'] = self.classify_node_category(node)
            
        return G
    
    def classify_node_category(self, entity_name):
        """Classify nodes into categories for visualization"""
        entity_lower = entity_name.lower()
        
        # Check if it's a stable core entity
        if any(core.lower() in entity_lower or entity_lower in core.lower() 
               for core in self.core_entities):
            return 'stable_core'
        
        # Russian/domestic indicators
        russian_indicators = [
            'российский', 'russia', 'moscow', 'москва', 'санкт-петербург',
            'минфин', 'министерство', 'федеральн', 'госуд', 'рос', 'мин',
            'дума', 'совет', 'банк', 'фонд'
        ]
        
        if any(indicator in entity_lower for indicator in russian_indicators):
            return 'domestic'
        
        # International indicators
        international_indicators = [
            'china', 'chinese', 'saudi', 'qatar', 'emirates', 'japan', 'japanese',
            'germany', 'german', 'france', 'french', 'uk', 'britain', 'usa', 'american',
            'investment corporation', 'sovereign fund', 'international', 'world',
            'european', 'asian', 'trump', 'biden', 'xi jinping'
        ]
        
        if any(indicator in entity_lower for indicator in international_indicators):
            return 'international'
        
        return 'domestic'
    
    def create_page1_whole_network_flexibility(self, periods_data, save_path=None):
        """
        PAGE 1: Whole Network Flexibility Visualization
        Shows the entire network with focus on how international connections change
        while domestic core remains stable
        """
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Network Repurposing: Flexible International Engagement with Stable Core', 
                    fontsize=18, fontweight='bold', y=0.95)
        
        periods = ['pre_crimea', 'post_crimea', 'covid', 'war']
        period_names = ['Pre-Crimea\n(2012-2014)', 'Post-Crimea\n(2014-2017)', 
                       'COVID-19\n(2020-2022)', 'War Period\n(2022-2024)']
        
        # Create subplot for each period
        for idx, (period, period_name) in enumerate(zip(periods, period_names)):
            row, col = idx // 2, idx % 2
            ax = axes[row, col]
            
            if period not in periods_data:
                ax.text(0.5, 0.5, f'No data for {period_name}', 
                       ha='center', va='center', transform=ax.transAxes)
                ax.set_title(period_name, fontsize=14, fontweight='bold')
                continue
            
            G = periods_data[period]
            
            # Use spring layout for consistent positioning
            pos = nx.spring_layout(G, k=0.5, iterations=50, seed=42)
            
            # Separate nodes by category
            stable_core_nodes = [n for n in G.nodes() if G.nodes[n]['node_category'] == 'stable_core']
            domestic_nodes = [n for n in G.nodes() if G.nodes[n]['node_category'] == 'domestic']
            international_nodes = [n for n in G.nodes() if G.nodes[n]['node_category'] == 'international']
            
            # Draw edges first (lighter, in background)
            nx.draw_networkx_edges(G, pos, ax=ax, edge_color=self.colors['connections'], 
                                 alpha=0.1, width=0.2)
            
            # Draw nodes by category with different sizes based on degree
            degrees = dict(G.degree())
            max_degree = max(degrees.values()) if degrees else 1
            
            # Stable core nodes (largest, most prominent)
            if stable_core_nodes:
                core_sizes = [min(300, 50 + (degrees.get(n, 0) / max_degree) * 200) 
                             for n in stable_core_nodes]
                nx.draw_networkx_nodes(G, pos, nodelist=stable_core_nodes, 
                                     node_color=self.colors['stable_core'],
                                     node_size=core_sizes, alpha=0.9, ax=ax)
            
            # Domestic nodes (medium size)
            if domestic_nodes:
                domestic_sizes = [min(150, 20 + (degrees.get(n, 0) / max_degree) * 100) 
                                for n in domestic_nodes]
                nx.draw_networkx_nodes(G, pos, nodelist=domestic_nodes,
                                     node_color=self.colors['domestic'],
                                     node_size=domestic_sizes, alpha=0.7, ax=ax)
            
            # International nodes (variable size, colored by period-specific importance)
            if international_nodes:
                intl_sizes = [min(200, 30 + (degrees.get(n, 0) / max_degree) * 150) 
                            for n in international_nodes]
                nx.draw_networkx_nodes(G, pos, nodelist=international_nodes,
                                     node_color=self.colors['international'],
                                     node_size=intl_sizes, alpha=0.8, ax=ax)
            
            # Add title and stats
            ax.set_title(f'{period_name}\n{G.number_of_nodes()} nodes, {G.number_of_edges()} edges', 
                        fontsize=12, fontweight='bold')
            ax.axis('off')
            
            # Add period-specific annotation
            period_annotations = {
                0: "Diverse international\npartnerships",
                1: "Sanctions response:\nEast pivot",
                2: "Health diplomacy\nnetworks",
                3: "Wartime alliance\nrestructuring"
            }
            
            ax.text(0.02, 0.98, period_annotations[idx], transform=ax.transAxes,
                   fontsize=10, va='top', ha='left', style='italic',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
        
        # Add legend
        legend_elements = [
            plt.scatter([], [], c=self.colors['stable_core'], s=100, alpha=0.9, label='Stable Core'),
            plt.scatter([], [], c=self.colors['domestic'], s=80, alpha=0.7, label='Domestic Network'),
            plt.scatter([], [], c=self.colors['international'], s=90, alpha=0.8, label='International Partners')
        ]
        
        fig.legend(handles=legend_elements, loc='lower center', ncol=3, 
                  fontsize=12, bbox_to_anchor=(0.5, 0.02))
        
        # Add explanatory text
        fig.text(0.5, 0.08, 
                'Node size reflects network centrality. The stable core (dark blue) persists across periods,\n'
                'while international partnerships (red) adapt to changing geopolitical contexts.',
                ha='center', va='center', fontsize=11, style='italic')
        
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.15, top=0.90)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.savefig(save_path.replace('.png', '.pdf'), dpi=300, bbox_inches='tight', facecolor='white')
            print(f"Page 1 - Whole Network Flexibility saved: {save_path}")
        
        plt.show()
        return fig
    
    def create_page2_core_periphery_structure(self, periods_data, save_path=None):
        """
        PAGE 2: Core-Periphery Structure of Entire Network
        Shows the stable domestic core and its relationship to the flexible periphery
        """
        
        fig, ax = plt.subplots(1, 1, figsize=(14, 10))
        
        # Combine all periods to show overall structure
        all_nodes = set()
        all_edges = defaultdict(int)
        node_periods = defaultdict(set)
        
        for period, G in periods_data.items():
            all_nodes.update(G.nodes())
            for node in G.nodes():
                node_periods[node].add(period)
            for edge in G.edges():
                sorted_edge = tuple(sorted(edge))
                all_edges[sorted_edge] += 1
        
        # Create combined network
        combined_G = nx.Graph()
        combined_G.add_nodes_from(all_nodes)
        
        # Add edges that appear in multiple periods (stronger connections)
        for edge, count in all_edges.items():
            if count >= 2:  # Appears in at least 2 periods
                combined_G.add_edge(edge[0], edge[1], weight=count)
        
        # Classify nodes by persistence and category
        total_periods = len(periods_data)
        persistent_nodes = {node for node, periods in node_periods.items() 
                          if len(periods) >= total_periods - 1}  # Appear in 3+ periods
        
        # Use circular layout with core in center
        pos = {}
        
        # Identify core nodes (persistent + high degree)
        degrees = dict(combined_G.degree())
        core_candidates = [node for node in persistent_nodes 
                          if degrees.get(node, 0) > np.percentile(list(degrees.values()), 75)]
        
        # Place core nodes in center circle
        if core_candidates:
            core_angles = np.linspace(0, 2*np.pi, len(core_candidates), endpoint=False)
            for i, node in enumerate(core_candidates):
                pos[node] = (0.3 * np.cos(core_angles[i]), 0.3 * np.sin(core_angles[i]))
        
        # Place other persistent nodes in middle ring
        other_persistent = [node for node in persistent_nodes if node not in core_candidates]
        if other_persistent:
            mid_angles = np.linspace(0, 2*np.pi, len(other_persistent), endpoint=False)
            for i, node in enumerate(other_persistent):
                pos[node] = (0.6 * np.cos(mid_angles[i]), 0.6 * np.sin(mid_angles[i]))
        
        # Place non-persistent nodes in outer ring
        non_persistent = [node for node in combined_G.nodes() if node not in persistent_nodes]
        if non_persistent:
            outer_angles = np.linspace(0, 2*np.pi, len(non_persistent), endpoint=False)
            for i, node in enumerate(non_persistent):
                pos[node] = (0.9 * np.cos(outer_angles[i]), 0.9 * np.sin(outer_angles[i]))
        
        # Draw the network
        # Edges first (background)
        edge_weights = [combined_G[u][v]['weight'] for u, v in combined_G.edges()]
        max_weight = max(edge_weights) if edge_weights else 1
        
        for edge in combined_G.edges():
            weight = combined_G[edge[0]][edge[1]]['weight']
            alpha = 0.1 + (weight / max_weight) * 0.4
            width = 0.2 + (weight / max_weight) * 1.0
            ax.plot([pos[edge[0]][0], pos[edge[1]][0]], 
                   [pos[edge[0]][1], pos[edge[1]][1]], 
                   color=self.colors['connections'], alpha=alpha, linewidth=width)
        
        # Draw nodes by category
        max_degree = max(degrees.values()) if degrees else 1
        
        # Core nodes (largest, most stable)
        if core_candidates:
            core_sizes = [min(400, 100 + (degrees.get(n, 0) / max_degree) * 300) 
                         for n in core_candidates]
            ax.scatter([pos[n][0] for n in core_candidates], 
                      [pos[n][1] for n in core_candidates],
                      s=core_sizes, c=self.colors['stable_core'], 
                      alpha=0.9, edgecolors='black', linewidths=2, zorder=3)
        
        # Other persistent nodes
        if other_persistent:
            persistent_sizes = [min(200, 50 + (degrees.get(n, 0) / max_degree) * 150) 
                              for n in other_persistent]
            ax.scatter([pos[n][0] for n in other_persistent], 
                      [pos[n][1] for n in other_persistent],
                      s=persistent_sizes, c=self.colors['domestic'], 
                      alpha=0.7, edgecolors='black', linewidths=1, zorder=2)
        
        # Non-persistent nodes (flexible periphery)
        if non_persistent:
            flexible_sizes = [min(100, 20 + (degrees.get(n, 0) / max_degree) * 80) 
                            for n in non_persistent]
            ax.scatter([pos[n][0] for n in non_persistent], 
                      [pos[n][1] for n in non_persistent],
                      s=flexible_sizes, c=self.colors['flexible'], 
                      alpha=0.6, edgecolors='gray', linewidths=0.5, zorder=1)
        
        # Draw concentric circles to show structure
        circles = [
            Circle((0, 0), 0.45, fill=False, linestyle='-', color=self.colors['stable_core'], 
                  linewidth=3, alpha=0.8),
            Circle((0, 0), 0.75, fill=False, linestyle='--', color=self.colors['domestic'], 
                  linewidth=2, alpha=0.6),
            Circle((0, 0), 1.0, fill=False, linestyle=':', color=self.colors['flexible'], 
                  linewidth=2, alpha=0.4)
        ]
        
        for circle in circles:
            ax.add_patch(circle)
        
        # Add labels for the rings
        ax.text(0, -0.55, 'STABLE CORE', ha='center', va='center', fontsize=14, 
               fontweight='bold', color=self.colors['stable_core'],
               bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9))
        
        ax.text(0, -0.85, 'Persistent Domestic Network', ha='center', va='center', fontsize=12, 
               style='italic', color=self.colors['domestic'],
               bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
        
        ax.text(0, -1.15, 'Flexible International Periphery', ha='center', va='center', fontsize=12, 
               style='italic', color=self.colors['flexible'],
               bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
        
        # Statistics in corner
        stats_text = f"Total Network: {combined_G.number_of_nodes()} entities\n"
        stats_text += f"Stable Core: {len(core_candidates)} entities\n"
        stats_text += f"Persistent Domestic: {len(other_persistent)} entities\n"
        stats_text += f"Flexible Periphery: {len(non_persistent)} entities\n"
        stats_text += f"Cross-period Connections: {combined_G.number_of_edges()}"
        
        ax.text(0.98, 0.98, stats_text, transform=ax.transAxes, fontsize=10, 
               ha='right', va='top', fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgray', alpha=0.9))
        
        ax.set_xlim(-1.3, 1.3)
        ax.set_ylim(-1.3, 1.3)
        ax.set_aspect('equal')
        ax.axis('off')
        
        ax.set_title('Core-Periphery Structure: Stable Domestic Core with Flexible International Engagement',
                    fontsize=16, fontweight='bold', pad=20)
        
        # Legend
        legend_elements = [
            plt.scatter([], [], c=self.colors['stable_core'], s=150, alpha=0.9, 
                       edgecolors='black', linewidths=2, label='Stable Core (High Persistence + Centrality)'),
            plt.scatter([], [], c=self.colors['domestic'], s=100, alpha=0.7, 
                       edgecolors='black', linewidths=1, label='Persistent Domestic Network'),
            plt.scatter([], [], c=self.colors['flexible'], s=80, alpha=0.6, 
                       edgecolors='gray', linewidths=0.5, label='Flexible International Periphery')
        ]
        
        ax.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, -0.15), 
                 ncol=1, fontsize=11, framealpha=0.9)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.savefig(save_path.replace('.png', '.pdf'), dpi=300, bbox_inches='tight', facecolor='white')
            print(f"Page 2 - Core-Periphery Structure saved: {save_path}")
        
        plt.show()
        return fig

def main():
    """Create both whole-network visualizations"""
    visualizer = WholeNetworkVisualizer()
    
    # Load networks with lower threshold to capture more of the whole network
    periods_data = {}
    period_files = {
        'pre_crimea': 'pre_crimea.csv',
        'post_crimea': 'post_crimea.csv', 
        'covid': 'covid.csv',
        'war': 'war.csv'
    }
    
    print("Loading networks for whole-network visualizations...")
    for period_name, file_path in period_files.items():
        try:
            G = visualizer.create_network_from_csv(file_path, min_edge_weight=5)  # Lower threshold
            periods_data[period_name] = G
            print(f"✅ {period_name}: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        except Exception as e:
            print(f"❌ Error loading {period_name}: {e}")
            continue
    
    print("\n" + "="*70)
    print("CREATING WHOLE NETWORK VISUALIZATIONS")
    print("="*70)
    
    # Page 1: Network Flexibility across periods
    print("\n📄 Creating Page 1: Whole Network Flexibility...")
    page1_fig = visualizer.create_page1_whole_network_flexibility(
        periods_data, "whole_network_flexibility.png"
    )
    
    # Page 2: Core-Periphery Structure  
    print("\n📄 Creating Page 2: Core-Periphery Structure...")
    page2_fig = visualizer.create_page2_core_periphery_structure(
        periods_data, "core_periphery_structure.png"
    )
    
    print("\n" + "="*70)
    print("WHOLE NETWORK VISUALIZATIONS COMPLETED")
    print("="*70)
    print("\n✅ Figure 1: Whole Network Flexibility")
    print("   → Shows entire network across 4 periods")
    print("   → Demonstrates network repurposing capability")
    print("   → File: whole_network_flexibility.png/.pdf")
    
    print("\n✅ Figure 2: Core-Periphery Structure")
    print("   → Shows stable domestic core vs flexible periphery")
    print("   → Concentric layout reveals structural hierarchy")
    print("   → File: core_periphery_structure.png/.pdf")
    
    print("\n🎯 Both visualizations show the ENTIRE network structure!")
    print("   → No limitation to top 20/50 actors")
    print("   → Captures full network repurposing dynamics")
    print("   → Clearly identifies stable core vs flexible periphery")

if __name__ == "__main__":
    main()




