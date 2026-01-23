import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from networkx.algorithms import community
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo
from collections import Counter, defaultdict
import seaborn as sns

class ComprehensiveNetworkVisualizer:
    """
    Visualizer for the complete network with focus on core-periphery structure
    and the stable domestic core vs. flexible international periphery
    """
    
    def __init__(self):
        self.core_entities = [
            'Кирилл Дмитриев', 'Российский фонд прямых инвестиций (РФПИ)', 'РФПИ',
            'Владимир Путин', 'Сбербанк', 'Внешэкономбанк (ВЭБ)', 'ВЭБ',
            'Банк ВТБ', 'ВТБ', 'Газпромбанк', 'ОАО «Газпром»', 'Роснефт',
            'Министерство финансов', 'Центральный банк', 'Банк России'
        ]
        
        self.russian_indicators = [
            'российский', 'russia', 'moscow', 'москва', 'санкт-петербург',
            'минфин', 'министерство', 'федеральн', 'госуд'
        ]
        
    def create_network_from_csv(self, file_path, min_edge_weight=10):
        """Create network with lower threshold to capture more entities"""
        df = pd.read_csv(file_path)
        
        # Create co-occurrence matrix
        article_entities = df.groupby('Article_ID')['Entity'].apply(list).reset_index()
        
        edges = []
        edge_weights = {}
        
        for _, row in article_entities.iterrows():
            entities = row['Entity']
            if len(entities) < 2:
                continue
                
            for i in range(len(entities)):
                for j in range(i + 1, len(entities)):
                    entity1, entity2 = entities[i], entities[j]
                    edge = tuple(sorted([entity1, entity2]))
                    
                    if edge in edge_weights:
                        edge_weights[edge] += 1
                    else:
                        edge_weights[edge] = 1
        
        # Filter edges by minimum weight
        filtered_edges = [(e[0], e[1], w) for e, w in edge_weights.items() if w >= min_edge_weight]
        
        # Create network
        G = nx.Graph()
        G.add_weighted_edges_from(filtered_edges)
        
        # Add comprehensive node attributes
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
            
            # Classify as core, domestic, or international
            G.nodes[node]['node_category'] = self.classify_node_category(node)
            
        return G
    
    def classify_node_category(self, entity_name):
        """Classify nodes into core, domestic, or international categories"""
        entity_lower = entity_name.lower()
        
        # Check if it's a core entity
        if any(core in entity_lower for core in [e.lower() for e in self.core_entities]):
            return 'core'
        
        # Check if it's Russian/domestic
        if any(indicator in entity_lower for indicator in self.russian_indicators):
            return 'domestic'
        
        # Check for obvious international indicators
        international_indicators = [
            'china', 'chinese', 'saudi', 'qatar', 'emirates', 'japan', 'japanese',
            'germany', 'german', 'france', 'french', 'uk', 'britain', 'usa', 'american',
            'investment corporation', 'sovereign fund', 'international'
        ]
        
        if any(indicator in entity_lower for indicator in international_indicators):
            return 'international'
        
        # Default to domestic if unclear
        return 'domestic'
    
    def calculate_persistence_scores(self, periods_data):
        """Calculate how persistent each entity is across periods"""
        entity_periods = defaultdict(set)
        
        for period, G in periods_data.items():
            for node in G.nodes():
                entity_periods[node].add(period)
        
        persistence_scores = {}
        total_periods = len(periods_data)
        
        for entity, periods in entity_periods.items():
            persistence_scores[entity] = len(periods) / total_periods
        
        return persistence_scores
    
    def create_core_periphery_visualization(self, periods_data, output_file="core_periphery_network.html"):
        """Create comprehensive visualization showing core-periphery structure"""
        
        # Combine all periods to get complete network
        combined_G = nx.Graph()
        
        for period, G in periods_data.items():
            for node in G.nodes():
                if not combined_G.has_node(node):
                    combined_G.add_node(node, **G.nodes[node])
            
            for edge in G.edges(data=True):
                if combined_G.has_edge(edge[0], edge[1]):
                    combined_G[edge[0]][edge[1]]['weight'] += edge[2]['weight']
                else:
                    combined_G.add_edge(edge[0], edge[1], **edge[2])
        
        print(f"Complete network: {combined_G.number_of_nodes()} nodes, {combined_G.number_of_edges()} edges")
        
        # Calculate persistence scores
        persistence_scores = self.calculate_persistence_scores(periods_data)
        
        # Calculate centrality measures
        degree_centrality = nx.degree_centrality(combined_G)
        betweenness_centrality = nx.betweenness_centrality(combined_G, k=min(200, combined_G.number_of_nodes()))
        
        # Create layout optimized for core-periphery structure
        # Use spring layout with adjusted parameters to separate core from periphery
        pos = nx.spring_layout(combined_G, k=1.5, iterations=100, seed=42)
        
        # Adjust positions to emphasize core-periphery structure
        for node in combined_G.nodes():
            category = combined_G.nodes[node]['node_category']
            if category == 'core':
                # Pull core nodes toward center
                pos[node] = (pos[node][0] * 0.3, pos[node][1] * 0.3)
            elif category == 'domestic':
                # Keep domestic nodes in middle ring
                pos[node] = (pos[node][0] * 0.7, pos[node][1] * 0.7)
            # International nodes stay at periphery
        
        # Prepare data for plotly
        edge_x, edge_y = [], []
        edge_weights = []
        
        for edge in combined_G.edges(data=True):
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            edge_weights.append(edge[2]['weight'])
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                'Complete Network: Core-Periphery Structure',
                'Node Categories Distribution',
                'Persistence Across Periods',
                'Core Entities Centrality'
            ],
            specs=[[{"type": "scatter"}, {"type": "bar"}],
                   [{"type": "scatter"}, {"type": "bar"}]]
        )
        
        # 1. Main network visualization
        # Draw edges with varying opacity based on weight
        max_weight = max(edge_weights) if edge_weights else 1
        normalized_weights = [w/max_weight for w in edge_weights]
        
        fig.add_trace(
            go.Scatter(x=edge_x, y=edge_y, mode='lines',
                      line=dict(width=0.5, color='rgba(125,125,125,0.2)'),
                      hoverinfo='none', showlegend=False),
            row=1, col=1
        )
        
        # Draw nodes by category
        categories = ['core', 'domestic', 'international']
        colors = ['#e74c3c', '#3498db', '#2ecc71']  # Red, Blue, Green
        
        for i, category in enumerate(categories):
            category_nodes = [node for node in combined_G.nodes() 
                            if combined_G.nodes[node]['node_category'] == category]
            
            if not category_nodes:
                continue
                
            node_x = [pos[node][0] for node in category_nodes]
            node_y = [pos[node][1] for node in category_nodes]
            
            # Size based on degree centrality and persistence
            node_sizes = []
            node_text = []
            
            for node in category_nodes:
                centrality = degree_centrality.get(node, 0)
                persistence = persistence_scores.get(node, 0)
                occurrences = combined_G.nodes[node].get('total_occurrences', 0)
                
                # Size calculation emphasizing persistence and centrality
                size = max(8, min(40, 
                    centrality * 200 + 
                    persistence * 100 + 
                    occurrences / 50
                ))
                node_sizes.append(size)
                
                node_text.append(
                    f"{node}<br>"
                    f"Category: {category.title()}<br>"
                    f"Persistence: {persistence:.2f}<br>"
                    f"Degree Centrality: {centrality:.3f}<br>"
                    f"Occurrences: {occurrences}"
                )
            
            fig.add_trace(
                go.Scatter(x=node_x, y=node_y, mode='markers+text',
                          marker=dict(size=node_sizes, color=colors[i],
                                    line=dict(width=1, color='black'),
                                    opacity=0.8),
                          text=[node[:15] + '...' if len(node) > 15 else node 
                               for node in category_nodes],
                          textposition="middle center",
                          textfont=dict(size=8),
                          hovertext=node_text,
                          hoverinfo='text',
                          name=f'{category.title()} Entities',
                          showlegend=True),
                row=1, col=1
            )
        
        # 2. Category distribution
        category_counts = Counter([combined_G.nodes[node]['node_category'] 
                                 for node in combined_G.nodes()])
        
        fig.add_trace(
            go.Bar(x=list(category_counts.keys()), 
                  y=list(category_counts.values()),
                  marker_color=colors[:len(category_counts)],
                  showlegend=False),
            row=1, col=2
        )
        
        # 3. Persistence analysis
        persistence_data = [(entity, score) for entity, score in persistence_scores.items()]
        persistence_data.sort(key=lambda x: x[1], reverse=True)
        
        # Show top 20 most persistent entities
        top_persistent = persistence_data[:20]
        entities, scores = zip(*top_persistent)
        
        # Color by category
        bar_colors = []
        for entity in entities:
            category = combined_G.nodes[entity]['node_category']
            if category == 'core':
                bar_colors.append('#e74c3c')
            elif category == 'domestic':
                bar_colors.append('#3498db')
            else:
                bar_colors.append('#2ecc71')
        
        fig.add_trace(
            go.Scatter(x=list(scores), y=list(range(len(entities))),
                      mode='markers',
                      marker=dict(size=10, color=bar_colors),
                      text=list(entities),
                      textposition="middle right",
                      showlegend=False),
            row=2, col=1
        )
        
        # 4. Core entities centrality comparison
        core_entities_in_network = [node for node in combined_G.nodes() 
                                   if combined_G.nodes[node]['node_category'] == 'core']
        
        if core_entities_in_network:
            core_centralities = [(entity, degree_centrality.get(entity, 0)) 
                               for entity in core_entities_in_network]
            core_centralities.sort(key=lambda x: x[1], reverse=True)
            
            core_entities, core_cents = zip(*core_centralities)
            
            fig.add_trace(
                go.Bar(x=list(core_entities), y=list(core_cents),
                      marker_color='#e74c3c',
                      showlegend=False),
                row=2, col=2
            )
        
        # Update layout
        fig.update_layout(
            title="Complete Network Analysis: Core-Periphery Structure and Flexibility",
            height=1000,
            showlegend=True
        )
        
        # Update axes
        fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False, row=1, col=1)
        fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False, row=1, col=1)
        
        fig.update_xaxes(title="Persistence Score", row=2, col=1)
        fig.update_yaxes(title="Entity Rank", row=2, col=1)
        
        fig.update_xaxes(title="Core Entity", tickangle=45, row=2, col=2)
        fig.update_yaxes(title="Degree Centrality", row=2, col=2)
        
        # Save visualization
        fig.write_html(output_file)
        print(f"Complete network visualization saved to {output_file}")
        
        return fig, combined_G, persistence_scores
    
    def create_stability_flexibility_analysis(self, periods_data, output_file="stability_flexibility_analysis.html"):
        """Analyze and visualize network stability vs flexibility"""
        
        # Calculate entity appearance patterns
        entity_appearances = defaultdict(list)
        
        for period, G in periods_data.items():
            for node in G.nodes():
                entity_appearances[node].append(period)
        
        # Classify entities by stability pattern
        stable_core = []  # Appears in all periods
        emerging_actors = []  # Appears in later periods only
        crisis_specific = []  # Appears in specific crisis periods
        flexible_international = []  # International actors with varying presence
        
        total_periods = len(periods_data)
        
        for entity, periods in entity_appearances.items():
            period_count = len(periods)
            
            # Get entity category from any period it appears in
            category = 'domestic'  # default
            for period in periods:
                if entity in periods_data[period].nodes():
                    category = periods_data[period].nodes[entity].get('node_category', 'domestic')
                    break
            
            if period_count == total_periods:
                stable_core.append(entity)
            elif period_count == 1:
                if 'covid' in periods:
                    crisis_specific.append(entity)
                elif 'war' in periods:
                    crisis_specific.append(entity)
                else:
                    emerging_actors.append(entity)
            elif category == 'international':
                flexible_international.append(entity)
            else:
                emerging_actors.append(entity)
        
        # Create visualization
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                'Network Stability Patterns',
                'Core Stability Over Time',
                'Flexibility: New Actors by Period',
                'International Actor Flexibility'
            ],
            specs=[[{"type": "bar"}, {"type": "scatter"}],
                   [{"type": "bar"}, {"type": "scatter"}]]
        )
        
        # 1. Stability patterns overview
        stability_categories = ['Stable Core', 'Emerging Actors', 'Crisis-Specific', 'Flexible International']
        stability_counts = [len(stable_core), len(emerging_actors), len(crisis_specific), len(flexible_international)]
        
        fig.add_trace(
            go.Bar(x=stability_categories, y=stability_counts,
                  marker_color=['#e74c3c', '#3498db', '#f39c12', '#2ecc71'],
                  showlegend=False),
            row=1, col=1
        )
        
        # 2. Core stability over time
        periods = list(periods_data.keys())
        core_presence = []
        
        for period in periods:
            G = periods_data[period]
            core_count = sum(1 for node in G.nodes() 
                           if G.nodes[node].get('node_category') == 'core')
            core_presence.append(core_count)
        
        fig.add_trace(
            go.Scatter(x=periods, y=core_presence, mode='lines+markers',
                      line=dict(color='#e74c3c', width=3),
                      marker=dict(size=10),
                      showlegend=False),
            row=1, col=2
        )
        
        # 3. New actors by period
        new_actors_by_period = {}
        all_previous_actors = set()
        
        for period in periods:
            current_actors = set(periods_data[period].nodes())
            new_actors = current_actors - all_previous_actors
            new_actors_by_period[period] = len(new_actors)
            all_previous_actors.update(current_actors)
        
        fig.add_trace(
            go.Bar(x=list(new_actors_by_period.keys()), 
                  y=list(new_actors_by_period.values()),
                  marker_color='#3498db',
                  showlegend=False),
            row=2, col=1
        )
        
        # 4. International actor flexibility
        international_by_period = {}
        for period in periods:
            G = periods_data[period]
            intl_count = sum(1 for node in G.nodes() 
                           if G.nodes[node].get('node_category') == 'international')
            international_by_period[period] = intl_count
        
        fig.add_trace(
            go.Scatter(x=list(international_by_period.keys()), 
                      y=list(international_by_period.values()),
                      mode='lines+markers',
                      line=dict(color='#2ecc71', width=3),
                      marker=dict(size=10),
                      showlegend=False),
            row=2, col=2
        )
        
        fig.update_layout(
            title="Network Stability vs. Flexibility Analysis",
            height=800
        )
        
        fig.write_html(output_file)
        print(f"Stability-flexibility analysis saved to {output_file}")
        
        # Generate insights
        insights = {
            'stable_core': stable_core,
            'emerging_actors': emerging_actors,
            'crisis_specific': crisis_specific,
            'flexible_international': flexible_international,
            'core_stability_pattern': core_presence,
            'new_actors_pattern': new_actors_by_period,
            'international_flexibility': international_by_period
        }
        
        return fig, insights

def main():
    """Main execution function"""
    visualizer = ComprehensiveNetworkVisualizer()
    
    # Load networks with lower threshold to capture complete network
    periods_data = {}
    period_files = {
        'pre_crimea': 'pre_crimea.csv',
        'post_crimea': 'post_crimea.csv', 
        'covid': 'covid.csv',
        'war': 'war.csv'
    }
    
    print("Loading complete networks with lower threshold (min_edge_weight=10)...")
    for period_name, file_path in period_files.items():
        try:
            # Lower threshold to capture more of the network
            G = visualizer.create_network_from_csv(file_path, min_edge_weight=10)
            periods_data[period_name] = G
            print(f"✅ {period_name}: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        except Exception as e:
            print(f"❌ Error loading {period_name}: {e}")
            continue
    
    # Create comprehensive core-periphery visualization
    print("\nCreating complete network visualization...")
    core_periphery_fig, combined_network, persistence_scores = visualizer.create_core_periphery_visualization(
        periods_data, "complete_core_periphery_network.html"
    )
    
    # Create stability vs flexibility analysis
    print("\nCreating stability-flexibility analysis...")
    stability_fig, insights = visualizer.create_stability_flexibility_analysis(
        periods_data, "network_stability_flexibility.html"
    )
    
    # Print key insights
    print("\n" + "="*70)
    print("COMPLETE NETWORK ANALYSIS INSIGHTS:")
    print("="*70)
    
    print(f"\n📊 NETWORK SCALE:")
    print(f"Complete network: {combined_network.number_of_nodes()} entities, {combined_network.number_of_edges()} relationships")
    
    print(f"\n🎯 STABLE CORE ({len(insights['stable_core'])} entities):")
    for entity in insights['stable_core'][:10]:  # Top 10
        print(f"  • {entity}")
    
    print(f"\n🌐 FLEXIBLE INTERNATIONAL ({len(insights['flexible_international'])} entities):")
    for entity in insights['flexible_international'][:5]:  # Top 5
        print(f"  • {entity}")
    
    print(f"\n⚡ CRISIS-SPECIFIC ACTORS ({len(insights['crisis_specific'])} entities):")
    for entity in insights['crisis_specific'][:5]:  # Top 5
        print(f"  • {entity}")
    
    print("\n🎉 Complete network visualizations created!")
    print("Files:")
    print("• complete_core_periphery_network.html - Full network with core-periphery structure")
    print("• network_stability_flexibility.html - Stability vs flexibility analysis")

if __name__ == "__main__":
    main()
