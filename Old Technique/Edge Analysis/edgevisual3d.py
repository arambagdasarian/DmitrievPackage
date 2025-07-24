import pandas as pd
import networkx as nx
import numpy as np
from itertools import combinations
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio
import warnings
warnings.filterwarnings('ignore')

# Set plotly renderer to browser
pio.renderers.default = "browser"

class TemporalNetworkAnalyzer:
    def __init__(self, datasets):
        """
        Initialize with datasets for each time period
        """
        self.datasets = datasets
        self.networks = {}
        self.edge_data = {}
        self.node_positions = {}
        self.combined_network = None
        
    def create_co_occurrence_edges(self, df, period_name, min_weight=2):
        """
        Create co-occurrence edges based on shared Article_IDs
        """
        print(f"Creating co-occurrence edges for {period_name}...")
        
        # Group entities by Article_ID
        article_groups = df.groupby('Article_ID')['Entity'].apply(list).reset_index()
        
        # Generate co-occurrence pairs
        edges = []
        edge_articles = defaultdict(list)
        
        for _, row in article_groups.iterrows():
            article_id = row['Article_ID']
            entities = row['Entity']
            
            if len(entities) > 1:
                for entity1, entity2 in combinations(entities, 2):
                    if entity1 != entity2:
                        edge = tuple(sorted([entity1, entity2]))
                        edges.append(edge)
                        edge_articles[edge].append(article_id)
        
        # Count co-occurrences and filter by minimum weight
        edge_counts = Counter(edges)
        
        # Create detailed edge data
        edge_list = []
        for (entity1, entity2), weight in edge_counts.items():
            if weight >= min_weight:
                edge_list.append({
                    'source': entity1,
                    'target': entity2,
                    'weight': weight,
                    'period': period_name,
                    'articles': edge_articles[(entity1, entity2)]
                })
        
        print(f"  Generated {len(edge_list)} edges (min_weight={min_weight})")
        return edge_list
    
    def build_temporal_networks(self, min_weight=2):
        """
        Build NetworkX graphs for each time period
        """
        print("\nBuilding temporal networks...")
        
        for period_name, df in self.datasets.items():
            # Create edges
            edge_list = self.create_co_occurrence_edges(df, period_name, min_weight)
            self.edge_data[period_name] = edge_list
            
            # Build NetworkX graph
            G = nx.Graph()
            for edge in edge_list:
                G.add_edge(edge['source'], edge['target'], 
                          weight=edge['weight'], 
                          period=period_name,
                          articles=edge['articles'])
            
            # Add node attributes
            node_occurrences = df.groupby('Entity')['Occurrences'].first().to_dict()
            entity_types = df.groupby('Entity')['Entity_Type'].first().to_dict()
            
            for node in G.nodes():
                G.nodes[node]['occurrences'] = node_occurrences.get(node, 0)
                G.nodes[node]['entity_type'] = entity_types.get(node, 'Unknown')
                G.nodes[node]['period'] = period_name
            
            self.networks[period_name] = G
            print(f"  {period_name}: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    def create_combined_temporal_network(self):
        """
        Create a combined network with temporal information
        """
        print("\nCreating combined temporal network...")
        
        self.combined_network = nx.Graph()
        
        # Add all edges from all periods
        for period_name, G in self.networks.items():
            for u, v, data in G.edges(data=True):
                if self.combined_network.has_edge(u, v):
                    self.combined_network[u][v]['periods'].append(period_name)
                    self.combined_network[u][v]['total_weight'] += data['weight']
                else:
                    self.combined_network.add_edge(u, v, 
                                                  weight=data['weight'],
                                                  total_weight=data['weight'],
                                                  periods=[period_name])
        
        # Add node attributes
        all_nodes = set()
        for G in self.networks.values():
            all_nodes.update(G.nodes())
        
        for node in all_nodes:
            periods_present = []
            total_occurrences = 0
            entity_type = None
            
            for period_name, G in self.networks.items():
                if node in G.nodes():
                    periods_present.append(period_name)
                    total_occurrences += G.nodes[node]['occurrences']
                    if entity_type is None:
                        entity_type = G.nodes[node]['entity_type']
            
            self.combined_network.nodes[node]['periods'] = periods_present
            self.combined_network.nodes[node]['total_occurrences'] = total_occurrences
            self.combined_network.nodes[node]['entity_type'] = entity_type
            self.combined_network.nodes[node]['period_count'] = len(periods_present)
        
        print(f"Combined network: {self.combined_network.number_of_nodes()} nodes, {self.combined_network.number_of_edges()} edges")
    
    def calculate_3d_positions(self, layout_type='spring'):
        """
        Calculate 3D positions with PROPER normalization for centrality-based Z positioning
        """
        print(f"\nCalculating 3D positions using {layout_type} layout...")
        
        # Calculate base layout for combined network
        if layout_type == 'spring':
            pos_dict = nx.spring_layout(self.combined_network, dim=2, k=0.8, iterations=100)
        else:
            pos_dict = {node: [np.random.uniform(-1, 1) for _ in range(2)] 
                       for node in self.combined_network.nodes()}
        
        self.node_positions = pos_dict
        
        # Define temporal base Z positions and colors
        period_info = {
            'Pre-Crimea': {'base_z': -4.0, 'color': '#FF6B6B', 'name': 'Pre-Crimea (2010-2013)'},
            'Post-Crimea': {'base_z': -1.5, 'color': '#4ECDC4', 'name': 'Post-Crimea (2013-2019)'},
            'Covid': {'base_z': 1.5, 'color': '#45B7D1', 'name': 'Covid (2020-2022)'},
            'War': {'base_z': 4.0, 'color': '#96CEB4', 'name': 'War (2022-2025)'}
        }
        
        # Create temporal-specific positions with PROPERLY NORMALIZED centrality-based Z elevation
        for period_name, G in self.networks.items():
            period_positions = {}
            
            # Calculate centrality metrics (all are already normalized to 0-1 by NetworkX)
            degree_centrality = nx.degree_centrality(G)  # Already normalized 0-1
            betweenness_centrality = nx.betweenness_centrality(G)  # Already normalized 0-1
            edge_count = dict(G.degree())  # Raw edge count - needs normalization
            
            # PROPER NORMALIZATION: Scale edge_count to 0-1 range
            max_edges = max(edge_count.values()) if edge_count else 1
            min_edges = min(edge_count.values()) if edge_count else 0
            edge_range = max_edges - min_edges if max_edges > min_edges else 1
            
            base_z = period_info[period_name]['base_z']
            
            for node in G.nodes():
                if node in pos_dict:
                    x, y = pos_dict[node]
                    
                    # All metrics now properly normalized to 0-1
                    degree_score = degree_centrality.get(node, 0)  # Already 0-1
                    betweenness_score = betweenness_centrality.get(node, 0)  # Already 0-1
                    edge_score = (edge_count.get(node, 0) - min_edges) / edge_range  # Now 0-1
                    
                    # FIXED: Composite centrality score with proper weighting
                    centrality_score = (0.4 * degree_score + 0.3 * betweenness_score + 0.3 * edge_score)
                    
                    # Apply Z elevation with better scaling
                    z_elevation = centrality_score * 3.0  # More dramatic height differences
                    final_z = base_z + z_elevation
                    
                    period_positions[node] = [x, y, final_z]
                else:
                    period_positions[node] = [0, 0, base_z]
            
            self.networks[period_name].graph['positions'] = period_positions
            self.networks[period_name].graph['color'] = period_info[period_name]['color']
            self.networks[period_name].graph['display_name'] = period_info[period_name]['name']
        
        print("3D positions with proper normalization calculated successfully!")
    
    def create_3d_temporal_visualization(self):
        """
        Create enhanced 3D visualization optimized for 800+ nodes
        """
        print("\nCreating enhanced 3D temporal visualization...")
        
        fig = go.Figure()
        
        # Enhanced period colors for better visibility
        period_colors = {
            'Pre-Crimea': '#FF4444',      # Bright red
            'Post-Crimea': '#00CED1',     # Dark turquoise
            'Covid': '#1E90FF',           # Dodger blue
            'War': '#32CD32'              # Lime green
        }
        
        # Add nodes and edges for each period with enhanced visibility
        for period_name, G in self.networks.items():
            positions = G.graph['positions']
            color = period_colors[period_name]
            
            # Extract node positions
            node_x = [positions[node][0] for node in G.nodes()]
            node_y = [positions[node][1] for node in G.nodes()]
            node_z = [positions[node][2] for node in G.nodes()]
            
            # Enhanced node information and sizes
            node_text = []
            node_sizes = []
            node_colors = []
            
            # Calculate centrality metrics for hover info
            degree_centrality = nx.degree_centrality(G)
            betweenness_centrality = nx.betweenness_centrality(G)
            edge_count = dict(G.degree())
            
            # Color mapping for entity types
            entity_type_colors = {
                'PER': '#FF6B6B',    # Red for persons
                'ORG': '#4ECDC4',    # Teal for organizations
                'LOC': '#45B7D1',    # Blue for locations
                'Unknown': '#96CEB4' # Gray for unknown
            }
            
            for node in G.nodes():
                occurrences = G.nodes[node]['occurrences']
                entity_type = G.nodes[node]['entity_type']
                degree_cent = degree_centrality.get(node, 0)
                betweenness_cent = betweenness_centrality.get(node, 0)
                edges = edge_count.get(node, 0)
                
                # Enhanced hover text
                text = f"<b>{node}</b><br>Period: {period_name}<br>Type: {entity_type}<br>Occurrences: {occurrences}<br>Degree Centrality: {degree_cent:.3f}<br>Betweenness Centrality: {betweenness_cent:.3f}<br>Edge Count: {edges}<br>Composite Score: {0.4*degree_cent + 0.3*betweenness_cent + 0.3*(edges/max(edge_count.values())):.3f}"
                node_text.append(text)
                
                # Enhanced node sizing for better visibility
                node_sizes.append(max(15, min(40, occurrences / 30)))
                
                # Mix period color with entity type color
                base_color = entity_type_colors.get(entity_type, '#96CEB4')
                node_colors.append(base_color)
            
            # Enhanced node trace with better styling
            fig.add_trace(go.Scatter3d(
                x=node_x, y=node_y, z=node_z,
                mode='markers',
                marker=dict(
                    size=node_sizes,
                    color=node_colors,
                    opacity=0.85,
                    line=dict(width=2, color='black'),
                    symbol='circle'
                ),
                text=node_text,
                hoverinfo='text',
                hovertemplate='%{text}<extra></extra>',
                name=f'{period_name} Nodes',
                showlegend=True
            ))
            
            # Simplified edge visualization for better performance with 800+ nodes
            # Only show edges for high-centrality nodes to reduce clutter
            high_centrality_nodes = [node for node in G.nodes() 
                                   if degree_centrality.get(node, 0) > 0.1 or 
                                      betweenness_centrality.get(node, 0) > 0.1]
            
            edge_x = []
            edge_y = []
            edge_z = []
            
            for edge in G.edges():
                if edge[0] in high_centrality_nodes or edge[1] in high_centrality_nodes:
                    if edge[0] in positions and edge[1] in positions:
                        x0, y0, z0 = positions[edge[0]]
                        x1, y1, z1 = positions[edge[1]]
                        edge_x.extend([x0, x1, None])
                        edge_y.extend([y0, y1, None])
                        edge_z.extend([z0, z1, None])
            
            # Add edge trace with reduced opacity
            fig.add_trace(go.Scatter3d(
                x=edge_x, y=edge_y, z=edge_z,
                mode='lines',
                line=dict(width=0.5, color=color),
                opacity=0.2,
                hoverinfo='none',
                name=f'{period_name} Edges',
                showlegend=False
            ))
        
        # Enhanced layout with better scaling for 800+ nodes
        fig.update_layout(
            title={
                'text': "3D Temporal Network Analysis - Entity Co-occurrence Over Time<br><sub>Node height = Composite centrality (0.4×degree + 0.3×betweenness + 0.3×normalized_edges)</sub>",
                'x': 0.5,
                'font': {'size': 22, 'color': 'black', 'family': 'Arial, sans-serif'}
            },
            scene=dict(
                xaxis=dict(
                    title='Network Space X',
                    showgrid=True,
                    gridcolor='lightgray',
                    gridwidth=1,
                    showticklabels=False,
                    backgroundcolor='rgba(248,248,248,0.8)',
                    showbackground=True
                ),
                yaxis=dict(
                    title='Network Space Y',
                    showgrid=True,
                    gridcolor='lightgray',
                    gridwidth=1,
                    showticklabels=False,
                    backgroundcolor='rgba(248,248,248,0.8)',
                    showbackground=True
                ),
                zaxis=dict(
                    title='Time Period + Network Centrality',
                    showgrid=True,
                    gridcolor='lightgray',
                    gridwidth=1,
                    tickmode='array',
                    tickvals=[-4, -1.5, 1.5, 4],
                    ticktext=['Pre-Crimea<br>(2010-2013)', 'Post-Crimea<br>(2013-2019)', 
                             'Covid<br>(2020-2022)', 'War<br>(2022-2025)'],
                    backgroundcolor='rgba(248,248,248,0.8)',
                    showbackground=True
                ),
                camera=dict(
                    eye=dict(x=1.8, y=1.8, z=1.8),
                    center=dict(x=0, y=0, z=0)
                ),
                aspectmode='cube',
                bgcolor='rgba(255,255,255,0.9)'
            ),
            # Full viewport sizing
            autosize=True,
            width=None,
            height=None,
            margin=dict(l=0, r=0, b=0, t=100, pad=0),
            legend=dict(
                yanchor="top",
                y=0.98,
                xanchor="left",
                x=0.02,
                bgcolor="rgba(255,255,255,0.95)",
                bordercolor="black",
                borderwidth=2,
                font=dict(size=14, family='Arial, sans-serif')
            ),
            paper_bgcolor='white',
            plot_bgcolor='white',
            font=dict(family='Arial, sans-serif')
        )
        
        return fig
    
    def create_individual_period_visualizations(self):
        """
        Create individual 3D visualizations for each period with enhanced styling
        """
        figures = {}
        
        for period_name, G in self.networks.items():
            positions = G.graph['positions']
            color = G.graph['color']
            
            # Extract node positions
            node_x = [positions[node][0] for node in G.nodes()]
            node_y = [positions[node][1] for node in G.nodes()]
            node_z = [positions[node][2] for node in G.nodes()]
            
            # Enhanced node information
            node_text = []
            node_sizes = []
            node_colors = []
            
            # Calculate centrality metrics
            degree_centrality = nx.degree_centrality(G)
            betweenness_centrality = nx.betweenness_centrality(G)
            edge_count = dict(G.degree())
            
            # Color mapping for entity types
            entity_type_colors = {
                'PER': '#FF6B6B',
                'ORG': '#4ECDC4',
                'LOC': '#45B7D1',
                'Unknown': '#96CEB4'
            }
            
            for node in G.nodes():
                occurrences = G.nodes[node]['occurrences']
                entity_type = G.nodes[node]['entity_type']
                degree_cent = degree_centrality.get(node, 0)
                betweenness_cent = betweenness_centrality.get(node, 0)
                edges = edge_count.get(node, 0)
                
                text = f"<b>{node}</b><br>Type: {entity_type}<br>Occurrences: {occurrences}<br>Degree Centrality: {degree_cent:.3f}<br>Betweenness Centrality: {betweenness_cent:.3f}<br>Edge Count: {edges}<br>Composite Score: {0.4*degree_cent + 0.3*betweenness_cent + 0.3*(edges/max(edge_count.values())):.3f}"
                node_text.append(text)
                node_sizes.append(max(15, min(40, occurrences / 30)))
                node_colors.append(entity_type_colors.get(entity_type, '#96CEB4'))
            
            # Create figure
            fig = go.Figure()
            
            # Add nodes with enhanced styling
            fig.add_trace(go.Scatter3d(
                x=node_x, y=node_y, z=node_z,
                mode='markers',
                marker=dict(
                    size=node_sizes,
                    color=node_colors,
                    opacity=0.85,
                    line=dict(width=2, color='black'),
                    symbol='circle'
                ),
                text=node_text,
                hoverinfo='text',
                hovertemplate='%{text}<extra></extra>',
                showlegend=False
            ))
            
            # Enhanced layout
            fig.update_layout(
                title={
                    'text': f"3D Network - {G.graph['display_name']}<br><sub>Node height represents composite centrality score</sub>",
                    'x': 0.5,
                    'font': {'size': 20, 'family': 'Arial, sans-serif'}
                },
                scene=dict(
                    xaxis=dict(showgrid=True, showticklabels=False, backgroundcolor='rgba(248,248,248,0.8)', showbackground=True),
                    yaxis=dict(showgrid=True, showticklabels=False, backgroundcolor='rgba(248,248,248,0.8)', showbackground=True),
                    zaxis=dict(showgrid=True, showticklabels=False, backgroundcolor='rgba(248,248,248,0.8)', showbackground=True),
                    camera=dict(eye=dict(x=1.8, y=1.8, z=1.8)),
                    aspectmode='cube',
                    bgcolor='rgba(255,255,255,0.9)'
                ),
                autosize=True,
                width=None,
                height=None,
                margin=dict(l=0, r=0, b=0, t=100, pad=0),
                paper_bgcolor='white',
                plot_bgcolor='white',
                font=dict(family='Arial, sans-serif')
            )
            
            figures[period_name] = fig
        
        return figures
    
    def create_network_metrics_plot(self):
        """
        Create network evolution metrics plot with enhanced styling
        """
        periods = list(self.networks.keys())
        metrics = {
            'nodes': [G.number_of_nodes() for G in self.networks.values()],
            'edges': [G.number_of_edges() for G in self.networks.values()],
            'density': [nx.density(G) for G in self.networks.values()],
            'avg_clustering': [nx.average_clustering(G) for G in self.networks.values()]
        }
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Network Size Evolution', 'Network Density Evolution', 
                          'Average Clustering Evolution', 'Connected Components Evolution'),
            specs=[[{"secondary_y": True}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Network size
        fig.add_trace(
            go.Scatter(x=periods, y=metrics['nodes'], name='Nodes', 
                      line=dict(color='#1f77b4', width=3), marker=dict(size=8)),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=periods, y=metrics['edges'], name='Edges', 
                      line=dict(color='#ff7f0e', width=3), marker=dict(size=8)),
            row=1, col=1, secondary_y=True
        )
        
        # Other metrics with enhanced styling
        fig.add_trace(
            go.Scatter(x=periods, y=metrics['density'], name='Density', 
                      line=dict(color='#2ca02c', width=3), marker=dict(size=8)),
            row=1, col=2
        )
        
        fig.add_trace(
            go.Scatter(x=periods, y=metrics['avg_clustering'], name='Clustering', 
                      line=dict(color='#d62728', width=3), marker=dict(size=8)),
            row=2, col=1
        )
        
        components = [nx.number_connected_components(G) for G in self.networks.values()]
        fig.add_trace(
            go.Scatter(x=periods, y=components, name='Components', 
                      line=dict(color='#9467bd', width=3), marker=dict(size=8)),
            row=2, col=2
        )
        
        # Enhanced layout
        fig.update_layout(
            autosize=True,
            width=None,
            height=None,
            showlegend=True, 
            title_text="Network Evolution Metrics Over Time",
            title_font_size=22,
            title_font_family='Arial, sans-serif',
            margin=dict(l=20, r=20, b=20, t=100, pad=4),
            font=dict(family='Arial, sans-serif', size=12)
        )
        
        return fig

def main():
    """
    Main execution function
    """
    # Load datasets
    datasets = {
        'Pre-Crimea': pd.read_csv('matched_entities_pre_crimea_cleaned.csv'),
        'Post-Crimea': pd.read_csv('matched_entities_post_crimea_cleaned.csv'),
        'Covid': pd.read_csv('matched_entities_covid_cleaned.csv'),
        'War': pd.read_csv('matched_entities_war_cleaned.csv')
    }
    
    print("=== TEMPORAL NETWORK ANALYSIS ===")
    for name, df in datasets.items():
        print(f"{name}: {len(df):,} rows, {df['Entity'].nunique():,} unique entities")
    
    # Initialize analyzer
    analyzer = TemporalNetworkAnalyzer(datasets)
    
    # Build temporal networks
    analyzer.build_temporal_networks(min_weight=2)
    
    # Create combined network
    analyzer.create_combined_temporal_network()
    
    # Calculate 3D positions with PROPER normalization
    analyzer.calculate_3d_positions(layout_type='spring')
    
    print("\n=== GENERATING ENHANCED VISUALIZATIONS ===")
    
    # Create main 3D temporal visualization
    main_fig = analyzer.create_3d_temporal_visualization()
    main_fig.write_html('temporal_network_3d_enhanced.html')
    print("Enhanced 3D visualization saved to: temporal_network_3d_enhanced.html")
    
    # Create individual period visualizations
    individual_figs = analyzer.create_individual_period_visualizations()
    for period_name, fig in individual_figs.items():
        filename = f'network_3d_enhanced_{period_name.lower().replace("-", "_")}.html'
        fig.write_html(filename)
        print(f"Enhanced {period_name} visualization saved to: {filename}")
    
    # Create network metrics plot
    metrics_fig = analyzer.create_network_metrics_plot()
    metrics_fig.write_html('network_evolution_metrics_enhanced.html')
    print("Enhanced metrics plot saved to: network_evolution_metrics_enhanced.html")
    
    print("\n=== VISUALIZATION COMPLETE ===")
    print("\nKey improvements:")
    print("✓ FIXED: Proper normalization of centrality metrics (all 0-1 scale)")
    print("✓ Enhanced node visibility for 800+ nodes")
    print("✓ Improved color scheme and styling")
    print("✓ Better hover information with composite scores")
    print("✓ Optimized edge display for performance")
    print("✓ Enhanced typography and layout")
    print("\nFormula: Composite Score = 0.4×degree + 0.3×betweenness + 0.3×normalized_edges")
    
    return analyzer

# Execute the analysis
if __name__ == "__main__":
    analyzer = main()
