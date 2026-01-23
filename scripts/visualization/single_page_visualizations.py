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

class SinglePageVisualizations:
    """
    Creates two separate, clean visualizations - one per page
    """
    
    def __init__(self):
        self.core_entities = [
            'Кирилл Дмитриев', 'Российский фонд прямых инвестиций (РФПИ)', 'РФПИ',
            'Владимир Путин', 'Сбербанк', 'Внешэкономбанк (ВЭБ)', 'ВЭБ',
            'Банк ВТБ', 'ВТБ', 'Газпромбанк', 'ОАО «Газпром»', 'Роснефть',
            'Министерство финансов', 'Центральный банк', 'Банк России'
        ]
        
        # Clean academic colors
        self.colors = {
            'core': '#2c3e50',           # Dark blue-gray
            'domestic': '#34495e',       # Medium gray
            'international': '#e74c3c',  # Red
            'new_partners': '#f39c12',   # Orange
            'stable': '#27ae60',         # Green
        }
    
    def create_network_from_csv(self, file_path, min_edge_weight=15):
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
    
    def create_page1_network_flexibility(self, periods_data, save_path=None):
        """
        PAGE 1: Network Flexibility - Single clean visualization
        Shows how international partnerships change while core remains stable
        """
        
        fig, ax = plt.subplots(1, 1, figsize=(12, 9))
        
        # Calculate data for all periods
        periods = list(periods_data.keys())
        period_names = ['Pre-Crimea\n(2012-2014)', 'Post-Crimea\n(2014-2017)', 
                       'COVID-19\n(2020-2022)', 'War Period\n(2022-2024)']
        
        # Track international partners across periods
        period_international = {}
        core_counts = []
        domestic_counts = []
        international_counts = []
        new_international = []
        
        previous_partners = set()
        
        for i, period in enumerate(periods):
            G = periods_data[period]
            
            # Count by category
            core_count = sum(1 for n in G.nodes() if G.nodes[n]['node_category'] == 'core')
            domestic_count = sum(1 for n in G.nodes() if G.nodes[n]['node_category'] == 'domestic')
            
            # International partners
            intl_entities = {node for node in G.nodes() 
                           if G.nodes[node]['node_category'] == 'international'}
            intl_count = len(intl_entities)
            
            # New international partners
            new_in_period = intl_entities - previous_partners
            new_count = len(new_in_period)
            
            core_counts.append(core_count)
            domestic_counts.append(domestic_count)
            international_counts.append(intl_count)
            new_international.append(new_count)
            
            period_international[period] = intl_entities
            previous_partners.update(intl_entities)
        
        # Create stacked horizontal bar chart
        y_positions = np.arange(len(periods))
        bar_height = 0.6
        
        # Plot bars with proper spacing
        bars1 = ax.barh(y_positions, core_counts, bar_height, 
                       color=self.colors['core'], alpha=0.9, label='Stable Core')
        bars2 = ax.barh(y_positions, domestic_counts, bar_height, left=core_counts,
                       color=self.colors['domestic'], alpha=0.7, label='Domestic Network')
        bars3 = ax.barh(y_positions, international_counts, bar_height, 
                       left=[c+d for c,d in zip(core_counts, domestic_counts)],
                       color=self.colors['international'], alpha=0.8, label='International Partners')
        
        # Add total counts at end of bars with proper spacing
        for i, (core, domestic, intl) in enumerate(zip(core_counts, domestic_counts, international_counts)):
            total = core + domestic + intl
            ax.text(total + 30, y_positions[i], f'n={total}', 
                   va='center', ha='left', fontweight='bold', fontsize=12)
        
        # Add new partner indicators with careful positioning
        for i, new_count in enumerate(new_international):
            if new_count > 0:
                x_pos = core_counts[i] + domestic_counts[i] + international_counts[i] + 100
                ax.text(x_pos, y_positions[i], f'+{new_count} new', 
                       va='center', ha='left', fontsize=10, style='italic',
                       color=self.colors['new_partners'], fontweight='bold')
        
        # Customize axes with proper spacing
        ax.set_yticks(y_positions)
        ax.set_yticklabels(period_names, fontsize=13, fontweight='normal')
        ax.set_xlabel('Number of Entities', fontsize=14, fontweight='bold')
        
        # Set title with proper spacing
        ax.set_title('Network Flexibility: Stable Core with Adaptive International Partnerships',
                    fontsize=16, fontweight='bold', pad=25)
        
        # Legend with proper positioning
        ax.legend(loc='lower right', fontsize=12, framealpha=0.95)
        
        # Grid for readability
        ax.grid(True, alpha=0.3, axis='x')
        
        # Set x-axis limits to prevent overlap
        max_total = max([c+d+i for c,d,i in zip(core_counts, domestic_counts, international_counts)])
        ax.set_xlim(0, max_total + 200)
        
        # Add adaptation annotations with careful positioning
        adaptation_events = [
            ('Sanctions Response', 0.5, self.colors['international']),
            ('Health Diplomacy', 1.5, self.colors['international']),
            ('Wartime Adaptation', 2.5, self.colors['international'])
        ]
        
        for event, y_pos, color in adaptation_events:
            ax.annotate(event, xy=(max_total + 50, y_pos), 
                       fontsize=11, ha='left', va='center',
                       style='italic', color=color, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                               alpha=0.8, edgecolor=color))
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.savefig(save_path.replace('.png', '.pdf'), dpi=300, bbox_inches='tight', facecolor='white')
            print(f"Page 1 - Network Flexibility saved: {save_path}")
        
        plt.show()
        return fig
    
    def create_page2_stable_core(self, periods_data, save_path=None):
        """
        PAGE 2: Stable Core - Single clean visualization
        Shows the persistent domestic institutional network
        """
        
        fig, ax = plt.subplots(1, 1, figsize=(12, 9))
        
        # Find entities that appear in all periods
        all_entities = {}
        for period, G in periods_data.items():
            for node in G.nodes():
                if node not in all_entities:
                    all_entities[node] = {'periods': set(), 'category': G.nodes[node]['node_category']}
                all_entities[node]['periods'].add(period)
        
        # Find persistent entities (appear in all periods)
        total_periods = len(periods_data)
        persistent_entities = {name: data for name, data in all_entities.items() 
                             if len(data['periods']) == total_periods}
        
        # Separate by category
        persistent_core = [name for name, data in persistent_entities.items() 
                          if data['category'] == 'core']
        persistent_domestic = [name for name, data in persistent_entities.items() 
                              if data['category'] == 'domestic']
        
        # Create concentric visualization
        ax.set_xlim(-1.3, 1.3)
        ax.set_ylim(-1.3, 1.3)
        ax.set_aspect('equal')
        
        # Draw background circles with labels
        core_circle = Circle((0, 0), 0.35, fill=False, linestyle='-', 
                           color=self.colors['core'], linewidth=4, alpha=0.8)
        domestic_circle = Circle((0, 0), 0.85, fill=False, linestyle='--', 
                               color=self.colors['domestic'], linewidth=3, alpha=0.6)
        ax.add_patch(core_circle)
        ax.add_patch(domestic_circle)
        
        # Core entities positioning - carefully spaced
        if persistent_core:
            # Limit to top entities for readability
            core_sample = persistent_core[:6]  # Top 6 for clean layout
            angles = np.linspace(0, 2*np.pi, len(core_sample), endpoint=False)
            
            for i, (entity, angle) in enumerate(zip(core_sample, angles)):
                x = 0.25 * np.cos(angle)
                y = 0.25 * np.sin(angle)
                
                # Draw entity node
                entity_circle = Circle((x, y), 0.08, facecolor=self.colors['core'], 
                                     alpha=0.9, edgecolor='black', linewidth=2)
                ax.add_patch(entity_circle)
                
                # Add connecting lines between core entities
                for j, (other_entity, other_angle) in enumerate(zip(core_sample, angles)):
                    if i < j:  # Avoid duplicate lines
                        x2 = 0.25 * np.cos(other_angle)
                        y2 = 0.25 * np.sin(other_angle)
                        ax.plot([x, x2], [y, y2], '-', color=self.colors['core'], 
                               alpha=0.4, linewidth=2)
                
                # Entity labels - positioned to avoid overlap
                label_radius = 0.45
                label_x = label_radius * np.cos(angle)
                label_y = label_radius * np.sin(angle)
                
                # Shorten labels for readability
                if 'рфпи' in entity.lower() or 'российский фонд' in entity.lower():
                    label = 'RDIF'
                elif 'путин' in entity.lower():
                    label = 'Putin'
                elif 'сбербанк' in entity.lower():
                    label = 'Sberbank'
                elif 'внешэконом' in entity.lower():
                    label = 'VEB'
                elif 'втб' in entity.lower():
                    label = 'VTB'
                elif 'газпром' in entity.lower():
                    label = 'Gazprom'
                else:
                    label = entity[:8] + '...' if len(entity) > 8 else entity
                
                # Position text to avoid overlap
                ha = 'center'
                va = 'center'
                if abs(label_x) > 0.1:
                    ha = 'left' if label_x > 0 else 'right'
                if abs(label_y) > 0.1:
                    va = 'bottom' if label_y > 0 else 'top'
                
                ax.text(label_x, label_y, label, ha=ha, va=va, fontsize=11, 
                       fontweight='bold', 
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                               alpha=0.9, edgecolor=self.colors['core']))
        
        # Domestic entities - sample in outer ring
        if persistent_domestic:
            domestic_sample = persistent_domestic[:8]  # Sample for clean layout
            angles = np.linspace(0, 2*np.pi, len(domestic_sample), endpoint=False)
            
            for entity, angle in zip(domestic_sample, angles):
                x = 0.7 * np.cos(angle)
                y = 0.7 * np.sin(angle)
                
                # Draw smaller nodes for domestic entities
                entity_circle = Circle((x, y), 0.04, facecolor=self.colors['domestic'], 
                                     alpha=0.7, edgecolor='black', linewidth=1)
                ax.add_patch(entity_circle)
        
        # Add circle labels with proper positioning
        ax.text(0, -0.55, 'STABLE CORE', ha='center', va='center',
                fontsize=14, fontweight='bold', color=self.colors['core'],
                bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.95,
                         edgecolor=self.colors['core'], linewidth=2))
        
        ax.text(0, -1.05, 'Persistent Domestic Network', ha='center', va='center',
                fontsize=12, style='italic', color=self.colors['domestic'],
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.9))
        
        # Add statistics in corners - carefully positioned
        total_entities = len(all_entities)
        persistent_count = len(persistent_entities)
        core_persistent_count = len(persistent_core)
        
        # Top right statistics
        stats_text = f"Persistent Entities: {persistent_count}/{total_entities}\n"
        stats_text += f"Core Persistence: {core_persistent_count} entities\n"
        stats_text += f"Stability Rate: {(persistent_count/total_entities)*100:.1f}%"
        
        ax.text(0.95, 0.95, stats_text, transform=ax.transAxes, 
               fontsize=11, ha='right', va='top', fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgray', alpha=0.9))
        
        # Title with proper spacing
        ax.set_title('Stable Political-Economic Core: Persistent Institutional Network',
                    fontsize=16, fontweight='bold', pad=25)
        
        ax.axis('off')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.savefig(save_path.replace('.png', '.pdf'), dpi=300, bbox_inches='tight', facecolor='white')
            print(f"Page 2 - Stable Core saved: {save_path}")
        
        plt.show()
        return fig

def main():
    """Create both single-page visualizations"""
    visualizer = SinglePageVisualizations()
    
    # Load networks
    periods_data = {}
    period_files = {
        'pre_crimea': 'pre_crimea.csv',
        'post_crimea': 'post_crimea.csv', 
        'covid': 'covid.csv',
        'war': 'war.csv'
    }
    
    print("Loading networks for single-page visualizations...")
    for period_name, file_path in period_files.items():
        try:
            G = visualizer.create_network_from_csv(file_path, min_edge_weight=15)
            periods_data[period_name] = G
            print(f"✅ {period_name}: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        except Exception as e:
            print(f"❌ Error loading {period_name}: {e}")
            continue
    
    print("\n" + "="*60)
    print("CREATING SINGLE-PAGE VISUALIZATIONS")
    print("="*60)
    
    # Page 1: Network Flexibility
    print("\n📄 Creating Page 1: Network Flexibility...")
    page1_fig = visualizer.create_page1_network_flexibility(
        periods_data, "figure_1_network_flexibility.png"
    )
    
    # Page 2: Stable Core  
    print("\n📄 Creating Page 2: Stable Core...")
    page2_fig = visualizer.create_page2_stable_core(
        periods_data, "figure_2_stable_core.png"
    )
    
    print("\n" + "="*60)
    print("SINGLE-PAGE VISUALIZATIONS COMPLETED")
    print("="*60)
    print("\n✅ Figure 1: Network Flexibility (Claim 1)")
    print("   → One clean horizontal bar chart")
    print("   → Shows adaptation while core stays stable")
    print("   → File: figure_1_network_flexibility.png/.pdf")
    
    print("\n✅ Figure 2: Stable Core (Claim 2)")
    print("   → One clean concentric circle diagram")
    print("   → Shows persistent institutional network")
    print("   → File: figure_2_stable_core.png/.pdf")
    
    print("\n🎯 Both figures ready for paper - one per page, no text overlap!")

if __name__ == "__main__":
    main()

