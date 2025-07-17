import pandas as pd
import networkx as nx
import numpy as np
import json
import gzip
import base64
from itertools import combinations
from collections import Counter, defaultdict
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio
import warnings
warnings.filterwarnings('ignore')

# Set plotly renderer to browser
pio.renderers.default = "browser"

class OptimizedTemporalNetworkAnalyzer:
    def __init__(self, datasets):
        """
        Initialize with datasets for each time period
        """
        self.datasets = datasets
        self.networks = {}
        self.edge_data = {}
        self.node_positions = {}
        self.combined_network = None
        self.compressed_data = {}  # Store compressed data only
        
    def compress_data(self, data):
        """
        Compress data using gzip and base64 encoding
        """
        json_str = json.dumps(data, ensure_ascii=False)
        compressed = gzip.compress(json_str.encode('utf-8'))
        encoded = base64.b64encode(compressed).decode('ascii')
        return encoded
    
    def create_minimal_dataset(self, df, period_name):
        """
        Create minimal dataset with only essential information
        """
        # Keep only essential columns and top entities
        essential_cols = ['Entity', 'Entity_Type', 'Occurrences', 'Article_ID']
        df_minimal = df[essential_cols].copy()
        
        # Keep only top entities by occurrences to reduce size
        top_entities = df_minimal.groupby('Entity')['Occurrences'].sum().nlargest(500).index
        df_minimal = df_minimal[df_minimal['Entity'].isin(top_entities)]
        
        # Convert to minimal format
        minimal_data = []
        for _, row in df_minimal.iterrows():
            minimal_data.append({
                'e': row['Entity'],  # Shortened keys
                't': row['Entity_Type'],
                'o': int(row['Occurrences']),
                'a': row['Article_ID']
            })
        
        return minimal_data
    
    def store_optimized_data(self):
        """
        Store optimized and compressed data for embedding
        """
        self.compressed_data = {}
        
        for period_name, df in self.datasets.items():
            print(f"Optimizing data for {period_name}...")
            
            # Create minimal dataset
            minimal_data = self.create_minimal_dataset(df, period_name)
            
            # Compress the data
            compressed = self.compress_data(minimal_data)
            
            self.compressed_data[period_name] = {
                'data': compressed,
                'size': len(compressed),
                'original_rows': len(df),
                'compressed_rows': len(minimal_data)
            }
            
            print(f"  Original: {len(df)} rows")
            print(f"  Compressed: {len(minimal_data)} rows")
            print(f"  Data size: {len(compressed)} bytes")
    
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
                    'articles': edge_articles[(entity1, entity2)][:10]  # Limit articles
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
            k_value = max(0.3, 1/np.sqrt(n_nodes)) if n_nodes > 0 else 0.3
            
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
            degree_centrality = nx.degree_centrality(G) if G.number_of_nodes() > 0 else {}
            betweenness_centrality = nx.betweenness_centrality(G) if G.number_of_nodes() > 0 else {}
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
    
    def create_optimized_github_visualization(self):
        """
        Create optimized GitHub Pages visualization with compressed data
        """
        print("\nCreating optimized GitHub Pages visualization...")
        
        fig = go.Figure()
        
        # Enhanced period colors
        period_colors = {
            'Pre-Crimea': '#FF4444',
            'Post-Crimea': '#00CED1',
            'Covid': '#1E90FF',
            'War': '#32CD32'
        }
        
        # Create minimal embedded data
        minimal_embedded_data = {
            'compressed_data': self.compressed_data,
            'periods': list(self.networks.keys()),
            'period_colors': period_colors,
            'network_summary': {}
        }
        
        # Add network summary only
        for period_name, G in self.networks.items():
            minimal_embedded_data['network_summary'][period_name] = {
                'nodes': G.number_of_nodes(),
                'edges': G.number_of_edges(),
                'density': float(nx.density(G)) if G.number_of_nodes() > 0 else 0.0
            }
        
        # Add visualization traces (nodes and edges)
        for period_name, G in self.networks.items():
            if 'positions' not in G.graph:
                continue
                
            positions = G.graph['positions']
            color = period_colors[period_name]
            
            # Extract node positions
            node_x = [positions[node][0] for node in G.nodes()]
            node_y = [positions[node][1] for node in G.nodes()]
            node_z = [positions[node][2] for node in G.nodes()]
            
            # Node information and sizes
            node_text = []
            node_sizes = []
            
            # Calculate centrality metrics
            degree_centrality = nx.degree_centrality(G) if G.number_of_nodes() > 0 else {}
            betweenness_centrality = nx.betweenness_centrality(G) if G.number_of_nodes() > 0 else {}
            edge_count = dict(G.degree())
            
            for node in G.nodes():
                occurrences = G.nodes[node]['occurrences']
                entity_type = G.nodes[node]['entity_type']
                degree_cent = degree_centrality.get(node, 0)
                betweenness_cent = betweenness_centrality.get(node, 0)
                edges = edge_count.get(node, 0)
                
                composite_score = 0.4*degree_cent + 0.3*betweenness_cent + 0.3*(edges/max(edge_count.values()) if edge_count.values() else 1)
                text = f"<b>{node}</b><br>Period: {period_name}<br>Type: {entity_type}<br>Occurrences: {occurrences}<br>Degree: {degree_cent:.3f}<br>Betweenness: {betweenness_cent:.3f}<br>Edges: {edges}<br>Score: {composite_score:.3f}"
                node_text.append(text)
                
                # Smaller node sizes
                node_sizes.append(max(4, min(15, occurrences / 100)))
            
            # Node trace
            if node_x:
                node_trace = go.Scatter3d(
                    x=node_x, y=node_y, z=node_z,
                    mode='markers',
                    marker=dict(
                        size=node_sizes,
                        color=color,
                        opacity=0.8,
                        line=dict(width=0.5, color='black')
                    ),
                    text=node_text,
                    hoverinfo='text',
                    hovertemplate='%{text}<extra></extra>',
                    name=f'{period_name} Nodes',
                    showlegend=True,
                    visible=True
                )
                fig.add_trace(node_trace)
            
            # Edge traces (simplified)
            edge_x, edge_y, edge_z = [], [], []
            for edge in list(G.edges())[:500]:  # Limit edges for performance
                if edge[0] in positions and edge[1] in positions:
                    x0, y0, z0 = positions[edge[0]]
                    x1, y1, z1 = positions[edge[1]]
                    edge_x.extend([x0, x1, None])
                    edge_y.extend([y0, y1, None])
                    edge_z.extend([z0, z1, None])
            
            if edge_x:
                edge_trace = go.Scatter3d(
                    x=edge_x, y=edge_y, z=edge_z,
                    mode='lines',
                    line=dict(width=1, color=color),
                    opacity=0.3,
                    hoverinfo='none',
                    name=f'{period_name} Edges',
                    showlegend=False,
                    visible=False
                )
                fig.add_trace(edge_trace)
        
        # Interactive buttons
        updatemenus = [
            dict(
                type="buttons",
                direction="left",
                buttons=[
                    dict(label="All Nodes", method="update", args=[{"visible": [True if i % 2 == 0 else False for i in range(len(fig.data))]}]),
                    dict(label="All + Edges", method="update", args=[{"visible": [True] * len(fig.data)}]),
                    dict(label="Pre-Crimea", method="update", args=[{"visible": [i == 0 for i in range(len(fig.data))]}]),
                    dict(label="Post-Crimea", method="update", args=[{"visible": [i == 2 for i in range(len(fig.data))]}]),
                    dict(label="Covid", method="update", args=[{"visible": [i == 4 for i in range(len(fig.data))]}]),
                    dict(label="War", method="update", args=[{"visible": [i == 6 for i in range(len(fig.data))]}])
                ],
                showactive=True,
                x=0.01, xanchor="left", y=1.02, yanchor="top"
            )
        ]
        
        # Layout
        fig.update_layout(
            title="3D Temporal Network Analysis - Optimized for GitHub Pages",
            updatemenus=updatemenus,
            scene=dict(
                xaxis=dict(title='X', showgrid=True, range=[-10, 10]),
                yaxis=dict(title='Y', showgrid=True, range=[-10, 10]),
                zaxis=dict(title='Time + Centrality', showgrid=True, range=[-12, 12]),
                camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
            ),
            autosize=True,
            margin=dict(l=0, r=0, b=0, t=100),
            font=dict(family='Arial, sans-serif')
        )
        
        # Create optimized HTML
        html_string = fig.to_html(include_plotlyjs='cdn')
        
        # Add compressed data and decompression functions
        data_script = f'''
        <script>
            // Compressed data for GitHub Pages
            window.compressedNetworkData = {json.dumps(minimal_embedded_data)};
            
            // Decompression function
            function decompressData(compressedData) {{
                try {{
                    const binaryString = atob(compressedData);
                    const bytes = new Uint8Array(binaryString.length);
                    for (let i = 0; i < binaryString.length; i++) {{
                        bytes[i] = binaryString.charCodeAt(i);
                    }}
                    const decompressed = pako.inflate(bytes, {{to: 'string'}});
                    return JSON.parse(decompressed);
                }} catch (e) {{
                    console.error('Decompression failed:', e);
                    return null;
                }}
            }}
            
            // Load pako for decompression
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/pako/2.1.0/pako.min.js';
            script.onload = function() {{
                console.log('Pako loaded, data ready for decompression');
                window.decompressedData = {{}};
                for (const [period, data] of Object.entries(window.compressedNetworkData.compressed_data)) {{
                    window.decompressedData[period] = decompressData(data.data);
                }}
            }};
            document.head.appendChild(script);
        </script>
        '''
        
        # Enhanced styling
        style = '''
        <style>
            body {{ margin: 0; padding: 0; height: 100vh; overflow: hidden; }}
            .plotly-graph-div {{ height: 100vh !important; width: 100vw !important; }}
            .status {{ position: fixed; top: 10px; right: 10px; background: #28a745; color: white; padding: 5px 10px; border-radius: 5px; font-size: 12px; z-index: 1000; }}
        </style>
        '''
        
        html_string = html_string.replace('<head>', f'<head><meta name="viewport" content="width=device-width, initial-scale=1.0">{style}')
        html_string = html_string.replace('</head>', data_script + '</head>')
        html_string = html_string.replace('<body>', '<body><div class="status">✓ Optimized</div>')
        
        return html_string

def main():
    """
    Main execution function with optimization
    """
    try:
        # Load datasets
        datasets = {
            'Pre-Crimea': pd.read_csv('matched_entities_pre_crimea_cleaned.csv'),
            'Post-Crimea': pd.read_csv('matched_entities_post_crimea_cleaned.csv'),
            'Covid': pd.read_csv('matched_entities_covid_cleaned.csv'),
            'War': pd.read_csv('matched_entities_war_cleaned.csv')
        }
        
        print("=== OPTIMIZED TEMPORAL NETWORK ANALYSIS ===")
        total_size = 0
        for name, df in datasets.items():
            size = df.memory_usage(deep=True).sum()
            total_size += size
            print(f"{name}: {len(df):,} rows, {size/1024/1024:.1f}MB")
        print(f"Total data size: {total_size/1024/1024:.1f}MB")
        
        # Initialize analyzer
        analyzer = OptimizedTemporalNetworkAnalyzer(datasets)
        
        # Store optimized data
        analyzer.store_optimized_data()
        
        # Build networks
        analyzer.build_temporal_networks(min_weight=2)
        analyzer.create_combined_temporal_network()
        analyzer.calculate_3d_positions()
        
        # Create optimized visualization
        print("\n=== GENERATING OPTIMIZED GITHUB PAGES VISUALIZATION ===")
        html_content = analyzer.create_optimized_github_visualization()
        
        # Save optimized HTML
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        file_size = len(html_content.encode('utf-8'))
        print(f"\nOptimized HTML saved: {file_size/1024/1024:.1f}MB")
        
        if file_size < 25 * 1024 * 1024:  # 25MB
            print("✓ File size is GitHub compatible!")
        else:
            print("⚠ File still too large for GitHub")
            
        return analyzer
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    analyzer = main()
