import pandas as pd
import networkx as nx
import numpy as np
import json
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
        Calculate 3D positions with ENHANCED node spacing for better visibility
        """
        print(f"\nCalculating 3D positions using {layout_type} layout with enhanced spacing...")
        
        # Enhanced spring layout parameters for better node spacing
        if layout_type == 'spring':
            n_nodes = len(self.combined_network.nodes())
            k_value = max(0.3, 1/np.sqrt(n_nodes))
            
            pos_dict = nx.spring_layout(
                self.combined_network, 
                dim=2, 
                k=k_value,
                iterations=200,
                scale=5.0  # Increased scale for better spread
            )
        else:
            pos_dict = {node: [np.random.uniform(-5, 5) for _ in range(2)] 
                       for node in self.combined_network.nodes()}
        
        self.node_positions = pos_dict
        
        # Enhanced temporal Z positions for better separation
        period_info = {
            'Pre-Crimea': {'base_z': -8.0, 'color': '#FF4444', 'name': 'Pre-Crimea (2010-2013)'},
            'Post-Crimea': {'base_z': -2.5, 'color': '#00CED1', 'name': 'Post-Crimea (2013-2019)'},
            'Covid': {'base_z': 2.5, 'color': '#1E90FF', 'name': 'Covid (2020-2022)'},
            'War': {'base_z': 8.0, 'color': '#32CD32', 'name': 'War (2022-2025)'}
        }
        
        # Create temporal-specific positions with enhanced spacing
        for period_name, G in self.networks.items():
            period_positions = {}
            
            # Calculate centrality metrics
            degree_centrality = nx.degree_centrality(G)
            betweenness_centrality = nx.betweenness_centrality(G)
            edge_count = dict(G.degree())
            
            # Proper normalization
            max_edges = max(edge_count.values()) if edge_count else 1
            min_edges = min(edge_count.values()) if edge_count else 0
            edge_range = max_edges - min_edges if max_edges > min_edges else 1
            
            base_z = period_info[period_name]['base_z']
            
            for node in G.nodes():
                if node in pos_dict:
                    x, y = pos_dict[node]
                    
                    # Apply additional spacing multiplier
                    x *= 2.0  # Increased X spacing
                    y *= 2.0  # Increased Y spacing
                    
                    # Normalized centrality scores
                    degree_score = degree_centrality.get(node, 0)
                    betweenness_score = betweenness_centrality.get(node, 0)
                    edge_score = (edge_count.get(node, 0) - min_edges) / edge_range
                    
                    # Composite centrality score
                    centrality_score = (0.4 * degree_score + 0.3 * betweenness_score + 0.3 * edge_score)
                    
                    # Enhanced Z elevation
                    z_elevation = centrality_score * 5.0
                    final_z = base_z + z_elevation
                    
                    period_positions[node] = [x, y, final_z]
                else:
                    period_positions[node] = [0, 0, base_z]
            
            self.networks[period_name].graph['positions'] = period_positions
            self.networks[period_name].graph['color'] = period_info[period_name]['color']
            self.networks[period_name].graph['display_name'] = period_info[period_name]['name']
        
        print("Enhanced 3D positions with improved spacing calculated successfully!")
    
    def create_3d_temporal_visualization(self):
        """
        Create visualization with embedded data for GitHub Pages
        """
        print("\nCreating enhanced 3D temporal visualization with embedded data...")
        
        fig = go.Figure()
        
        # Enhanced period colors
        period_colors = {
            'Pre-Crimea': '#FF4444',
            'Post-Crimea': '#00CED1',
            'Covid': '#1E90FF',
            'War': '#32CD32'
        }
        
        # Embed data directly in HTML
        embedded_data = {
            'nodes': [],
            'edges': [],
            'periods': list(self.networks.keys()),
            'period_colors': period_colors
        }
        
        # Add nodes and edges for each period
        for period_name, G in self.networks.items():
            positions = G.graph['positions']
            color = period_colors[period_name]
            
            # Extract node positions
            node_x = [positions[node][0] for node in G.nodes()]
            node_y = [positions[node][1] for node in G.nodes()]
            node_z = [positions[node][2] for node in G.nodes()]
            
            # Node information and SMALLER sizes
            node_text = []
            node_sizes = []
            
            # Calculate centrality metrics
            degree_centrality = nx.degree_centrality(G)
            betweenness_centrality = nx.betweenness_centrality(G)
            edge_count = dict(G.degree())
            
            for node in G.nodes():
                occurrences = G.nodes[node]['occurrences']
                entity_type = G.nodes[node]['entity_type']
                degree_cent = degree_centrality.get(node, 0)
                betweenness_cent = betweenness_centrality.get(node, 0)
                edges = edge_count.get(node, 0)
                
                # Extract node data for embedding
                embedded_data['nodes'].append({
                    'id': node,
                    'period': period_name,
                    'x': positions[node][0],
                    'y': positions[node][1], 
                    'z': positions[node][2],
                    'occurrences': occurrences,
                    'entity_type': entity_type,
                    'degree_centrality': degree_cent,
                    'betweenness_centrality': betweenness_cent,
                    'edge_count': edges,
                    'color': color
                })
                
                text = f"<b>{node}</b><br>Period: {period_name}<br>Type: {entity_type}<br>Occurrences: {occurrences}<br>Degree Centrality: {degree_cent:.3f}<br>Betweenness Centrality: {betweenness_cent:.3f}<br>Edge Count: {edges}<br>Composite Score: {0.4*degree_cent + 0.3*betweenness_cent + 0.3*(edges/max(edge_count.values()) if edge_count.values() else 1):.3f}"
                node_text.append(text)
                
                # SMALLER node sizes
                node_sizes.append(max(4, min(15, occurrences / 100)))
            
            # Extract edge data for embedding
            for edge in G.edges():
                embedded_data['edges'].append({
                    'source': edge[0],
                    'target': edge[1],
                    'period': period_name,
                    'weight': G.edges[edge]['weight'],
                    'color': color
                })
            
            # Node trace
            node_trace = go.Scatter3d(
                x=node_x, y=node_y, z=node_z,
                mode='markers',
                marker=dict(
                    size=node_sizes,
                    color=color,
                    opacity=0.8,
                    line=dict(width=0.5, color='black'),
                    symbol='circle'
                ),
                text=node_text,
                hoverinfo='text',
                hovertemplate='%{text}<extra></extra>',
                name=f'{period_name} Nodes',
                showlegend=True,
                visible=True
            )
            fig.add_trace(node_trace)
            
            # ALL edges for connection line visibility
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
            
            # Edge trace
            edge_trace = go.Scatter3d(
                x=edge_x, y=edge_y, z=edge_z,
                mode='lines',
                line=dict(width=1, color=color),
                opacity=0.3,
                hoverinfo='none',
                name=f'{period_name} Edges',
                showlegend=False,
                visible=False  # Start with edges hidden
            )
            fig.add_trace(edge_trace)
        
        # Enhanced interactive buttons with connection line controls
        updatemenus = [
            dict(
                type="buttons",
                direction="left",
                buttons=list([
                    dict(
                        label="Show All Nodes",
                        method="update",
                        args=[{"visible": [True if i % 2 == 0 else False for i in range(len(fig.data))]}]
                    ),
                    dict(
                        label="Show All + Connections",
                        method="update",
                        args=[{"visible": [True] * len(fig.data)}]
                    ),
                    dict(
                        label="Pre-Crimea Only",
                        method="update", 
                        args=[{"visible": [i == 0 for i in range(len(fig.data))]}]
                    ),
                    dict(
                        label="Pre-Crimea + Connections",
                        method="update",
                        args=[{"visible": [i < 2 for i in range(len(fig.data))]}]
                    ),
                    dict(
                        label="Post-Crimea Only",
                        method="update",
                        args=[{"visible": [i == 2 for i in range(len(fig.data))]}]
                    ),
                    dict(
                        label="Post-Crimea + Connections",
                        method="update",
                        args=[{"visible": [2 <= i < 4 for i in range(len(fig.data))]}]
                    ),
                    dict(
                        label="Covid Only",
                        method="update",
                        args=[{"visible": [i == 4 for i in range(len(fig.data))]}]
                    ),
                    dict(
                        label="Covid + Connections",
                        method="update",
                        args=[{"visible": [4 <= i < 6 for i in range(len(fig.data))]}]
                    ),
                    dict(
                        label="War Only",
                        method="update",
                        args=[{"visible": [i == 6 for i in range(len(fig.data))]}]
                    ),
                    dict(
                        label="War + Connections",
                        method="update",
                        args=[{"visible": [6 <= i < 8 for i in range(len(fig.data))]}]
                    )
                ]),
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.01,
                xanchor="left",
                y=1.02,
                yanchor="top"
            )
        ]
        
        # Full window layout
        fig.update_layout(
            title={
                'text': "3D Temporal Network Analysis - GitHub Pages<br><sub>Self-contained with embedded data • Connection line controls • Node height = Composite centrality</sub>",
                'x': 0.5,
                'font': {'size': 18, 'color': 'black', 'family': 'Arial, sans-serif'}
            },
            updatemenus=updatemenus,
            scene=dict(
                xaxis=dict(
                    title='Network Space X',
                    showgrid=True,
                    gridcolor='lightgray',
                    gridwidth=1,
                    showticklabels=False,
                    backgroundcolor='rgba(248,248,248,0.8)',
                    showbackground=True,
                    range=[-10, 10]
                ),
                yaxis=dict(
                    title='Network Space Y',
                    showgrid=True,
                    gridcolor='lightgray',
                    gridwidth=1,
                    showticklabels=False,
                    backgroundcolor='rgba(248,248,248,0.8)',
                    showbackground=True,
                    range=[-10, 10]
                ),
                zaxis=dict(
                    title='Time Period + Network Centrality',
                    showgrid=True,
                    gridcolor='lightgray',
                    gridwidth=1,
                    tickmode='array',
                    tickvals=[-8, -2.5, 2.5, 8],
                    ticktext=['Pre-Crimea<br>(2010-2013)', 'Post-Crimea<br>(2013-2019)', 
                             'Covid<br>(2020-2022)', 'War<br>(2022-2025)'],
                    backgroundcolor='rgba(248,248,248,0.8)',
                    showbackground=True,
                    range=[-12, 12]
                ),
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5),
                    center=dict(x=0, y=0, z=0)
                ),
                aspectmode='cube',
                bgcolor='rgba(255,255,255,0.9)'
            ),
            # Full window expansion
            autosize=True,
            width=None,
            height=None,
            margin=dict(l=0, r=0, b=0, t=140, pad=0),
            legend=dict(
                yanchor="top",
                y=0.92,
                xanchor="left",
                x=0.02,
                bgcolor="rgba(255,255,255,0.95)",
                bordercolor="black",
                borderwidth=1,
                font=dict(size=10, family='Arial, sans-serif')
            ),
            paper_bgcolor='white',
            plot_bgcolor='white',
            font=dict(family='Arial, sans-serif')
        )
        
        # Add embedded data as JavaScript in HTML
        fig.add_annotation(
            text=f"<script>window.networkData = {json.dumps(embedded_data, ensure_ascii=False)};</script>",
            showarrow=False,
            xref="paper", yref="paper",
            x=0, y=0, xanchor="left", yanchor="bottom",
            font=dict(size=1, color="rgba(0,0,0,0)")  # Make invisible
        )
        
        return fig
    
    def create_github_ready_visualization(self):
        """
        Create a completely self-contained HTML file for GitHub Pages
        """
        print("\nCreating GitHub Pages ready visualization...")
        
        fig = self.create_3d_temporal_visualization()
        
        # Get the HTML string with CDN-hosted Plotly
        html_string = fig.to_html(
            include_plotlyjs='cdn',
            config={'displayModeBar': True, 'responsive': True}
        )
        
        # Add GitHub Pages compatible styling
        github_style = """
        <style>
            body { 
                margin: 0; 
                padding: 0; 
                height: 100vh; 
                overflow: hidden; 
                font-family: Arial, sans-serif;
            }
            .plotly-graph-div { 
                height: 100vh !important; 
                width: 100vw !important; 
            }
            .main-svg {
                background-color: white !important;
            }
        </style>
        """
        
        # Add viewport meta tag for mobile compatibility
        viewport_meta = '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        
        # Insert enhancements
        html_string = html_string.replace('<head>', '<head>' + viewport_meta + github_style)
        
        # Save the self-contained file
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(html_string)
        
        print("GitHub Pages ready visualization saved to: index.html")
        print("This file contains all data embedded and works without external dependencies!")
        return html_string
    
    def create_individual_period_visualizations(self):
        """
        Create individual 3D visualizations with connection line controls
        """
        figures = {}
        
        for period_name, G in self.networks.items():
            positions = G.graph['positions']
            color = G.graph['color']
            
            # Extract node positions
            node_x = [positions[node][0] for node in G.nodes()]
            node_y = [positions[node][1] for node in G.nodes()]
            node_z = [positions[node][2] for node in G.nodes()]
            
            # Node information and SMALLER sizes
            node_text = []
            node_sizes = []
            
            # Calculate centrality metrics
            degree_centrality = nx.degree_centrality(G)
            betweenness_centrality = nx.betweenness_centrality(G)
            edge_count = dict(G.degree())
            
            for node in G.nodes():
                occurrences = G.nodes[node]['occurrences']
                entity_type = G.nodes[node]['entity_type']
                degree_cent = degree_centrality.get(node, 0)
                betweenness_cent = betweenness_centrality.get(node, 0)
                edges = edge_count.get(node, 0)
                
                text = f"<b>{node}</b><br>Type: {entity_type}<br>Occurrences: {occurrences}<br>Degree Centrality: {degree_cent:.3f}<br>Betweenness Centrality: {betweenness_cent:.3f}<br>Edge Count: {edges}<br>Composite Score: {0.4*degree_cent + 0.3*betweenness_cent + 0.3*(edges/max(edge_count.values()) if edge_count.values() else 1):.3f}"
                node_text.append(text)
                
                # SMALLER node sizes
                node_sizes.append(max(4, min(15, occurrences / 100)))
            
            # Edge positions
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
            
            # Create figure
            fig = go.Figure()
            
            # Add nodes
            fig.add_trace(go.Scatter3d(
                x=node_x, y=node_y, z=node_z,
                mode='markers',
                marker=dict(
                    size=node_sizes,
                    color=color,
                    opacity=0.8,
                    line=dict(width=0.5, color='black'),
                    symbol='circle'
                ),
                text=node_text,
                hoverinfo='text',
                hovertemplate='%{text}<extra></extra>',
                name='Nodes',
                showlegend=True,
                visible=True
            ))
            
            # Add edges (initially hidden)
            fig.add_trace(go.Scatter3d(
                x=edge_x, y=edge_y, z=edge_z,
                mode='lines',
                line=dict(width=1, color='gray'),
                opacity=0.4,
                hoverinfo='none',
                name='Connections',
                showlegend=True,
                visible=False
            ))
            
            # Connection line toggle buttons
            updatemenus = [
                dict(
                    type="buttons",
                    direction="left",
                    buttons=list([
                        dict(
                            label="Nodes Only",
                            method="update",
                            args=[{"visible": [True, False]}]
                        ),
                        dict(
                            label="Nodes + Connections",
                            method="update",
                            args=[{"visible": [True, True]}]
                        ),
                        dict(
                            label="Connections Only",
                            method="update",
                            args=[{"visible": [False, True]}]
                        )
                    ]),
                    pad={"r": 10, "t": 10},
                    showactive=True,
                    x=0.01,
                    xanchor="left",
                    y=1.02,
                    yanchor="top"
                )
            ]
            
            # Full window layout
            fig.update_layout(
                title={
                    'text': f"3D Network - {G.graph['display_name']}<br><sub>Self-contained • Connection line controls</sub>",
                    'x': 0.5,
                    'font': {'size': 16, 'family': 'Arial, sans-serif'}
                },
                updatemenus=updatemenus,
                scene=dict(
                    xaxis=dict(showgrid=True, showticklabels=False, backgroundcolor='rgba(248,248,248,0.8)', 
                              showbackground=True, range=[-10, 10]),
                    yaxis=dict(showgrid=True, showticklabels=False, backgroundcolor='rgba(248,248,248,0.8)', 
                              showbackground=True, range=[-10, 10]),
                    zaxis=dict(showgrid=True, showticklabels=False, backgroundcolor='rgba(248,248,248,0.8)', 
                              showbackground=True),
                    camera=dict(eye=dict(x=1.5, y=1.5, z=1.5)),
                    aspectmode='cube',
                    bgcolor='rgba(255,255,255,0.9)'
                ),
                # Full window expansion
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
        Create network evolution metrics plot with full window
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
        
        # Other metrics
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
        
        # Full window layout
        fig.update_layout(
            autosize=True,
            width=None,
            height=None,
            showlegend=True, 
            title_text="Network Evolution Metrics Over Time",
            title_font_size=18,
            title_font_family='Arial, sans-serif',
            margin=dict(l=0, r=0, b=0, t=60, pad=0),
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
    
    # Calculate 3D positions with enhanced spacing
    analyzer.calculate_3d_positions(layout_type='spring')
    
    print("\n=== GENERATING GITHUB PAGES VISUALIZATIONS ===")
    
    # Create GitHub Pages ready visualization (self-contained)
    github_html = analyzer.create_github_ready_visualization()
    
    # Create individual period visualizations
    individual_figs = analyzer.create_individual_period_visualizations()
    for period_name, fig in individual_figs.items():
        filename = f'network_3d_{period_name.lower().replace("-", "_")}.html'
        fig.write_html(filename, include_plotlyjs='cdn')
        print(f"GitHub ready {period_name} visualization saved to: {filename}")
    
    # Create network metrics plot
    metrics_fig = analyzer.create_network_metrics_plot()
    metrics_fig.write_html('network_metrics.html', include_plotlyjs='cdn')
    print("GitHub ready metrics plot saved to: network_metrics.html")
    
    print("\n=== GITHUB PAGES DEPLOYMENT READY ===")
    print("\nKey features:")
    print("✓ Self-contained HTML with embedded data")
    print("✓ CDN-hosted Plotly (no local dependencies)")
    print("✓ Full window expansion")
    print("✓ Connection line visibility controls")
    print("✓ Mobile-responsive design")
    print("✓ Works without CSV files")
    print("\nDeploy index.html to GitHub Pages - it will work immediately!")
    
    return analyzer

# Execute the analysis
if __name__ == "__main__":
    analyzer = main()
