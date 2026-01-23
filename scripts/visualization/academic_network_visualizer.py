import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from collections import Counter, defaultdict
import seaborn as sns
from matplotlib.patches import Circle, FancyBboxPatch
import matplotlib.patches as mpatches

class AcademicNetworkVisualizer:
    """
    Creates clean, interpretable academic-style network visualizations
    """
    
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
            'stable_core': '#2c3e50',        # Dark blue (stable institutions)
            'domestic': '#5b9bd5',           # Medium blue (domestic actors)
            'international': '#c55a5a',      # Muted red (international partners)
            'edges': '#d3d3d3',             # Light gray (connections)
            'text': '#2c3e50'               # Dark blue for text
        }
    
    def create_network_from_csv(self, file_path, min_edge_weight=20):
        """Create clean network focusing on significant connections"""
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
    
    def get_top_nodes_by_category(self, G, n_per_category=8):
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
    
    def create_page1_network_evolution(self, periods_data, save_path=None):
        """
        PAGE 1: Network Evolution - Clean comparison showing key actors
        """
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.patch.set_facecolor('white')
        
        periods = ['pre_crimea', 'post_crimea', 'covid', 'war']
        period_names = ['Pre-Crimea (2012-2014)', 'Post-Crimea (2014-2017)', 
                       'COVID-19 (2020-2022)', 'War Period (2022-2024)']
        
        # Track international partners across periods for comparison
        all_international = set()
        for G in periods_data.values():
            for node in G.nodes():
                if G.nodes[node]['node_category'] == 'international':
                    all_international.add(node)
        
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
            
            # Draw nodes by category
            degrees = dict(G_sub.degree())
            max_degree = max(degrees.values()) if degrees else 1
            
            # Stable core nodes (largest)
            stable_in_sub = [n for n in stable_core if n in G_sub.nodes()]
            if stable_in_sub:
                core_sizes = [300 + (degrees.get(n, 0) / max_degree) * 200 for n in stable_in_sub]
                nx.draw_networkx_nodes(G_sub, pos, nodelist=stable_in_sub, 
                                     node_color=self.colors['stable_core'],
                                     node_size=core_sizes, alpha=0.9, ax=ax,
                                     edgecolors='white', linewidths=2)
            
            # Domestic nodes (medium)
            domestic_in_sub = [n for n in domestic if n in G_sub.nodes()]
            if domestic_in_sub:
                domestic_sizes = [200 + (degrees.get(n, 0) / max_degree) * 150 for n in domestic_in_sub]
                nx.draw_networkx_nodes(G_sub, pos, nodelist=domestic_in_sub,
                                     node_color=self.colors['domestic'],
                                     node_size=domestic_sizes, alpha=0.8, ax=ax,
                                     edgecolors='white', linewidths=1.5)
            
            # International nodes (medium, different color)
            intl_in_sub = [n for n in international if n in G_sub.nodes()]
            if intl_in_sub:
                intl_sizes = [250 + (degrees.get(n, 0) / max_degree) * 150 for n in intl_in_sub]
                nx.draw_networkx_nodes(G_sub, pos, nodelist=intl_in_sub,
                                     node_color=self.colors['international'],
                                     node_size=intl_sizes, alpha=0.8, ax=ax,
                                     edgecolors='white', linewidths=1.5)
            
            # Add labels for key nodes with better visibility
            important_nodes = stable_in_sub[:4] + intl_in_sub[:3]  # Top 4 core + top 3 international
            
            for node in important_nodes:
                if node in pos:
                    # Create readable label
                    if 'путин' in node.lower():
                        label = 'Putin'
                    elif 'сбербанк' in node.lower():
                        label = 'Sberbank'
                    elif 'газпром' in node.lower():
                        label = 'Gazprom'
                    elif 'вэб' in node.lower() or 'внешэконом' in node.lower():
                        label = 'VEB'
                    elif 'втб' in node.lower():
                        label = 'VTB'
                    elif 'роснефть' in node.lower():
                        label = 'Rosneft'
                    elif 'трамп' in node.lower() or 'trump' in node.lower():
                        label = 'Trump'
                    elif 'байден' in node.lower() or 'biden' in node.lower():
                        label = 'Biden'
                    elif 'зеленский' in node.lower():
                        label = 'Zelensky'
                    elif 'медведев' in node.lower():
                        label = 'Medvedev'
                    elif len(node) > 15:
                        label = node[:12] + '...'
                    else:
                        label = node
                    
                    # Position label slightly offset from node center
                    x, y = pos[node]
                    ax.text(x, y, label, ha='center', va='center', 
                           fontsize=10, fontweight='bold', color='white',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='black', 
                                   alpha=0.7, edgecolor='none'))
            
            # Clean title
            ax.set_title(period_name, fontsize=14, fontweight='bold', pad=15)
            ax.axis('off')
            
            # Add network stats
            stats_text = f"Nodes: {G_sub.number_of_nodes()}\nCore: {len(stable_in_sub)}\nIntl: {len(intl_in_sub)}"
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=9, 
                   va='top', ha='left', 
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
        
        # Add main title
        fig.suptitle('Network Repurposing: Core Stability with International Flexibility', 
                    fontsize=18, fontweight='bold', y=0.95)
        
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
                  fontsize=12, bbox_to_anchor=(0.5, 0.02))
        
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.1, top=0.9)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white', 
                       pad_inches=0.2)
            plt.savefig(save_path.replace('.png', '.pdf'), dpi=300, bbox_inches='tight', 
                       facecolor='white', pad_inches=0.2)
            print(f"Page 1 saved: {save_path}")
        
        plt.show()
        return fig
    
    def create_page2_core_structure(self, periods_data, save_path=None):
        """
        PAGE 2: Core Structure - Clear hierarchical view
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
        
        # Draw connections
        max_connection = max(connections.values()) if connections else 1
        for (actor1, actor2), weight in connections.items():
            if actor1 in pos and actor2 in pos:
                alpha = 0.3 + (weight / max_connection) * 0.5
                width = 0.5 + (weight / max_connection) * 2
                ax.plot([pos[actor1][0], pos[actor2][0]], 
                       [pos[actor1][1], pos[actor2][1]], 
                       color=self.colors['edges'], alpha=alpha, linewidth=width)
        
        # Draw nodes
        # Core nodes (largest)
        if core_actors:
            core_sizes = [400 + item[1] * 0.1 for item in persistent_by_category['stable_core']]
            ax.scatter([pos[actor][0] for actor in core_actors], 
                      [pos[actor][1] for actor in core_actors],
                      s=core_sizes, c=self.colors['stable_core'], 
                      alpha=0.9, edgecolors='white', linewidths=2, zorder=3)
        
        # Domestic nodes
        if domestic_actors:
            domestic_sizes = [250 + item[1] * 0.05 for item in persistent_by_category['domestic']]
            ax.scatter([pos[actor][0] for actor in domestic_actors], 
                      [pos[actor][1] for actor in domestic_actors],
                      s=domestic_sizes, c=self.colors['domestic'], 
                      alpha=0.8, edgecolors='white', linewidths=1.5, zorder=2)
        
        # International nodes
        if intl_actors:
            intl_sizes = [200 + item[1] * 0.05 for item in persistent_by_category['international']]
            ax.scatter([pos[actor][0] for actor in intl_actors], 
                      [pos[actor][1] for actor in intl_actors],
                      s=intl_sizes, c=self.colors['international'], 
                      alpha=0.8, edgecolors='white', linewidths=1.5, zorder=2)
        
        # Draw hierarchy circles
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
        
        # Add clear labels
        ax.text(0, -0.4, 'STABLE CORE', ha='center', va='center', fontsize=14, 
               fontweight='bold', color=self.colors['stable_core'])
        
        ax.text(0, -0.7, 'Persistent Domestic Network', ha='center', va='center', fontsize=12, 
               color=self.colors['domestic'])
        
        ax.text(0, -1.0, 'International Partners', ha='center', va='center', fontsize=12, 
               color=self.colors['international'])
        
        # Add key actor labels with better visibility
        key_actors_to_label = core_actors[:4] + intl_actors[:2]  # Top 4 core + top 2 international
        
        for actor in key_actors_to_label:
            if actor in pos:
                # Create readable label
                if 'путин' in actor.lower():
                    label = 'Putin'
                elif 'сбербанк' in actor.lower():
                    label = 'Sberbank'
                elif 'газпром' in actor.lower():
                    label = 'Gazprom'
                elif 'вэб' in actor.lower() or 'внешэконом' in actor.lower():
                    label = 'VEB'
                elif 'втб' in actor.lower():
                    label = 'VTB'
                elif 'роснефть' in actor.lower():
                    label = 'Rosneft'
                elif 'трамп' in actor.lower() or 'trump' in actor.lower():
                    label = 'Trump'
                elif 'байден' in actor.lower() or 'biden' in actor.lower():
                    label = 'Biden'
                elif 'медведев' in actor.lower():
                    label = 'Medvedev'
                elif 'министерство финансов' in actor.lower():
                    label = 'MinFin'
                elif len(actor) > 12:
                    label = actor[:10] + '...'
                else:
                    label = actor
                
                # Position label with background for visibility
                x, y = pos[actor]
                ax.text(x, y, label, ha='center', va='center', 
                       fontsize=11, fontweight='bold', color='white',
                       bbox=dict(boxstyle='round,pad=0.4', facecolor='black', 
                               alpha=0.8, edgecolor='white', linewidth=0.5))
        
        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(-1.2, 1.2)
        ax.set_aspect('equal')
        ax.axis('off')
        
        ax.set_title('Institutional Core-Periphery Structure', fontsize=16, fontweight='bold', pad=20)
        
        # Simple legend
        legend_elements = [
            plt.scatter([], [], c=self.colors['stable_core'], s=150, alpha=0.9, 
                       edgecolors='white', linewidths=2, label='Stable Core'),
            plt.scatter([], [], c=self.colors['domestic'], s=120, alpha=0.8, 
                       edgecolors='white', linewidths=1.5, label='Persistent Domestic'),
            plt.scatter([], [], c=self.colors['international'], s=100, alpha=0.8, 
                       edgecolors='white', linewidths=1.5, label='International Partners')
        ]
        
        ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.98, 0.98), 
                 fontsize=11)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white', 
                       pad_inches=0.2)
            plt.savefig(save_path.replace('.png', '.pdf'), dpi=300, bbox_inches='tight', 
                       facecolor='white', pad_inches=0.2)
            print(f"Page 2 saved: {save_path}")
        
        plt.show()
        return fig

def main():
    """Create academic-quality network visualizations"""
    visualizer = AcademicNetworkVisualizer()
    
    # Load networks with higher threshold for cleaner visualization
    periods_data = {}
    period_files = {
        'pre_crimea': 'pre_crimea.csv',
        'post_crimea': 'post_crimea.csv', 
        'covid': 'covid.csv',
        'war': 'war.csv'
    }
    
    print("Loading networks for academic visualization...")
    for period_name, file_path in period_files.items():
        try:
            G = visualizer.create_network_from_csv(file_path, min_edge_weight=20)
            periods_data[period_name] = G
            print(f"✅ {period_name}: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        except Exception as e:
            print(f"❌ Error loading {period_name}: {e}")
            continue
    
    print("\nCreating academic network visualizations...")
    
    # Page 1: Network Evolution
    print("📄 Page 1: Network Evolution...")
    page1_fig = visualizer.create_page1_network_evolution(
        periods_data, "academic_network_evolution.png"
    )
    
    # Page 2: Core Structure  
    print("📄 Page 2: Core Structure...")
    page2_fig = visualizer.create_page2_core_structure(
        periods_data, "academic_core_structure.png"
    )
    
    print("\n✅ Academic visualizations completed!")
    print("   → Clean, interpretable network representations")
    print("   → Focus on key actors and meaningful connections")
    print("   → Academic-quality styling for publication")

if __name__ == "__main__":
    main()
