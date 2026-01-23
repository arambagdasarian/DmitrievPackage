import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from networkx.algorithms import community
from collections import Counter, defaultdict
import seaborn as sns
from matplotlib.patches import Circle, Rectangle
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import matplotlib.gridspec as gridspec

class CreativeNetworkVisualizer:
    """
    Creative visualization approaches for large networks that remain readable
    """
    
    def __init__(self):
        self.core_entities = [
            'Кирилл Дмитриев', 'Российский фонд прямых инвестиций (РФПИ)', 'РФПИ',
            'Владимир Путин', 'Сбербанк', 'Внешэкономбанк (ВЭБ)', 'ВЭБ',
            'Банк ВТБ', 'ВТБ', 'Газпромбанк', 'ОАО «Газпром»', 'Роснефт',
            'Министерство финансов', 'Центральный банк', 'Банк России'
        ]
        
        self.colors = {
            'core': '#2c3e50',
            'domestic': '#3498db', 
            'international': '#e74c3c',
            'background': '#ecf0f1'
        }
    
    def create_network_from_csv(self, file_path, min_edge_weight=5):
        """Create network with low threshold"""
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
        
        if any(core.lower() in entity_lower for core in self.core_entities):
            return 'core'
        
        russian_indicators = [
            'российский', 'russia', 'moscow', 'москва', 'санкт-петербург',
            'минфин', 'министерство', 'федеральн', 'госуд', 'рос', 'мин'
        ]
        
        if any(indicator in entity_lower for indicator in russian_indicators):
            return 'domestic'
        
        international_indicators = [
            'china', 'chinese', 'saudi', 'qatar', 'emirates', 'japan', 'japanese',
            'germany', 'german', 'france', 'french', 'uk', 'britain', 'usa', 'american',
            'investment corporation', 'sovereign fund', 'international', 'bank'
        ]
        
        if any(indicator in entity_lower for indicator in international_indicators):
            return 'international'
        
        return 'domestic'
    
    def create_hierarchical_sunburst_style(self, periods_data, save_path=None):
        """Create a sunburst/hierarchical visualization showing network layers"""
        
        # Combine all periods
        combined_G = nx.Graph()
        entity_periods = defaultdict(set)
        
        for period, G in periods_data.items():
            for node in G.nodes():
                entity_periods[node].add(period)
                if not combined_G.has_node(node):
                    combined_G.add_node(node, **G.nodes[node])
            
            for edge in G.edges(data=True):
                if combined_G.has_edge(edge[0], edge[1]):
                    combined_G[edge[0]][edge[1]]['weight'] += edge[2]['weight']
                else:
                    combined_G.add_edge(edge[0], edge[1], **edge[2])
        
        # Calculate persistence
        persistence_scores = {}
        for entity, periods in entity_periods.items():
            persistence_scores[entity] = len(periods) / len(periods_data)
        
        # Create figure
        fig = plt.figure(figsize=(20, 12))
        gs = gridspec.GridSpec(2, 3, height_ratios=[3, 1], width_ratios=[2, 2, 1])
        
        # Main sunburst-style visualization
        ax_main = fig.add_subplot(gs[0, :2])
        
        # Create concentric circles representing different persistence levels
        persistence_levels = [1.0, 0.75, 0.5, 0.25, 0.0]  # All periods, 3/4, half, quarter, single
        radii = [0.2, 0.4, 0.6, 0.8, 1.0]
        
        # Draw background rings
        for i, (level, radius) in enumerate(zip(persistence_levels, radii)):
            circle = Circle((0, 0), radius, fill=False, linestyle='--', 
                           color='gray', alpha=0.3, linewidth=1)
            ax_main.add_patch(circle)
        
        # Categorize entities by persistence and category
        entity_groups = {
            'core_persistent': [],
            'core_flexible': [],
            'domestic_persistent': [],
            'domestic_flexible': [],
            'international_persistent': [],
            'international_flexible': []
        }
        
        for entity in combined_G.nodes():
            persistence = persistence_scores.get(entity, 0)
            category = combined_G.nodes[entity]['node_category']
            
            if persistence >= 0.75:  # Appears in 3+ periods
                entity_groups[f'{category}_persistent'].append(entity)
            else:
                entity_groups[f'{category}_flexible'].append(entity)
        
        # Position entities in rings based on persistence and category
        angle_offsets = {'core': 0, 'domestic': 2*np.pi/3, 'international': 4*np.pi/3}
        
        for group_name, entities in entity_groups.items():
            if not entities:
                continue
                
            category = group_name.split('_')[0]
            is_persistent = 'persistent' in group_name
            
            # Determine radius based on persistence
            if is_persistent:
                radius = 0.3 if category == 'core' else 0.5 if category == 'domestic' else 0.7
            else:
                radius = 0.5 if category == 'core' else 0.7 if category == 'domestic' else 0.9
            
            # Arrange entities in arc
            base_angle = angle_offsets[category]
            angle_span = 2*np.pi/3 * 0.8  # 80% of the sector
            
            if len(entities) == 1:
                angles = [base_angle]
            else:
                angles = [base_angle - angle_span/2 + i * angle_span/(len(entities)-1) 
                         for i in range(len(entities))]
            
            # Plot entities
            for entity, angle in zip(entities, angles):
                x = radius * np.cos(angle)
                y = radius * np.sin(angle)
                
                # Size based on centrality
                centrality = nx.degree_centrality(combined_G).get(entity, 0)
                size = max(20, min(200, centrality * 1000 + 50))
                
                # Color and alpha
                color = self.colors[category]
                alpha = 0.9 if is_persistent else 0.6
                
                ax_main.scatter(x, y, s=size, c=color, alpha=alpha, 
                              edgecolors='black', linewidth=0.5, zorder=3)
                
                # Label only most important entities
                if (category == 'core' or 
                    (centrality > 0.05 and is_persistent) or
                    entity in ['Кирилл Дмитриев', 'РФПИ', 'Владимир Путин']):
                    
                    label = entity if len(entity) <= 15 else entity[:12] + '...'
                    ax_main.annotate(label, (x, y), xytext=(5, 5), 
                                   textcoords='offset points', fontsize=8,
                                   bbox=dict(boxstyle='round,pad=0.2', 
                                           facecolor='white', alpha=0.8),
                                   zorder=4)
        
        # Style main plot
        ax_main.set_xlim(-1.2, 1.2)
        ax_main.set_ylim(-1.2, 1.2)
        ax_main.set_aspect('equal')
        ax_main.axis('off')
        ax_main.set_title('Network Structure: Core Persistence and Peripheral Flexibility\n'
                         f'Complete Network ({combined_G.number_of_nodes()} entities)',
                         fontsize=16, fontweight='bold', pad=20)
        
        # Add ring labels
        ring_labels = ['Stable Core\n(All Periods)', 'Persistent\n(3+ Periods)', 
                      'Moderate\n(2+ Periods)', 'Flexible\n(1-2 Periods)', 'Periphery']
        for i, (radius, label) in enumerate(zip([0.1, 0.3, 0.5, 0.7, 0.9], ring_labels)):
            ax_main.text(radius, 0, label, ha='center', va='center', 
                        fontsize=9, fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.9))
        
        # Statistics panel
        ax_stats = fig.add_subplot(gs[0, 2])
        
        stats_text = []
        stats_text.append(f"NETWORK SCALE")
        stats_text.append(f"Total Entities: {combined_G.number_of_nodes():,}")
        stats_text.append(f"Total Connections: {combined_G.number_of_edges():,}")
        stats_text.append("")
        
        stats_text.append(f"PERSISTENCE ANALYSIS")
        all_periods = sum(1 for p in persistence_scores.values() if p == 1.0)
        most_periods = sum(1 for p in persistence_scores.values() if p >= 0.75)
        stats_text.append(f"All Periods: {all_periods}")
        stats_text.append(f"Most Periods (3+): {most_periods}")
        stats_text.append("")
        
        stats_text.append(f"CATEGORY BREAKDOWN")
        for category in ['core', 'domestic', 'international']:
            count = sum(1 for n in combined_G.nodes() 
                       if combined_G.nodes[n]['node_category'] == category)
            stats_text.append(f"{category.title()}: {count}")
        
        ax_stats.text(0.05, 0.95, '\n'.join(stats_text), transform=ax_stats.transAxes,
                     fontsize=11, verticalalignment='top', fontfamily='monospace',
                     bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgray', alpha=0.8))
        ax_stats.axis('off')
        
        # Legend
        ax_legend = fig.add_subplot(gs[1, :])
        legend_elements = [
            mpatches.Patch(color=self.colors['core'], alpha=0.9, label='Stable Core (high persistence)'),
            mpatches.Patch(color=self.colors['domestic'], alpha=0.9, label='Domestic Network (persistent)'),
            mpatches.Patch(color=self.colors['international'], alpha=0.9, label='International Partners (flexible)'),
            mpatches.Patch(color='gray', alpha=0.6, label='Lower persistence entities')
        ]
        
        ax_legend.legend(handles=legend_elements, loc='center', ncol=2, fontsize=12)
        ax_legend.axis('off')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.savefig(save_path.replace('.png', '.pdf'), dpi=300, bbox_inches='tight', facecolor='white')
            print(f"Creative sunburst visualization saved: {save_path}")
        
        plt.show()
        return fig
    
    def create_matrix_heatmap_style(self, periods_data, save_path=None):
        """Create a matrix/heatmap style showing network density and connections"""
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. Entity-Period Matrix
        all_entities = set()
        for G in periods_data.values():
            all_entities.update(G.nodes())
        
        # Focus on top entities by total connections
        entity_degrees = defaultdict(int)
        for G in periods_data.values():
            for node in G.nodes():
                entity_degrees[node] += G.degree(node)
        
        top_entities = sorted(entity_degrees.items(), key=lambda x: x[1], reverse=True)[:50]
        top_entity_names = [e[0] for e in top_entities]
        
        # Create presence matrix
        presence_matrix = []
        for entity in top_entity_names:
            row = []
            for period in ['pre_crimea', 'post_crimea', 'covid', 'war']:
                if entity in periods_data[period].nodes():
                    degree = periods_data[period].degree(entity)
                    row.append(degree)
                else:
                    row.append(0)
            presence_matrix.append(row)
        
        # Plot heatmap
        sns.heatmap(presence_matrix, 
                    xticklabels=['Pre-Crimea', 'Post-Crimea', 'COVID', 'War'],
                    yticklabels=[e[:20] + '...' if len(e) > 20 else e for e in top_entity_names],
                    cmap='YlOrRd', ax=ax1, cbar_kws={'label': 'Degree Centrality'})
        ax1.set_title('Top 50 Entities: Degree Centrality Across Periods', fontweight='bold')
        ax1.set_xlabel('Time Period')
        ax1.set_ylabel('Entity')
        
        # 2. Network density evolution
        periods = list(periods_data.keys())
        densities = [nx.density(G) for G in periods_data.values()]
        node_counts = [G.number_of_nodes() for G in periods_data.values()]
        edge_counts = [G.number_of_edges() for G in periods_data.values()]
        
        ax2_twin = ax2.twinx()
        
        bars = ax2.bar(periods, node_counts, alpha=0.7, color='lightblue', label='Nodes')
        line = ax2_twin.plot(periods, densities, 'ro-', color='red', linewidth=2, label='Density')
        
        ax2.set_ylabel('Number of Nodes', color='blue')
        ax2_twin.set_ylabel('Network Density', color='red')
        ax2.set_title('Network Scale and Density Evolution', fontweight='bold')
        ax2.tick_params(axis='x', rotation=45)
        
        # 3. Category distribution over time
        category_data = {period: {'core': 0, 'domestic': 0, 'international': 0} 
                        for period in periods}
        
        for period, G in periods_data.items():
            for node in G.nodes():
                category = G.nodes[node]['node_category']
                category_data[period][category] += 1
        
        categories = ['core', 'domestic', 'international']
        colors = [self.colors[cat] for cat in categories]
        
        bottom = np.zeros(len(periods))
        for i, category in enumerate(categories):
            values = [category_data[period][category] for period in periods]
            ax3.bar(periods, values, bottom=bottom, label=category.title(), 
                   color=colors[i], alpha=0.8)
            bottom += values
        
        ax3.set_title('Entity Categories Over Time', fontweight='bold')
        ax3.set_ylabel('Number of Entities')
        ax3.legend()
        ax3.tick_params(axis='x', rotation=45)
        
        # 4. Core entities persistence
        core_entities = set()
        for G in periods_data.values():
            core_entities.update([n for n in G.nodes() 
                                if G.nodes[n]['node_category'] == 'core'])
        
        core_persistence = {}
        for entity in core_entities:
            appearances = sum(1 for G in periods_data.values() if entity in G.nodes())
            core_persistence[entity] = appearances
        
        sorted_core = sorted(core_persistence.items(), key=lambda x: x[1], reverse=True)[:15]
        
        entities, counts = zip(*sorted_core)
        bars = ax4.barh(range(len(entities)), counts, color=self.colors['core'], alpha=0.8)
        ax4.set_yticks(range(len(entities)))
        ax4.set_yticklabels([e[:25] + '...' if len(e) > 25 else e for e in entities])
        ax4.set_xlabel('Periods Appeared')
        ax4.set_title('Core Entities: Cross-Period Persistence', fontweight='bold')
        ax4.set_xlim(0, 4)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.savefig(save_path.replace('.png', '.pdf'), dpi=300, bbox_inches='tight', facecolor='white')
            print(f"Matrix heatmap visualization saved: {save_path}")
        
        plt.show()
        return fig

def main():
    """Main execution function"""
    visualizer = CreativeNetworkVisualizer()
    
    # Load networks
    periods_data = {}
    period_files = {
        'pre_crimea': 'pre_crimea.csv',
        'post_crimea': 'post_crimea.csv', 
        'covid': 'covid.csv',
        'war': 'war.csv'
    }
    
    print("Loading networks for creative visualization...")
    for period_name, file_path in period_files.items():
        try:
            G = visualizer.create_network_from_csv(file_path, min_edge_weight=5)
            periods_data[period_name] = G
            print(f"✅ {period_name}: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        except Exception as e:
            print(f"❌ Error loading {period_name}: {e}")
            continue
    
    # Create creative visualizations
    print("\n1. Creating sunburst-style visualization...")
    sunburst_fig = visualizer.create_hierarchical_sunburst_style(
        periods_data, "creative_sunburst_network.png"
    )
    
    print("\n2. Creating matrix heatmap visualization...")
    matrix_fig = visualizer.create_matrix_heatmap_style(
        periods_data, "network_matrix_heatmap.png"
    )
    
    print("\n🎉 Creative visualizations completed!")
    print("Files created:")
    print("• creative_sunburst_network.png - Hierarchical rings showing persistence")
    print("• network_matrix_heatmap.png - Matrix view of entity activity patterns")
    print("\nBoth visualizations show the complete network in readable, creative ways!")

if __name__ == "__main__":
    main()
