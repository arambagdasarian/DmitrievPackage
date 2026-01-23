import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from collections import Counter, defaultdict
import seaborn as sns
from matplotlib.patches import Circle, Rectangle, Wedge
import matplotlib.patches as mpatches
from matplotlib.sankey import Sankey

class AggregateNetworkVisualizer:
    """
    Create aggregate visualizations that show network patterns without individual nodes
    """
    
    def __init__(self):
        self.core_entities = [
            'Кирилл Дмитриев', 'Российский фонд прямых инвестиций (РФПИ)', 'РФПИ',
            'Владимир Путин', 'Сбербанк', 'Внешэкономбанк (ВЭБ)', 'ВЭБ',
            'Банк ВТБ', 'ВТБ', 'Газпромбанк', 'ОАО «Газпром»', 'Роснефть',
            'Министерство финансов', 'Центральный банк', 'Банк России'
        ]
        
        self.colors = {
            'core': '#c0392b',           # Dark red
            'domestic': '#2980b9',       # Blue
            'international': '#27ae60',  # Green
            'mixed': '#8e44ad'          # Purple
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
            'investment corporation', 'sovereign fund', 'international'
        ]
        
        if any(indicator in entity_lower for indicator in international_indicators):
            return 'international'
        
        return 'domestic'
    
    def create_flow_diagram(self, periods_data, save_path=None):
        """Create a flow diagram showing network evolution and core stability"""
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
        
        # Left panel: Core-Periphery Flow Structure
        ax1.set_xlim(0, 10)
        ax1.set_ylim(0, 10)
        
        # Calculate aggregate statistics
        period_stats = {}
        for period, G in periods_data.items():
            stats = {'core': 0, 'domestic': 0, 'international': 0, 'total_edges': G.number_of_edges()}
            for node in G.nodes():
                category = G.nodes[node]['node_category']
                stats[category] += 1
            period_stats[period] = stats
        
        # Draw core as central stable element
        core_circle = Circle((5, 5), 1.5, facecolor=self.colors['core'], 
                           alpha=0.8, edgecolor='black', linewidth=2)
        ax1.add_patch(core_circle)
        ax1.text(5, 5, 'STABLE\nCORE\n(RDIF/Dmitriev\nNetwork)', 
                ha='center', va='center', fontsize=12, fontweight='bold', color='white')
        
        # Draw domestic ring
        domestic_ring = Circle((5, 5), 2.8, fill=False, edgecolor=self.colors['domestic'], 
                             linewidth=8, alpha=0.7)
        ax1.add_patch(domestic_ring)
        ax1.text(5, 2.2, 'DOMESTIC NETWORK\n(Russian Institutions)', 
                ha='center', va='center', fontsize=11, fontweight='bold', 
                color=self.colors['domestic'])
        
        # Draw flexible international elements as separate bubbles
        international_positions = [(2, 8), (8, 8), (1.5, 2), (8.5, 2)]
        international_labels = ['China/Asia', 'Middle East', 'Europe', 'Other Partners']
        
        for pos, label in zip(international_positions, international_labels):
            bubble = Circle(pos, 0.8, facecolor=self.colors['international'], 
                          alpha=0.6, edgecolor='black', linewidth=1)
            ax1.add_patch(bubble)
            ax1.text(pos[0], pos[1], label, ha='center', va='center', 
                    fontsize=9, fontweight='bold', color='white')
            
            # Draw connection lines to core (dashed to show flexibility)
            ax1.plot([pos[0], 5], [pos[1], 5], '--', color='gray', alpha=0.5, linewidth=2)
        
        # Add arrows showing adaptation
        from matplotlib.patches import FancyArrowPatch
        from matplotlib.patches import ArrowStyle
        
        # Curved arrows showing flexibility
        arrow1 = FancyArrowPatch((2, 7.2), (2.5, 6.5), 
                               arrowstyle='->', mutation_scale=20, 
                               color=self.colors['international'], alpha=0.7,
                               connectionstyle="arc3,rad=0.3")
        ax1.add_patch(arrow1)
        
        ax1.text(1, 6, 'Flexible\nAdaptation', fontsize=10, style='italic', 
                color=self.colors['international'])
        
        ax1.set_title('Network Architecture: Stable Core with Flexible Periphery', 
                     fontsize=16, fontweight='bold', pad=20)
        ax1.axis('off')
        
        # Right panel: Quantitative flow across periods
        periods = list(periods_data.keys())
        period_labels = ['Pre-Crimea\n(2012-2014)', 'Post-Crimea\n(2014-2017)', 
                        'COVID\n(2020-2022)', 'War\n(2022-2024)']
        
        # Create stacked area chart showing entity flows
        core_counts = [period_stats[p]['core'] for p in periods]
        domestic_counts = [period_stats[p]['domestic'] for p in periods]
        international_counts = [period_stats[p]['international'] for p in periods]
        
        x = np.arange(len(periods))
        
        # Stacked areas
        ax2.fill_between(x, 0, core_counts, alpha=0.8, color=self.colors['core'], 
                        label=f'Stable Core (avg: {np.mean(core_counts):.0f})')
        ax2.fill_between(x, core_counts, 
                        [c+d for c,d in zip(core_counts, domestic_counts)], 
                        alpha=0.7, color=self.colors['domestic'], 
                        label=f'Domestic Network (avg: {np.mean(domestic_counts):.0f})')
        ax2.fill_between(x, [c+d for c,d in zip(core_counts, domestic_counts)],
                        [c+d+i for c,d,i in zip(core_counts, domestic_counts, international_counts)],
                        alpha=0.6, color=self.colors['international'], 
                        label=f'International Partners (avg: {np.mean(international_counts):.0f})')
        
        # Add trend lines
        ax2.plot(x, core_counts, 'o-', color='darkred', linewidth=3, markersize=8, alpha=0.8)
        ax2.plot(x, international_counts, 's-', color='darkgreen', linewidth=2, markersize=6, alpha=0.8)
        
        ax2.set_xticks(x)
        ax2.set_xticklabels(period_labels, fontsize=11)
        ax2.set_ylabel('Number of Entities', fontsize=12, fontweight='bold')
        ax2.set_title('Network Composition Evolution:\nCore Stability vs. Peripheral Flexibility', 
                     fontsize=14, fontweight='bold')
        ax2.legend(loc='upper left', fontsize=11)
        ax2.grid(True, alpha=0.3)
        
        # Add annotations
        ax2.annotate('Core remains\nstable', xy=(1, core_counts[1]), xytext=(1.5, core_counts[1]+50),
                    arrowprops=dict(arrowstyle='->', color='darkred', alpha=0.7),
                    fontsize=10, color='darkred', fontweight='bold')
        
        ax2.annotate('International\npartners adapt', 
                    xy=(3, international_counts[3]), xytext=(2.5, international_counts[3]+20),
                    arrowprops=dict(arrowstyle='->', color='darkgreen', alpha=0.7),
                    fontsize=10, color='darkgreen', fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.savefig(save_path.replace('.png', '.pdf'), dpi=300, bbox_inches='tight', facecolor='white')
            print(f"Flow diagram saved: {save_path}")
        
        plt.show()
        return fig
    
    def create_density_heatmap(self, periods_data, save_path=None):
        """Create a clean density heatmap showing connection patterns"""
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. Connection density matrix between categories
        connection_matrix = np.zeros((3, 3))  # core, domestic, international
        category_names = ['Core', 'Domestic', 'International']
        category_map = {'core': 0, 'domestic': 1, 'international': 2}
        
        total_connections = defaultdict(int)
        
        for period, G in periods_data.items():
            for edge in G.edges():
                cat1 = G.nodes[edge[0]]['node_category']
                cat2 = G.nodes[edge[1]]['node_category']
                
                idx1, idx2 = category_map[cat1], category_map[cat2]
                connection_matrix[idx1][idx2] += 1
                connection_matrix[idx2][idx1] += 1  # Symmetric
                total_connections[(cat1, cat2)] += 1
        
        # Normalize by maximum
        connection_matrix = connection_matrix / np.max(connection_matrix)
        
        sns.heatmap(connection_matrix, annot=True, fmt='.2f', 
                    xticklabels=category_names, yticklabels=category_names,
                    cmap='Reds', ax=ax1, cbar_kws={'label': 'Connection Density'})
        ax1.set_title('Inter-Category Connection Density\n(Normalized)', fontweight='bold', fontsize=12)
        
        # 2. Network metrics evolution
        periods = list(periods_data.keys())
        period_labels = ['Pre-Crimea', 'Post-Crimea', 'COVID', 'War']
        
        metrics = {
            'density': [nx.density(G) for G in periods_data.values()],
            'clustering': [nx.average_clustering(G) for G in periods_data.values()],
            'components': [nx.number_connected_components(G) for G in periods_data.values()]
        }
        
        x = np.arange(len(periods))
        width = 0.25
        
        bars1 = ax2.bar(x - width, metrics['density'], width, label='Density', 
                       color=self.colors['core'], alpha=0.7)
        bars2 = ax2.bar(x, metrics['clustering'], width, label='Clustering', 
                       color=self.colors['domestic'], alpha=0.7)
        bars3 = ax2.bar(x + width, [c/10 for c in metrics['components']], width, 
                       label='Components/10', color=self.colors['international'], alpha=0.7)
        
        ax2.set_xlabel('Period')
        ax2.set_ylabel('Metric Value')
        ax2.set_title('Network Cohesion Metrics', fontweight='bold', fontsize=12)
        ax2.set_xticks(x)
        ax2.set_xticklabels(period_labels, rotation=45)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. Entity persistence patterns
        all_entities = set()
        for G in periods_data.values():
            all_entities.update(G.nodes())
        
        persistence_counts = {1: 0, 2: 0, 3: 0, 4: 0}  # Appears in N periods
        persistence_by_category = {'core': {1:0, 2:0, 3:0, 4:0}, 
                                  'domestic': {1:0, 2:0, 3:0, 4:0}, 
                                  'international': {1:0, 2:0, 3:0, 4:0}}
        
        for entity in all_entities:
            appearances = 0
            category = None
            for G in periods_data.values():
                if entity in G.nodes():
                    appearances += 1
                    if category is None:
                        category = G.nodes[entity]['node_category']
            
            persistence_counts[appearances] += 1
            if category:
                persistence_by_category[category][appearances] += 1
        
        # Stacked bar chart
        categories = ['core', 'domestic', 'international']
        bottom = np.zeros(4)
        
        for i, category in enumerate(categories):
            values = [persistence_by_category[category][j] for j in range(1, 5)]
            ax3.bar(range(1, 5), values, bottom=bottom, label=category.title(), 
                   color=self.colors[category], alpha=0.8)
            bottom += values
        
        ax3.set_xlabel('Number of Periods Entity Appears')
        ax3.set_ylabel('Number of Entities')
        ax3.set_title('Entity Persistence Patterns', fontweight='bold', fontsize=12)
        ax3.set_xticks(range(1, 5))
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. Core entity stability indicator
        core_entities_all_periods = set()
        for period, G in periods_data.items():
            period_core = {n for n in G.nodes() if G.nodes[n]['node_category'] == 'core'}
            if period == list(periods_data.keys())[0]:
                core_entities_all_periods = period_core
            else:
                core_entities_all_periods = core_entities_all_periods.intersection(period_core)
        
        # Show core stability as percentage
        period_core_stability = []
        for period, G in periods_data.items():
            period_core = {n for n in G.nodes() if G.nodes[n]['node_category'] == 'core'}
            if core_entities_all_periods:
                stability = len(period_core.intersection(core_entities_all_periods)) / len(core_entities_all_periods)
            else:
                stability = 0
            period_core_stability.append(stability * 100)
        
        bars = ax4.bar(period_labels, period_core_stability, color=self.colors['core'], alpha=0.8)
        ax4.set_ylabel('Core Stability (%)')
        ax4.set_title('Core Network Stability\n(% of core entities persistent)', fontweight='bold', fontsize=12)
        ax4.set_ylim(0, 100)
        ax4.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar, value in zip(bars, period_core_stability):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{value:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.savefig(save_path.replace('.png', '.pdf'), dpi=300, bbox_inches='tight', facecolor='white')
            print(f"Density heatmap saved: {save_path}")
        
        plt.show()
        return fig

def main():
    """Main execution function"""
    visualizer = AggregateNetworkVisualizer()
    
    # Load networks
    periods_data = {}
    period_files = {
        'pre_crimea': 'pre_crimea.csv',
        'post_crimea': 'post_crimea.csv', 
        'covid': 'covid.csv',
        'war': 'war.csv'
    }
    
    print("Loading networks for aggregate visualization...")
    for period_name, file_path in period_files.items():
        try:
            G = visualizer.create_network_from_csv(file_path, min_edge_weight=5)
            periods_data[period_name] = G
            print(f"✅ {period_name}: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        except Exception as e:
            print(f"❌ Error loading {period_name}: {e}")
            continue
    
    # Create aggregate visualizations
    print("\n1. Creating flow diagram (conceptual structure)...")
    flow_fig = visualizer.create_flow_diagram(
        periods_data, "network_flow_diagram.png"
    )
    
    print("\n2. Creating density heatmap (quantitative patterns)...")
    heatmap_fig = visualizer.create_density_heatmap(
        periods_data, "network_density_analysis.png"
    )
    
    print("\n🎉 Aggregate visualizations completed!")
    print("Files created:")
    print("• network_flow_diagram.png - Conceptual core-periphery structure")
    print("• network_density_analysis.png - Quantitative connection patterns")
    print("\nThese show the complete network patterns without individual node clutter!")

if __name__ == "__main__":
    main()
