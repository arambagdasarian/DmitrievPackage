import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from collections import defaultdict
from matplotlib.patches import Circle
import os

class ConceptualCoreStructureVisualizer:
    """
    Creates a purely conceptual visualization of core-periphery structure
    without any node labels, badges, or names - only legend
    """
    
    def __init__(self):
        # Define stable domestic core entities
        self.core_entities = [
            'Владимир Путин', 'Внешэкономбанк (ВЭБ)', 'Сбербанк', 'Банк ВТБ',
            'ОАО «Газпром»', 'Роснефть', 'ОАО «РЖД»', 'Министерство финансов',
            'Совет Федерации', 'Московская биржа', 'Дмитрий Медведев',
            'Федеральная антимонопольная служба (ФАС)', 'МВД', 'Банк России'
        ]
        
        # Academic color palette matching the image description
        self.colors = {
            'stable_core': '#2c3e50',        # Dark grey (stable institutions)
            'domestic': '#5b9bd5',           # Light blue (domestic actors)
            'international': '#c55a5a',      # Reddish-brown (international partners)
            'edges': '#d3d3d3'               # Light gray (connections)
        }
    
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
            
            G.nodes[node]['node_category'] = self.classify_node_category(node)
            
        return G
    
    def classify_node_category(self, entity_name):
        """Classify nodes into meaningful categories"""
        entity_lower = entity_name.lower()
        
        # Check if it's a stable core entity
        if any(core.lower() in entity_lower or entity_lower in core.lower() 
               for core in self.core_entities):
            return 'stable_core'
        
        # Russian/domestic indicators
        russian_indicators = [
            'российский', 'russia', 'moscow', 'москва', 'санкт-петербург',
            'минфин', 'министерство', 'федеральн', 'госуд', 'рос', 'мин',
            'дума', 'совет', 'банк', 'фонд', 'роснефть', 'газпром'
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
    
    def create_conceptual_core_structure(self, periods_data, save_path=None):
        """
        Create purely conceptual visualization - NO labels, badges, or names
        Only shows the three-layer structure with legend
        """
        
        fig, ax = plt.subplots(1, 1, figsize=(12, 10))
        fig.patch.set_facecolor('white')
        
        # Combine all periods to identify persistent actors
        all_nodes = set()
        node_periods = defaultdict(set)
        node_total_degree = defaultdict(int)
        
        for period, G in periods_data.items():
            all_nodes.update(G.nodes())
            degrees = dict(G.degree())
            for node in G.nodes():
                node_periods[node].add(period)
                node_total_degree[node] += degrees[node]
        
        # Classify by persistence and importance
        total_periods = len(periods_data)
        persistent_nodes = {node for node, periods in node_periods.items() 
                          if len(periods) >= total_periods - 1}
        
        # Get top actors by category from persistent nodes
        persistent_by_category = {'stable_core': [], 'domestic': [], 'international': []}
        
        for node in persistent_nodes:
            # Use first available period to get category
            for G in periods_data.values():
                if node in G.nodes():
                    category = G.nodes[node]['node_category']
                    persistent_by_category[category].append((node, node_total_degree[node]))
                    break
        
        # Sort by total degree and take top actors
        for category in persistent_by_category:
            persistent_by_category[category] = sorted(
                persistent_by_category[category], 
                key=lambda x: x[1], reverse=True
            )[:8]  # Top 8 per category
        
        # Create positions in hierarchical layout
        pos = {}
        
        # Core in center (tight circle)
        core_actors = [item[0] for item in persistent_by_category['stable_core']]
        if core_actors:
            if len(core_actors) == 1:
                pos[core_actors[0]] = (0, 0)
            else:
                angles = np.linspace(0, 2*np.pi, len(core_actors), endpoint=False)
                for i, actor in enumerate(core_actors):
                    pos[actor] = (0.2 * np.cos(angles[i]), 0.2 * np.sin(angles[i]))
        
        # Domestic in middle ring
        domestic_actors = [item[0] for item in persistent_by_category['domestic']]
        if domestic_actors:
            angles = np.linspace(0, 2*np.pi, len(domestic_actors), endpoint=False)
            for i, actor in enumerate(domestic_actors):
                pos[actor] = (0.5 * np.cos(angles[i]), 0.5 * np.sin(angles[i]))
        
        # International in outer ring
        intl_actors = [item[0] for item in persistent_by_category['international']]
        if intl_actors:
            angles = np.linspace(0, 2*np.pi, len(intl_actors), endpoint=False)
            for i, actor in enumerate(intl_actors):
                pos[actor] = (0.8 * np.cos(angles[i]), 0.8 * np.sin(angles[i]))
        
        # Create subgraph with these key actors
        all_key_actors = core_actors + domestic_actors + intl_actors
        
        # Find connections between these actors across all periods
        connections = defaultdict(int)
        for G in periods_data.values():
            for actor1 in all_key_actors:
                for actor2 in all_key_actors:
                    if actor1 != actor2 and G.has_edge(actor1, actor2):
                        edge = tuple(sorted([actor1, actor2]))
                        connections[edge] += G[actor1][actor2]['weight']
        
        # Draw connections (edges)
        max_connection = max(connections.values()) if connections else 1
        for (actor1, actor2), weight in connections.items():
            if actor1 in pos and actor2 in pos:
                alpha = 0.3 + (weight / max_connection) * 0.5
                width = 0.5 + (weight / max_connection) * 2
                ax.plot([pos[actor1][0], pos[actor2][0]], 
                       [pos[actor1][1], pos[actor2][1]], 
                       color=self.colors['edges'], alpha=alpha, linewidth=width, zorder=1)
        
        # Draw nodes - NO LABELS, NO BADGES, NO NAMES
        # Core nodes (largest, dark grey)
        if core_actors:
            core_sizes = [400 + item[1] * 0.1 for item in persistent_by_category['stable_core']]
            ax.scatter([pos[actor][0] for actor in core_actors], 
                      [pos[actor][1] for actor in core_actors],
                      s=core_sizes, c=self.colors['stable_core'], 
                      alpha=0.9, edgecolors='white', linewidths=2, zorder=3)
        
        # Domestic nodes (medium, light blue)
        if domestic_actors:
            domestic_sizes = [250 + item[1] * 0.05 for item in persistent_by_category['domestic']]
            ax.scatter([pos[actor][0] for actor in domestic_actors], 
                      [pos[actor][1] for actor in domestic_actors],
                      s=domestic_sizes, c=self.colors['domestic'], 
                      alpha=0.8, edgecolors='white', linewidths=1.5, zorder=2)
        
        # International nodes (medium, reddish-brown)
        if intl_actors:
            intl_sizes = [200 + item[1] * 0.05 for item in persistent_by_category['international']]
            ax.scatter([pos[actor][0] for actor in intl_actors], 
                      [pos[actor][1] for actor in intl_actors],
                      s=intl_sizes, c=self.colors['international'], 
                      alpha=0.8, edgecolors='white', linewidths=1.5, zorder=2)
        
        # Draw hierarchy circles to show layers
        circles = [
            Circle((0, 0), 0.3, fill=False, linestyle='-', color=self.colors['stable_core'], 
                  linewidth=2, alpha=0.6),
            Circle((0, 0), 0.6, fill=False, linestyle='--', color=self.colors['domestic'], 
                  linewidth=1.5, alpha=0.5),
            Circle((0, 0), 0.9, fill=False, linestyle=':', color=self.colors['international'], 
                  linewidth=1.5, alpha=0.4)
        ]
        
        for circle in circles:
            ax.add_patch(circle)
        
        # Set axis limits and properties
        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(-1.2, 1.2)
        ax.set_aspect('equal')
        ax.axis('off')
        
        # Title
        ax.set_title('Institutional Core-Periphery Structure', fontsize=16, fontweight='bold', pad=20)
        
        # Legend only - NO node labels
        legend_elements = [
            plt.scatter([], [], c=self.colors['stable_core'], s=150, alpha=0.9, 
                       edgecolors='white', linewidths=2, label='Stable Core'),
            plt.scatter([], [], c=self.colors['domestic'], s=120, alpha=0.8, 
                       edgecolors='white', linewidths=1.5, label='Persistent Domestic'),
            plt.scatter([], [], c=self.colors['international'], s=100, alpha=0.8, 
                       edgecolors='white', linewidths=1.5, label='International Partners')
        ]
        
        ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.98, 0.98), 
                 fontsize=12, frameon=True, fancybox=True, shadow=False)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white', 
                       pad_inches=0.2)
            plt.savefig(save_path.replace('.png', '.pdf'), dpi=300, bbox_inches='tight', 
                       facecolor='white', pad_inches=0.2)
            print(f"✓ Saved conceptual core structure: {save_path}")
        
        plt.close()
        return fig


def main():
    """Create conceptual core-periphery visualization without labels"""
    
    visualizer = ConceptualCoreStructureVisualizer()
    
    # Load networks from period files
    periods_data = {}
    period_files = {
        'pre_crimea': 'data/periods/pre_crimea.csv',
        'post_crimea': 'data/periods/post_crimea.csv', 
        'covid': 'data/periods/covid.csv',
        'war': 'data/periods/war.csv'
    }
    
    print("Loading networks for conceptual visualization...")
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
    
    print("\nCreating conceptual core-periphery structure (no labels)...")
    
    # Create output directory
    output_dir = "final visuals"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create the visualization
    save_path = os.path.join(output_dir, "academic_core_structure.png")
    visualizer.create_conceptual_core_structure(periods_data, save_path)
    
    print(f"\n✅ Conceptual visualization completed!")
    print(f"   → Saved to: {save_path}")
    print(f"   → No labels, badges, or names - purely conceptual")
    print(f"   → Shows three layers: Stable Core, Persistent Domestic, International Partners")


if __name__ == "__main__":
    main()
