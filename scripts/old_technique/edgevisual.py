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
        Calculate 3D positions for nodes using layout algorithms
        """
        print(f"\nCalculating 3D positions using {layout_type} layout...")
        
        if layout_type == 'spring':
            # Use spring layout in 3D for combined network
            pos_dict = nx.spring_layout(self.combined_network, dim=3, k=1, iterations=50)
        else:
            # Random 3D positions
            pos_dict = {node: [np.random.uniform(-1, 1) for _ in range(3)] 
                       for node in self.combined_network.nodes()}
        
        self.node_positions = pos_dict
        
        # Define temporal Z-axis positions and colors
        period_info = {
            'Pre-Crimea': {'z': -1.5, 'color': '#FF6B6B', 'name': 'Pre-Crimea (2010-2013)'},
            'Post-Crimea': {'z': -0.5, 'color': '#4ECDC4', 'name': 'Post-Crimea (2013-2019)'},
            'Covid': {'z': 0.5, 'color': '#45B7D1', 'name': 'Covid (2020-2022)'},
            'War': {'z': 1.5, 'color': '#96CEB4', 'name': 'War (2022-2025)'}
        }
        
        # Create temporal-specific positions for each period
        for period_name, G in self.networks.items():
            period_positions = {}
            for node in G.nodes():
                if node in pos_dict:
                    x, y, _ = pos_dict[node]
                    period_positions[node] = [x, y, period_info[period_name]['z']]
                else:
                    period_positions[node] = [0, 0, period_info[period_name]['z']]
            
            self.networks[period_name].graph['positions'] = period_positions
            self.networks[period_name].graph['color'] = period_info[period_name]['color']
            self.networks[period_name].graph['display_name'] = period_info[period_name]['name']
        
        print("3D positions calculated successfully!")
    
    def create_3d_temporal_visualization(self):
        """
        Create comprehensive 3D visualization with colored timeframes
        """
        print("\nCreating 3D temporal visualization...")
        
        fig = go.Figure()
        
        # Define period colors and info
        period_colors = {
            'Pre-Crimea': '#FF6B6B',
            'Post-Crimea': '#4ECDC4', 
            'Covid': '#45B7D1',
            'War': '#96CEB4'
        }
        
        # Add nodes and edges for each period
        for period_name, G in self.networks.items():
            positions = G.graph['positions']
            color = period_colors[period_name]
            
            # Extract node positions
            node_x = [positions[node][0] for node in G.nodes()]
            node_y = [positions[node][1] for node in G.nodes()]
            node_z = [positions[node][2] for node in G.nodes()]
            
            # Node information and sizes
            node_text = []
            node_sizes = []
            
            for node in G.nodes():
                occurrences = G.nodes[node]['occurrences']
                entity_type = G.nodes[node]['entity_type']
                text = f"<b>{node}</b><br>Period: {period_name}<br>Type: {entity_type}<br>Occurrences: {occurrences}"
                node_text.append(text)
                node_sizes.append(max(8, min(25, occurrences / 100)))
            
            # Add node trace
            fig.add_trace(go.Scatter3d(
                x=node_x, y=node_y, z=node_z,
                mode='markers',
                marker=dict(
                    size=node_sizes,
                    color=color,
                    opacity=0.8,
                    line=dict(width=1, color='black')
                ),
                text=node_text,
                hoverinfo='text',
                name=f'{period_name} Nodes',
                showlegend=True
            ))
            
            # Add edges for this period
            edge_x = []
            edge_y = []
            edge_z = []
            
            for edge in G.edges():
                if edge[0] in positions and edge[1] in positions:
                    x0, y0, z0 = positions[edge[0]]
                    x1, y1, z1 = positions[edge[1]]
                    edge_x.extend([x0, x1, None])
                    edge_y.extend([y0, y1, None])
                    edge_z.extend([z0, z1, None])
            
            # Add edge trace
            fig.add_trace(go.Scatter3d(
                x=edge_x, y=edge_y, z=edge_z,
                mode='lines',
                line=dict(width=2, color=color),
                opacity=0.5,
                hoverinfo='none',
                name=f'{period_name} Edges',
                showlegend=False
            ))
        
        # Update layout
        fig.update_layout(
            title={
                'text': "3D Temporal Network Analysis - Entity Co-occurrence Over Time",
                'x': 0.5,
                'font': {'size': 16, 'color': 'black'}
            },
            scene=dict(
                xaxis=dict(
                    title='Network Space X',
                    showgrid=True,
                    gridcolor='lightgray',
                    showticklabels=False
                ),
                yaxis=dict(
                    title='Network Space Y',
                    showgrid=True,
                    gridcolor='lightgray',
                    showticklabels=False
                ),
                zaxis=dict(
                    title='Time Period',
                    showgrid=True,
                    gridcolor='lightgray',
                    tickmode='array',
                    tickvals=[-1.5, -0.5, 0.5, 1.5],
                    ticktext=['Pre-Crimea<br>(2010-2013)', 'Post-Crimea<br>(2013-2019)', 
                             'Covid<br>(2020-2022)', 'War<br>(2022-2025)']
                ),
                camera=dict(
                    eye=dict(x=1.2, y=1.2, z=1.2)
                ),
                aspectmode='cube'
            ),
            width=1200,
            height=800,
            margin=dict(l=0, r=0, b=0, t=50),
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="black",
                borderwidth=1
            )
        )
        
        return fig
    
    def create_individual_period_visualizations(self):
        """
        Create individual 3D visualizations for each period
        """
        figures = {}
        
        for period_name, G in self.networks.items():
            positions = G.graph['positions']
            color = G.graph['color']
            
            # Extract node positions
            node_x = [positions[node][0] for node in G.nodes()]
            node_y = [positions[node][1] for node in G.nodes()]
            node_z = [positions[node][2] for node in G.nodes()]
            
            # Node information
            node_text = []
            node_sizes = []
            
            for node in G.nodes():
                occurrences = G.nodes[node]['occurrences']
                entity_type = G.nodes[node]['entity_type']
                text = f"<b>{node}</b><br>Type: {entity_type}<br>Occurrences: {occurrences}"
                node_text.append(text)
                node_sizes.append(max(8, min(25, occurrences / 100)))
            
            # Extract edge positions
            edge_x = []
            edge_y = []
            edge_z = []
            
            for edge in G.edges():
                x0, y0, z0 = positions[edge[0]]
                x1, y1, z1 = positions[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
                edge_z.extend([z0, z1, None])
            
            # Create figure
            fig = go.Figure()
            
            # Add edges
            fig.add_trace(go.Scatter3d(
                x=edge_x, y=edge_y, z=edge_z,
                mode='lines',
                line=dict(width=2, color='gray'),
                opacity=0.6,
                hoverinfo='none',
                showlegend=False
            ))
            
            # Add nodes
            fig.add_trace(go.Scatter3d(
                x=node_x, y=node_y, z=node_z,
                mode='markers',
                marker=dict(
                    size=node_sizes,
                    color=color,
                    opacity=0.8,
                    line=dict(width=1, color='black')
                ),
                text=node_text,
                hoverinfo='text',
                showlegend=False
            ))
            
            # Update layout
            fig.update_layout(
                title={
                    'text': f"3D Network - {G.graph['display_name']}",
                    'x': 0.5,
                    'font': {'size': 16}
                },
                scene=dict(
                    xaxis=dict(showgrid=True, showticklabels=False),
                    yaxis=dict(showgrid=True, showticklabels=False),
                    zaxis=dict(showgrid=True, showticklabels=False),
                    camera=dict(eye=dict(x=1.2, y=1.2, z=1.2))
                ),
                width=800,
                height=600,
                margin=dict(l=0, r=0, b=0, t=50)
            )
            
            figures[period_name] = fig
        
        return figures
    
    def create_network_metrics_plot(self):
        """
        Create network evolution metrics plot
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
            subplot_titles=('Network Size', 'Network Density', 'Average Clustering', 'Connected Components'),
            specs=[[{"secondary_y": True}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Network size
        fig.add_trace(
            go.Scatter(x=periods, y=metrics['nodes'], name='Nodes', line=dict(color='blue')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=periods, y=metrics['edges'], name='Edges', line=dict(color='red')),
            row=1, col=1, secondary_y=True
        )
        
        # Density
        fig.add_trace(
            go.Scatter(x=periods, y=metrics['density'], name='Density', line=dict(color='green')),
            row=1, col=2
        )
        
        # Clustering
        fig.add_trace(
            go.Scatter(x=periods, y=metrics['avg_clustering'], name='Clustering', line=dict(color='orange')),
            row=2, col=1
        )
        
        # Components
        components = [nx.number_connected_components(G) for G in self.networks.values()]
        fig.add_trace(
            go.Scatter(x=periods, y=components, name='Components', line=dict(color='purple')),
            row=2, col=2
        )
        
        fig.update_layout(height=600, showlegend=True, title_text="Network Evolution Over Time")
        return fig

def main():
    """
    Main execution function
    """
    # Load datasets (adjust filenames as needed)
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
    
    # Calculate 3D positions
    analyzer.calculate_3d_positions(layout_type='spring')
    
    print("\n=== GENERATING VISUALIZATIONS ===")
    
    # Create main 3D temporal visualization and save to HTML
    main_fig = analyzer.create_3d_temporal_visualization()
    main_fig.write_html('temporal_network_3d_complete.html')
    print("Main 3D visualization saved to: temporal_network_3d_complete.html")
    
    # Create individual period visualizations and save to HTML
    individual_figs = analyzer.create_individual_period_visualizations()
    for period_name, fig in individual_figs.items():
        filename = f'network_3d_{period_name.lower().replace("-", "_")}.html'
        fig.write_html(filename)
        print(f"Individual {period_name} visualization saved to: {filename}")
    
    # Create network metrics plot and save to HTML
    metrics_fig = analyzer.create_network_metrics_plot()
    metrics_fig.write_html('network_evolution_metrics.html')
    print("Network metrics plot saved to: network_evolution_metrics.html")
    
    print("\n=== VISUALIZATION COMPLETE ===")
    print("\nGenerated HTML files:")
    print("- temporal_network_3d_complete.html (Main 3D visualization)")
    print("- network_3d_pre_crimea.html (Pre-Crimea period)")
    print("- network_3d_post_crimea.html (Post-Crimea period)")
    print("- network_3d_covid.html (Covid period)")
    print("- network_3d_war.html (War period)")
    print("- network_evolution_metrics.html (Network metrics)")
    print("\nOpen these HTML files in your browser to view the interactive 3D visualizations!")
    
    return analyzer

# Execute the analysis
if __name__ == "__main__":
    analyzer = main()
