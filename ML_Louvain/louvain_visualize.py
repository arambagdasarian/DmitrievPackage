import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pyvis.network import Network
import numpy as np
from collections import Counter
import warnings
import os
import json
import re
warnings.filterwarnings('ignore')

class TemporalNetworkVisualizer:
    def __init__(self):
        self.periods = ['pre_crimea', 'post_crimea', 'covid', 'war']
        self.period_labels = {
            'pre_crimea': 'Pre-Crimea (2010-2013)',
            'post_crimea': 'Post-Crimea (2013-2019)', 
            'covid': 'COVID Period (2020-2022)',
            'war': 'War Period (2022-2025)'
        }
        self.colors = ['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', 
                      '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe']
        
        # Optimized parameters for reliability
        self.max_nodes = 80   # Reduced for better performance
        self.min_edge_weight = 3
        self.max_edges = 250  # Reduced for faster loading
    
    def check_file_exists(self, filename):
        """Check if file exists and is not empty"""
        if not os.path.exists(filename):
            return False
        return os.path.getsize(filename) > 0
    
    def clean_text(self, text):
        """Simple, reliable text cleaning"""
        if pd.isna(text) or text is None:
            return "unknown"
        
        text = str(text).strip()
        # Remove problematic characters
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'\s+', '_', text)
        
        if len(text) > 30:
            text = text[:30]
        
        if not text:
            text = "node"
            
        return text
    
    def load_and_create_network_data(self, period):
        """Load data and create network with simplified approach"""
        nodes_file = f'{period}.csv'
        
        if not self.check_file_exists(nodes_file):
            print(f"File not found: {nodes_file}")
            return None, None, None
        
        try:
            # Load data
            nodes = pd.read_csv(nodes_file, encoding='utf-8')
            
            if nodes.empty or 'Entity' not in nodes.columns or 'Article_ID' not in nodes.columns:
                print(f"Invalid data in {nodes_file}")
                return None, None, None
            
            print(f"Processing {len(nodes)} rows from {nodes_file}")
            
            # Clean entity names
            nodes['Entity'] = nodes['Entity'].apply(self.clean_text)
            nodes = nodes.dropna(subset=['Entity', 'Article_ID'])
            nodes = nodes[nodes['Entity'] != 'unknown']
            
            # Create co-occurrence network
            edges_list = []
            for article_id, group in nodes.groupby('Article_ID'):
                entities = group['Entity'].unique().tolist()
                if len(entities) < 2:
                    continue
                    
                # Limit entities per article
                if len(entities) > 15:
                    entities = entities[:15]
                
                # Create entity pairs
                for i, entity1 in enumerate(entities):
                    for entity2 in entities[i+1:]:
                        if entity1 != entity2:
                            edge = tuple(sorted([entity1, entity2]))
                            edges_list.append(edge)
            
            if not edges_list:
                print(f"No co-occurrences found for {period}")
                return None, None, None
            
            # Count edges and filter
            edge_counts = Counter(edges_list)
            filtered_edges = [
                {'src': edge[0], 'dst': edge[1], 'weight': count}
                for edge, count in edge_counts.items()
                if count >= self.min_edge_weight
            ]
            
            # Limit edges
            if len(filtered_edges) > self.max_edges:
                filtered_edges = sorted(filtered_edges, key=lambda x: x['weight'], reverse=True)[:self.max_edges]
            
            edges_df = pd.DataFrame(filtered_edges)
            
            # Create graph and communities
            G = nx.from_pandas_edgelist(edges_df, 'src', 'dst', edge_attr='weight')
            
            # Simple community detection
            try:
                import networkx.algorithms.community as nx_comm
                communities = list(nx_comm.louvain_communities(G, seed=42))
            except:
                communities = list(nx.connected_components(G))
            
            # Create community dataframe
            communities_data = []
            for i, community in enumerate(communities):
                for node in community:
                    communities_data.append({'node': node, 'community': i})
            
            communities_df = pd.DataFrame(communities_data)
            
            print(f"Created network: {len(G.nodes())} nodes, {len(edges_df)} edges, {len(communities)} communities")
            return edges_df, communities_df, None
            
        except Exception as e:
            print(f"Error processing {period}: {e}")
            return None, None, None
    
    def create_working_network(self, period, edges_df, communities_df):
        """Create a reliable network that loads and works"""
        try:
            print(f"Creating network for {period}...")
            
            # Build graph
            G = nx.from_pandas_edgelist(edges_df, 'src', 'dst', edge_attr='weight')
            
            # Limit nodes for performance
            if G.number_of_nodes() > self.max_nodes:
                degrees = dict(G.degree())
                top_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:self.max_nodes]
                selected_nodes = [node for node, _ in top_nodes]
                G = G.subgraph(selected_nodes)
            
            # Get community mapping
            community_dict = {}
            if communities_df is not None and not communities_df.empty:
                for _, row in communities_df.iterrows():
                    if row['node'] in G.nodes():
                        community_dict[row['node']] = int(row['community'])
            
            # Create PyVis network with minimal configuration
            net = Network(
                height="700px",
                width="100%",
                bgcolor="#1a1a1a",
                font_color="white"
            )
            
            # Simple physics
            net.set_options("""
            var options = {
              "physics": {
                "enabled": true,
                "stabilization": {"enabled": true, "iterations": 50}
              }
            }
            """)
            
            # Add nodes
            for node in G.nodes():
                community = community_dict.get(node, 0)
                degree = G.degree(node)
                color = self.colors[community % len(self.colors)]
                size = max(15, min(35, 15 + degree * 2))
                
                net.add_node(
                    str(node),
                    label=str(node)[:20],
                    color=color,
                    size=size,
                    title=f"Entity: {node}\\nCommunity: {community}\\nConnections: {degree}",
                    community=community,
                    degree=degree
                )
            
            # Add edges
            for _, row in edges_df.iterrows():
                src, dst, weight = str(row['src']), str(row['dst']), row['weight']
                if src in [str(n) for n in G.nodes()] and dst in [str(n) for n in G.nodes()]:
                    width = max(1, min(5, weight // 2))
                    net.add_edge(src, dst, width=width, weight=weight)
            
            # Generate HTML
            html = net.generate_html()
            
            # Add working controls
            enhanced_html = self.add_simple_controls(html, period, G)
            
            # Save file
            filename = f"{period}_network.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(enhanced_html)
            
            if os.path.exists(filename):
                print(f"✅ Created working network: {filename}")
            else:
                print(f"❌ Failed to create {filename}")
                
        except Exception as e:
            print(f"Error creating network for {period}: {e}")
    
    def add_simple_controls(self, html, period, G):
        """Add simple, working controls"""
        
        # Calculate stats
        total_nodes = G.number_of_nodes()
        total_edges = G.number_of_edges()
        avg_degree = sum(dict(G.degree()).values()) / total_nodes if total_nodes > 0 else 0
        
        # Simple CSS
        css = """
        <style>
            .control-panel {
                position: fixed;
                top: 20px;
                right: 20px;
                background: rgba(0,0,0,0.8);
                color: white;
                padding: 20px;
                border-radius: 10px;
                z-index: 1000;
                max-width: 300px;
            }
            .control-section {
                margin-bottom: 15px;
            }
            .control-section h3 {
                margin: 0 0 10px 0;
                color: #3498db;
                font-size: 14px;
            }
            .btn {
                background: #3498db;
                color: white;
                border: none;
                padding: 8px 12px;
                margin: 2px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 12px;
            }
            .btn:hover {
                background: #2980b9;
            }
            .stats {
                background: rgba(52, 152, 219, 0.2);
                padding: 10px;
                border-radius: 5px;
                font-size: 12px;
            }
            .search-box {
                width: 100%;
                padding: 5px;
                margin: 5px 0;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            #status {
                font-size: 11px;
                color: #bdc3c7;
                margin-top: 10px;
            }
        </style>
        """
        
        # Working JavaScript
        js = f"""
        <script>
            let originalData = null;
            let networkReady = false;
            
            // Wait for network to load
            setTimeout(function() {{
                if (typeof network !== 'undefined') {{
                    originalData = {{
                        nodes: network.body.data.nodes.map(n => ({{...n}})),
                        edges: network.body.data.edges.map(e => ({{...e}}))
                    }};
                    networkReady = true;
                    updateStatus('Network ready - ' + originalData.nodes.length + ' nodes, ' + originalData.edges.length + ' edges');
                    console.log('Network initialized successfully');
                }} else {{
                    setTimeout(arguments.callee, 1000);
                }}
            }}, 2000);
            
            function updateStatus(message) {{
                const statusEl = document.getElementById('status');
                if (statusEl) statusEl.textContent = message;
            }}
            
            function resetView() {{
                if (!networkReady || !originalData) {{
                    alert('Network not ready yet, please wait...');
                    return;
                }}
                try {{
                    network.setData(originalData);
                    network.fit();
                    updateStatus('Showing all nodes');
                }} catch (e) {{
                    console.error('Reset error:', e);
                }}
            }}
            
            function filterByDegree(minDegree) {{
                if (!networkReady || !originalData) {{
                    alert('Network not ready yet, please wait...');
                    return;
                }}
                try {{
                    const filteredNodes = originalData.nodes.filter(n => (n.degree || 0) >= minDegree);
                    const nodeIds = new Set(filteredNodes.map(n => n.id));
                    const filteredEdges = originalData.edges.filter(e => nodeIds.has(e.from) && nodeIds.has(e.to));
                    
                    network.setData({{nodes: filteredNodes, edges: filteredEdges}});
                    network.fit();
                    updateStatus('Showing ' + filteredNodes.length + ' nodes with ' + minDegree + '+ connections');
                }} catch (e) {{
                    console.error('Filter error:', e);
                }}
            }}
            
            function filterByWeight(minWeight) {{
                if (!networkReady || !originalData) {{
                    alert('Network not ready yet, please wait...');
                    return;
                }}
                try {{
                    const filteredEdges = originalData.edges.filter(e => (e.weight || 1) >= minWeight);
                    const nodeIds = new Set();
                    filteredEdges.forEach(e => {{
                        nodeIds.add(e.from);
                        nodeIds.add(e.to);
                    }});
                    const filteredNodes = originalData.nodes.filter(n => nodeIds.has(n.id));
                    
                    network.setData({{nodes: filteredNodes, edges: filteredEdges}});
                    network.fit();
                    updateStatus('Showing ' + filteredNodes.length + ' nodes with ' + minWeight + '+ co-occurrences');
                }} catch (e) {{
                    console.error('Weight filter error:', e);
                }}
            }}
            
            function searchNodes() {{
                if (!networkReady || !originalData) {{
                    alert('Network not ready yet, please wait...');
                    return;
                }}
                const searchTerm = document.getElementById('searchInput').value.toLowerCase().trim();
                if (!searchTerm) {{
                    resetView();
                    return;
                }}
                
                try {{
                    const matchingNodes = originalData.nodes.filter(n => 
                        (n.label || n.id || '').toLowerCase().includes(searchTerm)
                    );
                    
                    if (matchingNodes.length === 0) {{
                        alert('No matches found for: ' + searchTerm);
                        return;
                    }}
                    
                    const nodeIds = new Set(matchingNodes.map(n => n.id));
                    const filteredEdges = originalData.edges.filter(e => nodeIds.has(e.from) && nodeIds.has(e.to));
                    
                    network.setData({{nodes: matchingNodes, edges: filteredEdges}});
                    network.fit();
                    updateStatus('Found ' + matchingNodes.length + ' matches for "' + searchTerm + '"');
                }} catch (e) {{
                    console.error('Search error:', e);
                }}
            }}
            
            function togglePhysics() {{
                if (!networkReady) {{
                    alert('Network not ready yet, please wait...');
                    return;
                }}
                try {{
                    const physicsEnabled = network.physics.physicsEnabled;
                    network.setOptions({{physics: {{enabled: !physicsEnabled}}}});
                    updateStatus('Physics ' + (physicsEnabled ? 'disabled' : 'enabled'));
                }} catch (e) {{
                    console.error('Physics toggle error:', e);
                }}
            }}
        </script>
        """
        
        # Control panel HTML
        controls = f"""
        <div class="control-panel">
            <div class="control-section">
                <h3>{self.period_labels.get(period, period)}</h3>
                <div class="stats">
                    <strong>Nodes:</strong> {total_nodes}<br>
                    <strong>Edges:</strong> {total_edges}<br>
                    <strong>Avg Degree:</strong> {avg_degree:.1f}
                </div>
            </div>
            
            <div class="control-section">
                <h3>View Controls</h3>
                <button class="btn" onclick="resetView()">Show All</button>
                <button class="btn" onclick="network.fit()">Fit View</button>
                <button class="btn" onclick="togglePhysics()">Toggle Physics</button>
            </div>
            
            <div class="control-section">
                <h3>Filter by Connections</h3>
                <button class="btn" onclick="filterByDegree(1)">All</button>
                <button class="btn" onclick="filterByDegree(3)">3+</button>
                <button class="btn" onclick="filterByDegree(5)">5+</button>
                <button class="btn" onclick="filterByDegree(10)">10+</button>
            </div>
            
            <div class="control-section">
                <h3>Filter by Co-occurrence</h3>
                <button class="btn" onclick="filterByWeight(3)">3+</button>
                <button class="btn" onclick="filterByWeight(5)">5+</button>
                <button class="btn" onclick="filterByWeight(10)">10+</button>
            </div>
            
            <div class="control-section">
                <h3>Search</h3>
                <input type="text" id="searchInput" class="search-box" placeholder="Search entities...">
                <button class="btn" onclick="searchNodes()" style="width: 100%; margin-top: 5px;">Search</button>
            </div>
            
            <div id="status">Initializing network...</div>
        </div>
        """
        
        # Insert into HTML
        if '<head>' in html:
            html = html.replace('<head>', f'<head>{css}')
        
        if '<body>' in html:
            html = html.replace('<body>', f'<body>{controls}')
        
        if '</body>' in html:
            html = html.replace('</body>', f'{js}</body>')
        
        return html
    
    def create_interactive_networks(self):
        """Create networks for all periods"""
        for period in self.periods:
            try:
                print(f"\n--- Processing {period} ---")
                
                # Load or create data
                edges_file = f'{period}_edges.csv'
                communities_file = f'{period}_communities.csv'
                
                if (self.check_file_exists(edges_file) and 
                    self.check_file_exists(communities_file)):
                    edges_df = pd.read_csv(edges_file)
                    communities_df = pd.read_csv(communities_file)
                    print("Loaded existing data")
                else:
                    edges_df, communities_df, _ = self.load_and_create_network_data(period)
                    if edges_df is not None:
                        edges_df.to_csv(edges_file, index=False)
                        communities_df.to_csv(communities_file, index=False)
                        print("Created and saved new data")
                
                if edges_df is not None and not edges_df.empty:
                    self.create_working_network(period, edges_df, communities_df)
                else:
                    print(f"No data for {period}")
                    
            except Exception as e:
                print(f"Error with {period}: {e}")
    
    def run_complete_visualization(self):
        """Run the complete visualization process"""
        print("🚀 Starting Reliable Network Visualization")
        print("=" * 50)
        
        try:
            self.create_interactive_networks()
            
            print("\n" + "=" * 50)
            print("✅ COMPLETED!")
            print("=" * 50)
            
            # Check results
            created_files = []
            for period in self.periods:
                filename = f"{period}_network.html"
                if os.path.exists(filename):
                    size = os.path.getsize(filename)
                    print(f"✅ {filename} ({size:,} bytes)")
                    created_files.append(filename)
            
            if created_files:
                print(f"\n🎯 SUCCESS: Created {len(created_files)} working networks!")
                print("\n📋 WORKING FEATURES:")
                print("   • Filter by connection count (1, 3+, 5+, 10+)")
                print("   • Filter by co-occurrence strength (3+, 5+, 10+)")  
                print("   • Search for specific entities")
                print("   • Reset to show all nodes")
                print("   • Fit view and toggle physics")
                print("   • Real-time status updates")
                
                print("\n🎮 HOW TO USE:")
                print("   1. Open HTML file in browser")
                print("   2. Wait for 'Network ready' status")
                print("   3. Use buttons in control panel")
                print("   4. All buttons should work properly")
                
            else:
                print("\n❌ No files were created successfully")
                
        except Exception as e:
            print(f"\n❌ Critical error: {e}")

# Run the visualization
if __name__ == "__main__":
    visualizer = TemporalNetworkVisualizer()
    visualizer.run_complete_visualization()
