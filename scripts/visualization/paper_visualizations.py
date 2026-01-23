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

class PaperVisualizationCreator:
    """
    Creates two focused visualizations for academic paper:
    1. Network Flexibility/Repurposing visualization
    2. Stable Core visualization
    """
    
    def __init__(self):
        self.core_entities = [
            'Кирилл Дмитриев', 'Российский фонд прямых инвестиций (РФПИ)', 'РФПИ',
            'Владимир Путин', 'Сбербанк', 'Внешэкономбанк (ВЭБ)', 'ВЭБ',
            'Банк ВТБ', 'ВТБ', 'Газпромбанк', 'ОАО «Газпром»', 'Роснефть',
            'Министерство финансов', 'Центральный банк', 'Банк России'
        ]
        
        # Academic color palette
        self.colors = {
            'core': '#2c3e50',           # Dark blue-gray (stable)
            'domestic': '#34495e',       # Medium gray (domestic)
            'international': '#e74c3c',  # Red (flexible/changing)
            'new_partners': '#f39c12',   # Orange (emerging)
            'persistent': '#27ae60',     # Green (stable relationships)
            'background': '#ecf0f1'      # Light gray background
        }
    
    def create_network_from_csv(self, file_path, min_edge_weight=10):
        """Create network with appropriate threshold"""
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
        """Classify nodes into core, domestic, or international"""
        entity_lower = entity_name.lower()
        
        # Check if it's a core entity
        if any(core.lower() in entity_lower for core in self.core_entities):
            return 'core'
        
        # Russian/domestic indicators
        russian_indicators = [
            'российский', 'russia', 'moscow', 'москва', 'санкт-петербург',
            'минфин', 'министерство', 'федеральн', 'госуд', 'рос', 'мин'
        ]
        
        if any(indicator in entity_lower for indicator in russian_indicators):
            return 'domestic'
        
        # International indicators
        international_indicators = [
            'china', 'chinese', 'saudi', 'qatar', 'emirates', 'japan', 'japanese',
            'germany', 'german', 'france', 'french', 'uk', 'britain', 'usa', 'american',
            'investment corporation', 'sovereign fund', 'international'
        ]
        
        if any(indicator in entity_lower for indicator in international_indicators):
            return 'international'
        
        return 'domestic'
    
    def create_flexibility_visualization(self, periods_data, save_path=None):
        """
        Page 1: Network Flexibility and Repurposing Visualization
        Shows how international partnerships adapt while core remains stable
        """
        
        fig = plt.figure(figsize=(12, 8))
        gs = gridspec.GridSpec(2, 2, height_ratios=[3, 1], width_ratios=[1, 1])
        
        # Main visualization showing network adaptation
        ax_main = fig.add_subplot(gs[0, :])
        
        # Calculate international partner changes
        period_names = ['Pre-Crimea\n(2012-2014)', 'Post-Crimea\n(2014-2017)', 
                       'COVID-19\n(2020-2022)', 'War Period\n(2022-2024)']
        periods = list(periods_data.keys())
        
        # Track international partners across periods
        all_international = set()
        period_international = {}
        
        for period, G in periods_data.items():
            intl_entities = {node for node in G.nodes() 
                           if G.nodes[node]['node_category'] == 'international'}
            period_international[period] = intl_entities
            all_international.update(intl_entities)
        
        # Categorize international partners by persistence
        persistent_partners = set()
        flexible_partners = set()
        
        for entity in all_international:
            appearances = sum(1 for period_set in period_international.values() 
                            if entity in period_set)
            if appearances >= 3:  # Appears in 3+ periods
                persistent_partners.add(entity)
            else:
                flexible_partners.add(entity)
        
        # Create horizontal timeline visualization
        y_positions = np.arange(len(periods))
        bar_height = 0.6
        
        # Draw stable core (consistent across all periods)
        core_counts = []
        domestic_counts = []
        international_counts = []
        
        for period in periods:
            G = periods_data[period]
            core_count = sum(1 for n in G.nodes() if G.nodes[n]['node_category'] == 'core')
            domestic_count = sum(1 for n in G.nodes() if G.nodes[n]['node_category'] == 'domestic')
            intl_count = sum(1 for n in G.nodes() if G.nodes[n]['node_category'] == 'international')
            
            core_counts.append(core_count)
            domestic_counts.append(domestic_count)
            international_counts.append(intl_count)
        
        # Stacked horizontal bars showing composition
        ax_main.barh(y_positions, core_counts, bar_height, 
                    color=self.colors['core'], alpha=0.9, label='Stable Core')
        ax_main.barh(y_positions, domestic_counts, bar_height, left=core_counts,
                    color=self.colors['domestic'], alpha=0.7, label='Domestic Network')
        ax_main.barh(y_positions, international_counts, bar_height, 
                    left=[c+d for c,d in zip(core_counts, domestic_counts)],
                    color=self.colors['international'], alpha=0.8, label='International Partners')
        
        # Add arrows showing flexibility
        for i in range(len(periods)-1):
            # Arrow showing adaptation between periods
            y_start = y_positions[i] + bar_height/2
            y_end = y_positions[i+1] - bar_height/2
            x_pos = max(core_counts) + max(domestic_counts) + max(international_counts) + 20
            
            ax_main.annotate('', xy=(x_pos, y_end), xytext=(x_pos, y_start),
                           arrowprops=dict(arrowstyle='->', color=self.colors['international'], 
                                         lw=2, alpha=0.7))
        
        # Add adaptation labels
        adaptation_events = ['Sanctions &\nIsolation', 'Health\nDiplomacy', 'Wartime\nAdaptation']
        for i, event in enumerate(adaptation_events):
            y_pos = y_positions[i] + 0.5
            x_pos = max(core_counts) + max(domestic_counts) + max(international_counts) + 40
            ax_main.text(x_pos, y_pos, event, fontsize=9, ha='left', va='center',
                        style='italic', color=self.colors['international'])
        
        ax_main.set_yticks(y_positions)
        ax_main.set_yticklabels(period_names, fontsize=11)
        ax_main.set_xlabel('Number of Entities', fontsize=12, fontweight='bold')
        ax_main.set_title('Network Flexibility: Stable Core with Adaptive International Partnerships',
                         fontsize=14, fontweight='bold', pad=20)
        
        # Add value labels on bars
        for i, (core, domestic, intl) in enumerate(zip(core_counts, domestic_counts, international_counts)):
            total = core + domestic + intl
            ax_main.text(total + 5, y_positions[i], f'n={total}', 
                        va='center', fontweight='bold', fontsize=10)
        
        ax_main.legend(loc='lower right', fontsize=10)
        ax_main.grid(True, alpha=0.3, axis='x')
        
        # Bottom left: Core stability metrics
        ax_stability = fig.add_subplot(gs[1, 0])
        
        # Calculate core stability (percentage of core entities that persist)
        core_entities_by_period = {}
        for period, G in periods_data.items():
            core_entities_by_period[period] = {n for n in G.nodes() 
                                             if G.nodes[n]['node_category'] == 'core'}
        
        # Find entities that appear in all periods
        all_periods_core = set.intersection(*core_entities_by_period.values()) if core_entities_by_period else set()
        
        stability_scores = []
        for period in periods:
            period_core = core_entities_by_period[period]
            if period_core:
                stability = len(all_periods_core.intersection(period_core)) / len(period_core)
            else:
                stability = 0
            stability_scores.append(stability * 100)
        
        bars = ax_stability.bar(range(len(periods)), stability_scores, 
                               color=self.colors['core'], alpha=0.8)
        ax_stability.set_xticks(range(len(periods)))
        ax_stability.set_xticklabels(['Pre', 'Post', 'COVID', 'War'], fontsize=10)
        ax_stability.set_ylabel('Core Stability (%)', fontsize=11, fontweight='bold')
        ax_stability.set_title('Domestic Core Stability', fontsize=12, fontweight='bold')
        ax_stability.set_ylim(0, 100)
        ax_stability.grid(True, alpha=0.3)
        
        # Add percentage labels
        for bar, score in zip(bars, stability_scores):
            height = bar.get_height()
            ax_stability.text(bar.get_x() + bar.get_width()/2., height + 1,
                            f'{score:.0f}%', ha='center', va='bottom', fontweight='bold')
        
        # Bottom right: International partner turnover
        ax_turnover = fig.add_subplot(gs[1, 1])
        
        # Calculate new vs persistent international partners
        new_partners = []
        total_partners = []
        
        previous_partners = set()
        for period in periods:
            current_partners = period_international[period]
            new_in_period = current_partners - previous_partners
            
            new_partners.append(len(new_in_period))
            total_partners.append(len(current_partners))
            
            previous_partners.update(current_partners)
        
        x_pos = np.arange(len(periods))
        width = 0.35
        
        bars1 = ax_turnover.bar(x_pos - width/2, total_partners, width, 
                               color=self.colors['international'], alpha=0.6, label='Total')
        bars2 = ax_turnover.bar(x_pos + width/2, new_partners, width,
                               color=self.colors['new_partners'], alpha=0.8, label='New')
        
        ax_turnover.set_xticks(x_pos)
        ax_turnover.set_xticklabels(['Pre', 'Post', 'COVID', 'War'], fontsize=10)
        ax_turnover.set_ylabel('International Partners', fontsize=11, fontweight='bold')
        ax_turnover.set_title('Partnership Flexibility', fontsize=12, fontweight='bold')
        ax_turnover.legend(fontsize=9)
        ax_turnover.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.savefig(save_path.replace('.png', '.pdf'), dpi=300, bbox_inches='tight', facecolor='white')
            print(f"Flexibility visualization saved: {save_path}")
        
        plt.show()
        return fig
    
    def create_stable_core_visualization(self, periods_data, save_path=None):
        """
        Page 2: Stable Political-Economic Core Visualization
        Shows the persistent domestic institutional network
        """
        
        fig = plt.figure(figsize=(12, 8))
        gs = gridspec.GridSpec(2, 2, height_ratios=[2, 1], width_ratios=[2, 1])
        
        # Main network diagram showing core persistence
        ax_main = fig.add_subplot(gs[0, :])
        
        # Find entities that appear in all periods
        all_entities = {}
        for period, G in periods_data.items():
            for node in G.nodes():
                if node not in all_entities:
                    all_entities[node] = {'periods': set(), 'category': G.nodes[node]['node_category']}
                all_entities[node]['periods'].add(period)
        
        # Categorize by persistence
        persistent_entities = {name: data for name, data in all_entities.items() 
                             if len(data['periods']) == len(periods_data)}
        
        # Separate by category
        persistent_core = {name: data for name, data in persistent_entities.items() 
                          if data['category'] == 'core'}
        persistent_domestic = {name: data for name, data in persistent_entities.items() 
                              if data['category'] == 'domestic'}
        
        # Create concentric circles layout
        ax_main.set_xlim(-1.2, 1.2)
        ax_main.set_ylim(-1.2, 1.2)
        ax_main.set_aspect('equal')
        
        # Draw background circles
        core_circle = Circle((0, 0), 0.3, fill=False, linestyle='-', 
                           color=self.colors['core'], linewidth=3, alpha=0.7)
        domestic_circle = Circle((0, 0), 0.8, fill=False, linestyle='--', 
                               color=self.colors['domestic'], linewidth=2, alpha=0.5)
        ax_main.add_patch(core_circle)
        ax_main.add_patch(domestic_circle)
        
        # Position core entities in center
        if persistent_core:
            core_entities = list(persistent_core.keys())[:8]  # Top 8 for readability
            angles = np.linspace(0, 2*np.pi, len(core_entities), endpoint=False)
            
            for i, (entity, angle) in enumerate(zip(core_entities, angles)):
                x = 0.2 * np.cos(angle)
                y = 0.2 * np.sin(angle)
                
                # Draw entity circle
                entity_circle = Circle((x, y), 0.08, facecolor=self.colors['core'], 
                                     alpha=0.8, edgecolor='black', linewidth=1)
                ax_main.add_patch(entity_circle)
                
                # Add label
                label = 'RDIF' if 'рфпи' in entity.lower() else entity[:8] + '...' if len(entity) > 8 else entity
                ax_main.text(x, y-0.15, label, ha='center', va='top', fontsize=8, 
                           fontweight='bold', bbox=dict(boxstyle='round,pad=0.2', 
                           facecolor='white', alpha=0.8))
        
        # Position domestic entities in outer ring (sample)
        if persistent_domestic:
            domestic_sample = list(persistent_domestic.keys())[:12]  # Sample for readability
            angles = np.linspace(0, 2*np.pi, len(domestic_sample), endpoint=False)
            
            for entity, angle in zip(domestic_sample, angles):
                x = 0.65 * np.cos(angle)
                y = 0.65 * np.sin(angle)
                
                # Draw smaller circles for domestic entities
                entity_circle = Circle((x, y), 0.05, facecolor=self.colors['domestic'], 
                                     alpha=0.6, edgecolor='black', linewidth=0.5)
                ax_main.add_patch(entity_circle)
        
        # Add connecting lines showing relationships
        if len(persistent_core) > 1:
            core_entities = list(persistent_core.keys())[:8]
            angles = np.linspace(0, 2*np.pi, len(core_entities), endpoint=False)
            
            for i in range(len(core_entities)):
                for j in range(i+1, min(i+3, len(core_entities))):  # Connect to nearest neighbors
                    x1 = 0.2 * np.cos(angles[i])
                    y1 = 0.2 * np.sin(angles[i])
                    x2 = 0.2 * np.cos(angles[j])
                    y2 = 0.2 * np.sin(angles[j])
                    
                    ax_main.plot([x1, x2], [y1, y2], '-', color=self.colors['core'], 
                               alpha=0.4, linewidth=2)
        
        # Add labels for circles
        ax_main.text(0, -0.4, 'STABLE CORE\n(All Periods)', ha='center', va='center',
                    fontsize=12, fontweight='bold', color=self.colors['core'],
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9))
        
        ax_main.text(0, -0.9, 'Persistent Domestic Network', ha='center', va='center',
                    fontsize=11, style='italic', color=self.colors['domestic'])
        
        ax_main.set_title('Stable Political-Economic Core: Persistent Institutional Network',
                         fontsize=14, fontweight='bold', pad=20)
        ax_main.axis('off')
        
        # Bottom left: Persistence statistics
        ax_stats = fig.add_subplot(gs[1, 0])
        
        # Calculate persistence statistics
        total_entities = len(all_entities)
        persistent_count = len(persistent_entities)
        core_persistent = len(persistent_core)
        domestic_persistent = len(persistent_domestic)
        
        categories = ['All Entities', 'Core Entities', 'Domestic Entities']
        persistence_rates = [
            (persistent_count / total_entities) * 100,
            (core_persistent / max(1, len([e for e in all_entities.values() if e['category'] == 'core']))) * 100,
            (domestic_persistent / max(1, len([e for e in all_entities.values() if e['category'] == 'domestic']))) * 100
        ]
        
        bars = ax_stats.bar(categories, persistence_rates, 
                           color=[self.colors['background'], self.colors['core'], self.colors['domestic']],
                           alpha=0.8, edgecolor='black', linewidth=1)
        
        ax_stats.set_ylabel('Persistence Rate (%)', fontsize=11, fontweight='bold')
        ax_stats.set_title('Cross-Period Persistence', fontsize=12, fontweight='bold')
        ax_stats.set_ylim(0, 100)
        ax_stats.tick_params(axis='x', rotation=45)
        ax_stats.grid(True, alpha=0.3)
        
        # Add percentage labels
        for bar, rate in zip(bars, persistence_rates):
            height = bar.get_height()
            ax_stats.text(bar.get_x() + bar.get_width()/2., height + 2,
                         f'{rate:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        # Bottom right: Network density over time
        ax_density = fig.add_subplot(gs[1, 1])
        
        periods = list(periods_data.keys())
        period_labels = ['Pre-Crimea', 'Post-Crimea', 'COVID', 'War']
        
        # Calculate core network density (connections within core entities)
        core_densities = []
        for period, G in periods_data.items():
            core_nodes = [n for n in G.nodes() if G.nodes[n]['node_category'] == 'core']
            if len(core_nodes) > 1:
                core_subgraph = G.subgraph(core_nodes)
                density = nx.density(core_subgraph)
            else:
                density = 0
            core_densities.append(density)
        
        ax_density.plot(range(len(periods)), core_densities, 'o-', 
                       color=self.colors['core'], linewidth=3, markersize=8,
                       markerfacecolor=self.colors['core'], markeredgecolor='black')
        
        ax_density.set_xticks(range(len(periods)))
        ax_density.set_xticklabels(['Pre', 'Post', 'COVID', 'War'], fontsize=10)
        ax_density.set_ylabel('Core Network Density', fontsize=11, fontweight='bold')
        ax_density.set_title('Core Cohesion Over Time', fontsize=12, fontweight='bold')
        ax_density.grid(True, alpha=0.3)
        ax_density.set_ylim(0, max(core_densities) * 1.1 if core_densities else 1)
        
        # Add trend line
        if len(core_densities) > 1:
            z = np.polyfit(range(len(periods)), core_densities, 1)
            p = np.poly1d(z)
            ax_density.plot(range(len(periods)), p(range(len(periods))), "--", 
                           alpha=0.7, color=self.colors['core'])
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.savefig(save_path.replace('.png', '.pdf'), dpi=300, bbox_inches='tight', facecolor='white')
            print(f"Stable core visualization saved: {save_path}")
        
        plt.show()
        return fig

def main():
    """Create both paper visualizations"""
    visualizer = PaperVisualizationCreator()
    
    # Load networks
    periods_data = {}
    period_files = {
        'pre_crimea': 'pre_crimea.csv',
        'post_crimea': 'post_crimea.csv', 
        'covid': 'covid.csv',
        'war': 'war.csv'
    }
    
    print("Loading networks for paper visualizations...")
    for period_name, file_path in period_files.items():
        try:
            G = visualizer.create_network_from_csv(file_path, min_edge_weight=15)
            periods_data[period_name] = G
            print(f"✅ {period_name}: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        except Exception as e:
            print(f"❌ Error loading {period_name}: {e}")
            continue
    
    print("\n" + "="*60)
    print("CREATING PAPER VISUALIZATIONS")
    print("="*60)
    
    # Page 1: Network Flexibility and Repurposing
    print("\n📊 Creating Page 1: Network Flexibility & Repurposing...")
    flexibility_fig = visualizer.create_flexibility_visualization(
        periods_data, "paper_figure_1_network_flexibility.png"
    )
    
    # Page 2: Stable Political-Economic Core  
    print("\n📊 Creating Page 2: Stable Political-Economic Core...")
    core_fig = visualizer.create_stable_core_visualization(
        periods_data, "paper_figure_2_stable_core.png"
    )
    
    print("\n" + "="*60)
    print("PAPER VISUALIZATIONS COMPLETED")
    print("="*60)
    print("\n📄 Figure 1: Network Flexibility & Repurposing")
    print("   → Shows international partnership adaptation")
    print("   → Demonstrates network repurposing capability")
    print("   → File: paper_figure_1_network_flexibility.png/.pdf")
    
    print("\n📄 Figure 2: Stable Political-Economic Core")
    print("   → Shows persistent domestic institutional network")
    print("   → Demonstrates core stability across periods")
    print("   → File: paper_figure_2_stable_core.png/.pdf")
    
    print("\n✅ Both visualizations ready for academic paper inclusion!")

if __name__ == "__main__":
    main()

