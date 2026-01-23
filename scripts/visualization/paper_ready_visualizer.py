import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from collections import Counter, defaultdict
import seaborn as sns
from matplotlib.patches import Circle
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec

class PaperReadyNetworkVisualizer:
    """
    Creates clean, minimal visualizations for academic paper
    """
    
    def __init__(self):
        # Define stable domestic core entities
        self.core_entities = [
            'Владимир Путин', 'Внешэкономбанк (ВЭБ)', 'Сбербанк', 'Банк ВТБ',
            'ОАО «Газпром»', 'Роснефть', 'ОАО «РЖД»', 'Министерство финансов',
            'Совет Федерации', 'Московская биржа', 'Дмитрий Медведев',
            'Федеральная антимонопольная служба (ФАС)', 'МВД', 'Банк России'
        ]
        
        # Clean academic colors
        self.colors = {
            'stable_core': '#1f4e79',        # Deep blue
            'domestic': '#5b9bd5',           # Medium blue
            'international': '#c55a5a',      # Muted red
            'connections': '#e6e6e6'         # Very light gray
        }
    
    def create_network_from_csv(self, file_path, min_edge_weight=10):
        """Create network with clean threshold"""
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
        """Classify nodes into categories"""
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
            'european', 'asian', 'trump', 'biden', 'xi jinping', 'трамп', 'байден'
        ]
        
        if any(indicator in entity_lower for indicator in international_indicators):
            return 'international'
        
        return 'domestic'
    
    def create_page1_network_flexibility(self, periods_data, save_path=None):
        """
        PAGE 1: Minimal Network Flexibility - 4 periods side by side
        """
        
        fig, axes = plt.subplots(1, 4, figsize=(20, 5))
        fig.patch.set_facecolor('white')
        
        periods = ['pre_crimea', 'post_crimea', 'covid', 'war']
        period_names = ['Pre-Crimea', 'Post-Crimea', 'COVID-19', 'War Period']
        
        for idx, (period, period_name) in enumerate(zip(periods, period_names)):
            ax = axes[idx]
            
            if period not in periods_data:
                ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
                ax.set_title(period_name, fontsize=14, fontweight='bold')
                ax.axis('off')
                continue
            
            G = periods_data[period]
            
            # Use spring layout
            pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
            
            # Separate nodes by category
            stable_core_nodes = [n for n in G.nodes() if G.nodes[n]['node_category'] == 'stable_core']
            domestic_nodes = [n for n in G.nodes() if G.nodes[n]['node_category'] == 'domestic']
            international_nodes = [n for n in G.nodes() if G.nodes[n]['node_category'] == 'international']
            
            # Draw edges very lightly
            if G.number_of_edges() > 0:
                nx.draw_networkx_edges(G, pos, ax=ax, edge_color=self.colors['connections'], 
                                     alpha=0.1, width=0.2)
            
            # Calculate node sizes
            degrees = dict(G.degree())
            max_degree = max(degrees.values()) if degrees else 1
            
            # Draw nodes
            if stable_core_nodes:
                core_sizes = [max(60, min(150, 30 + (degrees.get(n, 0) / max_degree) * 80)) 
                             for n in stable_core_nodes]
                nx.draw_networkx_nodes(G, pos, nodelist=stable_core_nodes, 
                                     node_color=self.colors['stable_core'],
                                     node_size=core_sizes, alpha=0.9, ax=ax)
            
            if domestic_nodes:
                domestic_sizes = [max(30, min(100, 15 + (degrees.get(n, 0) / max_degree) * 60)) 
                                for n in domestic_nodes]
                nx.draw_networkx_nodes(G, pos, nodelist=domestic_nodes,
                                     node_color=self.colors['domestic'],
                                     node_size=domestic_sizes, alpha=0.8, ax=ax)
            
            if international_nodes:
                intl_sizes = [max(40, min(120, 20 + (degrees.get(n, 0) / max_degree) * 70)) 
                            for n in international_nodes]
                nx.draw_networkx_nodes(G, pos, nodelist=international_nodes,
                                     node_color=self.colors['international'],
                                     node_size=intl_sizes, alpha=0.8, ax=ax)
            
            # Clean title
            ax.set_title(period_name, fontsize=14, fontweight='bold', pad=10)
            ax.axis('off')
        
        # Simple legend
        legend_elements = [
            plt.scatter([], [], c=self.colors['stable_core'], s=80, alpha=0.9, label='Stable Core'),
            plt.scatter([], [], c=self.colors['domestic'], s=60, alpha=0.8, label='Domestic'),
            plt.scatter([], [], c=self.colors['international'], s=70, alpha=0.8, label='International')
        ]
        
        fig.legend(handles=legend_elements, loc='lower center', ncol=3, 
                  fontsize=12, bbox_to_anchor=(0.5, -0.05))
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white', 
                       pad_inches=0.1)
            plt.savefig(save_path.replace('.png', '.pdf'), dpi=300, bbox_inches='tight', 
                       facecolor='white', pad_inches=0.1)
            print(f"Page 1 saved: {save_path}")
        
        plt.show()
        return fig
    
    def create_page2_core_periphery_structure(self, periods_data, save_path=None):
        """
        PAGE 2: Minimal Core-Periphery Structure
        """
        
        fig, ax = plt.subplots(1, 1, figsize=(10, 10))
        fig.patch.set_facecolor('white')
        
        # Combine all periods
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
        
        for edge, count in all_edges.items():
            if count >= 2:
                combined_G.add_edge(edge[0], edge[1], weight=count)
        
        # Classify nodes
        total_periods = len(periods_data)
        persistent_nodes = {node for node, periods in node_periods.items() 
                          if len(periods) >= total_periods - 1}
        
        degrees = dict(combined_G.degree())
        
        if degrees:
            degree_threshold = np.percentile(list(degrees.values()), 75)
            core_candidates = [node for node in persistent_nodes 
                              if degrees.get(node, 0) >= degree_threshold]
        else:
            core_candidates = []
        
        # Create circular layout
        pos = {}
        
        # Core in center
        if core_candidates:
            if len(core_candidates) == 1:
                pos[core_candidates[0]] = (0, 0)
            else:
                core_angles = np.linspace(0, 2*np.pi, len(core_candidates), endpoint=False)
                for i, node in enumerate(core_candidates):
                    pos[node] = (0.2 * np.cos(core_angles[i]), 0.2 * np.sin(core_angles[i]))
        
        # Other persistent in middle
        other_persistent = [node for node in persistent_nodes if node not in core_candidates]
        if other_persistent:
            mid_angles = np.linspace(0, 2*np.pi, len(other_persistent), endpoint=False)
            for i, node in enumerate(other_persistent):
                pos[node] = (0.5 * np.cos(mid_angles[i]), 0.5 * np.sin(mid_angles[i]))
        
        # Non-persistent in outer
        non_persistent = [node for node in combined_G.nodes() if node not in persistent_nodes]
        if non_persistent:
            outer_angles = np.linspace(0, 2*np.pi, len(non_persistent), endpoint=False)
            for i, node in enumerate(non_persistent):
                pos[node] = (0.8 * np.cos(outer_angles[i]), 0.8 * np.sin(outer_angles[i]))
        
        # Draw edges lightly
        if combined_G.number_of_edges() > 0:
            edge_weights = [combined_G[u][v]['weight'] for u, v in combined_G.edges()]
            max_weight = max(edge_weights)
            
            for edge in combined_G.edges():
                weight = combined_G[edge[0]][edge[1]]['weight']
                alpha = 0.1 + (weight / max_weight) * 0.3
                width = 0.3 + (weight / max_weight) * 1.0
                ax.plot([pos[edge[0]][0], pos[edge[1]][0]], 
                       [pos[edge[0]][1], pos[edge[1]][1]], 
                       color=self.colors['connections'], alpha=alpha, linewidth=width)
        
        # Draw nodes
        max_degree = max(degrees.values()) if degrees else 1
        
        # Core nodes
        if core_candidates:
            core_sizes = [max(150, min(300, 100 + (degrees.get(n, 0) / max_degree) * 150)) 
                         for n in core_candidates]
            ax.scatter([pos[n][0] for n in core_candidates], 
                      [pos[n][1] for n in core_candidates],
                      s=core_sizes, c=self.colors['stable_core'], 
                      alpha=0.9, edgecolors='white', linewidths=1.5, zorder=3)
        
        # Other persistent
        if other_persistent:
            persistent_sizes = [max(80, min(200, 50 + (degrees.get(n, 0) / max_degree) * 100)) 
                              for n in other_persistent]
            ax.scatter([pos[n][0] for n in other_persistent], 
                      [pos[n][1] for n in other_persistent],
                      s=persistent_sizes, c=self.colors['domestic'], 
                      alpha=0.8, edgecolors='white', linewidths=1, zorder=2)
        
        # Non-persistent
        if non_persistent:
            flexible_sizes = [max(40, min(120, 25 + (degrees.get(n, 0) / max_degree) * 60)) 
                            for n in non_persistent]
            ax.scatter([pos[n][0] for n in non_persistent], 
                      [pos[n][1] for n in non_persistent],
                      s=flexible_sizes, c=self.colors['international'], 
                      alpha=0.7, edgecolors='white', linewidths=0.5, zorder=1)
        
        # Draw concentric circles
        circles = [
            Circle((0, 0), 0.3, fill=False, linestyle='-', color=self.colors['stable_core'], 
                  linewidth=2, alpha=0.7),
            Circle((0, 0), 0.6, fill=False, linestyle='--', color=self.colors['domestic'], 
                  linewidth=1.5, alpha=0.5),
            Circle((0, 0), 0.9, fill=False, linestyle=':', color=self.colors['international'], 
                  linewidth=1.5, alpha=0.4)
        ]
        
        for circle in circles:
            ax.add_patch(circle)
        
        # Minimal labels
        ax.text(0, -0.4, 'STABLE CORE', ha='center', va='center', fontsize=12, 
               fontweight='bold', color=self.colors['stable_core'])
        
        ax.text(0, -0.7, 'Persistent Domestic', ha='center', va='center', fontsize=10, 
               color=self.colors['domestic'])
        
        ax.text(0, -1.0, 'Flexible International', ha='center', va='center', fontsize=10, 
               color=self.colors['international'])
        
        ax.set_xlim(-1.1, 1.1)
        ax.set_ylim(-1.1, 1.1)
        ax.set_aspect('equal')
        ax.axis('off')
        
        # Simple legend
        legend_elements = [
            plt.scatter([], [], c=self.colors['stable_core'], s=120, alpha=0.9, 
                       edgecolors='white', linewidths=1.5, label='Stable Core'),
            plt.scatter([], [], c=self.colors['domestic'], s=100, alpha=0.8, 
                       edgecolors='white', linewidths=1, label='Persistent Domestic'),
            plt.scatter([], [], c=self.colors['international'], s=80, alpha=0.7, 
                       edgecolors='white', linewidths=0.5, label='Flexible International')
        ]
        
        ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.98, 0.98), 
                 fontsize=10)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white', 
                       pad_inches=0.1)
            plt.savefig(save_path.replace('.png', '.pdf'), dpi=300, bbox_inches='tight', 
                       facecolor='white', pad_inches=0.1)
            print(f"Page 2 saved: {save_path}")
        
        plt.show()
        return fig

def main():
    """Create minimal, paper-ready visualizations"""
    visualizer = PaperReadyNetworkVisualizer()
    
    # Load networks
    periods_data = {}
    period_files = {
        'pre_crimea': 'pre_crimea.csv',
        'post_crimea': 'post_crimea.csv', 
        'covid': 'covid.csv',
        'war': 'war.csv'
    }
    
    print("Loading networks...")
    for period_name, file_path in period_files.items():
        try:
            G = visualizer.create_network_from_csv(file_path, min_edge_weight=10)
            periods_data[period_name] = G
            print(f"✅ {period_name}: {G.number_of_nodes()} nodes")
        except Exception as e:
            print(f"❌ Error loading {period_name}: {e}")
            continue
    
    print("\nCreating paper-ready visualizations...")
    
    # Page 1: Network Flexibility
    print("📄 Page 1: Network Flexibility...")
    page1_fig = visualizer.create_page1_network_flexibility(
        periods_data, "paper_network_flexibility.png"
    )
    
    # Page 2: Core-Periphery Structure  
    print("📄 Page 2: Core-Periphery Structure...")
    page2_fig = visualizer.create_page2_core_periphery_structure(
        periods_data, "paper_core_periphery.png"
    )
    
    print("\n✅ Paper-ready visualizations completed!")

if __name__ == "__main__":
    main()




