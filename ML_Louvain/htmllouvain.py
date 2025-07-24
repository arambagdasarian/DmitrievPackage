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
from datetime import datetime
import re
warnings.filterwarnings('ignore')

# Set style for matplotlib
try:
    plt.style.use('seaborn-v0_8')
except:
    try:
        plt.style.use('seaborn')
    except:
        plt.style.use('default')

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
                      '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe',
                      '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57']
        
        # Network filtering parameters
        self.max_nodes = 120  # Optimized for performance
        self.min_edge_weight = 3
        self.max_edges = 350
    
    def check_file_exists(self, filename):
        """Check if file exists and is not empty"""
        if not os.path.exists(filename):
            return False
        return os.path.getsize(filename) > 0
    
    def sanitize_for_js(self, value):
        """Sanitize any value for JavaScript to prevent serialization errors"""
        if pd.isna(value) or value is None:
            return "unknown"
        
        # Convert to string and clean thoroughly
        value = str(value).strip()
        
        # Remove or replace problematic characters
        value = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', value)  # Remove control characters
        value = value.replace('"', "'").replace("'", "`")    # Replace quotes
        value = value.replace('\n', ' ').replace('\r', ' ')  # Remove line breaks
        value = value.replace('\\', '/').replace('\t', ' ')  # Replace backslashes and tabs
        value = re.sub(r'\s+', ' ', value)                   # Normalize whitespace
        
        # Limit length to prevent memory issues
        if len(value) > 40:
            value = value[:37] + "..."
        
        # Ensure it's not empty after cleaning
        if not value or value.isspace():
            value = "entity"
            
        # Ensure it starts with a letter or number (for JavaScript compatibility)
        if not re.match(r'^[a-zA-Z0-9]', value):
            value = "node_" + value
            
        return value
    
    def load_and_create_network_data(self, period):
        """Load data from final_nodes.csv and create network files"""
        nodes_file = f'{period}.csv'
        
        print(f"Processing: {nodes_file}")
        
        if not self.check_file_exists(nodes_file):
            print(f"File not found: {nodes_file}")
            return None, None, None
        
        try:
            # Load with multiple encoding attempts
            encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
            nodes = None
            
            for encoding in encodings:
                try:
                    nodes = pd.read_csv(nodes_file, encoding=encoding)
                    print(f"Successfully loaded with {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    continue
            
            if nodes is None:
                print(f"Failed to load {nodes_file} with any encoding")
                return None, None, None
            
            if nodes.empty:
                print(f"Empty file: {nodes_file}")
                return None, None, None
            
            print(f"Loaded {len(nodes)} rows from {nodes_file}")
            
            # Verify required columns
            if 'Entity' not in nodes.columns or 'Article_ID' not in nodes.columns:
                print(f"Missing required columns. Found: {list(nodes.columns)}")
                return None, None, None
            
            # Clean and sanitize entity names thoroughly
            nodes['Entity'] = nodes['Entity'].apply(self.sanitize_for_js)
            
            # Remove any remaining problematic entries
            nodes = nodes[nodes['Entity'].notna()]
            nodes = nodes[nodes['Entity'] != '']
            nodes = nodes[nodes['Article_ID'].notna()]
            
            # Remove duplicates
            nodes = nodes.drop_duplicates(subset=['Article_ID', 'Entity'])
            
            print(f"After cleaning: {len(nodes)} valid entries")
            
            # Build co-occurrence network
            edges_list = []
            processed_articles = 0
            
            # Process articles in batches for better memory management
            for article_id, group in nodes.groupby('Article_ID'):
                entities = group['Entity'].unique().tolist()
                
                # Only process if we have multiple entities
                if len(entities) < 2:
                    continue
                
                # Limit entities per article to prevent memory issues
                if len(entities) > 20:
                    entities = entities[:20]
                
                # Create edges for entity pairs
                for i, entity1 in enumerate(entities):
                    for entity2 in entities[i+1:]:
                        if entity1 and entity2 and entity1 != entity2:
                            # Create consistent edge ordering
                            edge = tuple(sorted([entity1, entity2]))
                            edges_list.append(edge)
                
                processed_articles += 1
                if processed_articles % 500 == 0:
                    print(f"Processed {processed_articles} articles, found {len(edges_list)} co-occurrences")
            
            print(f"Total co-occurrences: {len(edges_list)}")
            
            if not edges_list:
                print(f"No valid co-occurrences found for {period}")
                return None, None, None
            
            # Count and filter edges
            edge_counts = Counter(edges_list)
            print(f"Unique edge pairs: {len(edge_counts)}")
            
            # Filter by minimum weight
            filtered_edges = [
                {'src': edge[0], 'dst': edge[1], 'weight': count}
                for edge, count in edge_counts.items()
                if count >= self.min_edge_weight
            ]
            
            if not filtered_edges:
                print(f"No edges meet minimum weight threshold of {self.min_edge_weight}")
                # Lower threshold if no edges found
                self.min_edge_weight = max(1, self.min_edge_weight - 1)
                filtered_edges = [
                    {'src': edge[0], 'dst': edge[1], 'weight': count}
                    for edge, count in edge_counts.items()
                    if count >= self.min_edge_weight
                ]
            
            # Limit edges for performance
            if len(filtered_edges) > self.max_edges:
                filtered_edges = sorted(filtered_edges, key=lambda x: x['weight'], reverse=True)[:self.max_edges]
                print(f"Limited to top {self.max_edges} strongest connections")
            
            edges_df = pd.DataFrame(filtered_edges)
            print(f"Final edge list: {len(edges_df)} edges")
            
            # Build NetworkX graph
            G = nx.from_pandas_edgelist(edges_df, 'src', 'dst', edge_attr='weight')
            print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
            
            if G.number_of_nodes() == 0:
                return None, None, None
            
            # Community detection with error handling
            communities = []
            try:
                import networkx.algorithms.community as nx_comm
                communities = list(nx_comm.louvain_communities(G, seed=42, resolution=1.0))
                print(f"Louvain found {len(communities)} communities")
            except Exception as e:
                print(f"Louvain failed ({e}), using connected components")
                communities = list(nx.connected_components(G))
            
            # Create community dataframe
            communities_data = []
            for i, community in enumerate(communities):
                for node in community:
                    communities_data.append({'node': node, 'community': i})
            
            communities_df = pd.DataFrame(communities_data)
            
            # Community statistics
            community_stats = []
            for i, community in enumerate(communities):
                if len(community) > 0:
                    subgraph = G.subgraph(community)
                    community_stats.append({
                        'community': i,
                        'size': len(community),
                        'edges': subgraph.number_of_edges(),
                        'density': nx.density(subgraph) if len(community) > 1 else 0
                    })
            
            stats_df = pd.DataFrame(community_stats)
            
            print(f"Successfully created network data for {period}")
            return edges_df, communities_df, stats_df
            
        except Exception as e:
            print(f"Error processing {period}: {e}")
            import traceback
            traceback.print_exc()
            return None, None, None
    
    def create_robust_network(self, period, edges_df, communities_df):
        """Create a robust network that will definitely load"""
        try:
            print(f"Creating robust network for {period}...")
            
            # Build graph with validation
            G = nx.from_pandas_edgelist(edges_df, 'src', 'dst', edge_attr='weight')
            
            if G.number_of_nodes() == 0:
                print(f"Empty graph for {period}")
                return
            
            # Limit nodes for guaranteed performance
            if G.number_of_nodes() > self.max_nodes:
                # Select most connected nodes
                node_degrees = dict(G.degree())
                top_nodes = sorted(node_degrees.items(), key=lambda x: x[1], reverse=True)[:self.max_nodes]
                selected_nodes = [node for node, _ in top_nodes]
                G = G.subgraph(selected_nodes)
                print(f"Limited to {len(selected_nodes)} most connected nodes")
            
            # Get community mapping with validation
            community_dict = {}
            if communities_df is not None and not communities_df.empty:
                for _, row in communities_df.iterrows():
                    if row['node'] in G.nodes():
                        community_dict[row['node']] = int(row['community'])
            
            # Calculate centrality metrics
            try:
                degree_centrality = nx.degree_centrality(G)
                betweenness_centrality = nx.betweenness_centrality(G, k=min(30, len(G.nodes())))
            except:
                degree_centrality = {node: G.degree(node) / max(1, len(G.nodes()) - 1) for node in G.nodes()}
                betweenness_centrality = {node: 0 for node in G.nodes()}
            
            # Create PyVis network with minimal configuration for stability
            net = Network(
                height="750px",
                width="100%",
                bgcolor="#1a1a1a",
                font_color="#ffffff",
                select_menu=False,  # Disable initially to ensure loading
                filter_menu=False   # Disable initially to ensure loading
            )
            
            # Simple, stable physics
            net.set_options("""
            var options = {
              "physics": {
                "enabled": true,
                "stabilization": {"enabled": true, "iterations": 100},
                "barnesHut": {
                  "gravitationalConstant": -2000,
                  "centralGravity": 0.3,
                  "springLength": 150,
                  "springConstant": 0.04,
                  "damping": 0.09
                }
              }
            }
            """)
            
            # Add nodes with comprehensive validation
            node_count = 0
            for node in G.nodes():
                try:
                    # Validate and sanitize all node properties
                    node_id = self.sanitize_for_js(str(node))
                    if not node_id or node_id == "unknown":
                        node_id = f"node_{node_count}"
                    
                    community = community_dict.get(node, 0)
                    degree = G.degree(node)
                    centrality = degree_centrality.get(node, 0)
                    betweenness = betweenness_centrality.get(node, 0)
                    
                    # Safe color assignment
                    color = self.colors[int(community) % len(self.colors)]
                    
                    # Size with bounds
                    size = max(15, min(40, 15 + degree * 3))
                    
                    # Clean label
                    label = node_id[:20] + "..." if len(node_id) > 20 else node_id
                    
                    # Safe title with proper escaping
                    title = (f"Entity: {node_id}\\n"
                           f"Community: {community}\\n"
                           f"Connections: {degree}\\n"
                           f"Centrality: {centrality:.3f}")
                    
                    # Add node with validated properties
                    net.add_node(
                        node_id,
                        label=label,
                        title=title,
                        color=color,
                        size=int(size),
                        community=int(community),
                        degree=int(degree),
                        centrality=float(centrality)
                    )
                    node_count += 1
                    
                except Exception as e:
                    print(f"Error adding node {node}: {e}")
                    continue
            
            # Add edges with validation
            edge_count = 0
            for _, row in edges_df.iterrows():
                try:
                    src = self.sanitize_for_js(str(row['src']))
                    dst = self.sanitize_for_js(str(row['dst']))
                    weight = int(row.get('weight', 1))
                    
                    # Check if both nodes exist in current graph
                    if src in [self.sanitize_for_js(str(n)) for n in G.nodes()] and \
                       dst in [self.sanitize_for_js(str(n)) for n in G.nodes()]:
                        
                        width = max(1, min(6, weight // 2))
                        
                        net.add_edge(
                            src, dst,
                            value=int(width),
                            width=int(width),
                            title=f"Weight: {weight}",
                            weight=int(weight)
                        )
                        edge_count += 1
                        
                except Exception as e:
                    print(f"Error adding edge: {e}")
                    continue
            
            print(f"Successfully added {node_count} nodes and {edge_count} edges")
            
            # Generate HTML with comprehensive error handling
            filename = f"{period}_interactive_network.html"
            
            try:
                # Generate base HTML
                html_string = net.generate_html()
                
                # Add enhanced features after ensuring base network works
                enhanced_html = self.create_enhanced_html(html_string, period, G, community_dict)
                
                # Write to file with error handling
                with open(filename, 'w', encoding='utf-8', errors='replace') as f:
                    f.write(enhanced_html)
                
                # Verify file creation
                if os.path.exists(filename) and os.path.getsize(filename) > 5000:
                    print(f"✅ SUCCESS: Created {filename} ({os.path.getsize(filename):,} bytes)")
                    
                    # Test HTML validity by checking for required elements
                    with open(filename, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'vis-network' in content and 'nodes' in content and 'edges' in content:
                            print(f"✅ HTML validation passed for {filename}")
                        else:
                            print(f"⚠️ HTML may have issues in {filename}")
                else:
                    print(f"❌ File creation failed or file too small: {filename}")
                    
            except Exception as save_error:
                print(f"❌ Error saving {filename}: {save_error}")
                # Create minimal fallback version
                self.create_fallback_network(period, G, community_dict)
                
        except Exception as e:
            print(f"❌ Error creating network for {period}: {e}")
            import traceback
            traceback.print_exc()
    
    def create_enhanced_html(self, base_html, period, G, community_dict):
        """Add enhanced features while maintaining stability"""
        
        # Calculate statistics
        total_nodes = G.number_of_nodes()
        total_edges = G.number_of_edges()
        num_communities = len(set(community_dict.values())) if community_dict else 0
        avg_degree = sum(dict(G.degree()).values()) / total_nodes if total_nodes > 0 else 0
        
        # Enhanced CSS - stable and tested
        enhanced_css = """
        <style>
            body { 
                font-family: 'Segoe UI', Arial, sans-serif; 
                margin: 0; 
                padding: 0; 
                background: linear-gradient(135deg, #2c3e50, #34495e);
                color: #ecf0f1;
                overflow-x: hidden;
            }
            .header {
                position: fixed; top: 0; left: 0; right: 0; z-index: 2000;
                background: rgba(52, 73, 94, 0.95); backdrop-filter: blur(5px);
                padding: 12px 20px; border-bottom: 2px solid #3498db;
                box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            }
            .header h1 {
                margin: 0; font-size: 20px; color: #3498db; text-align: center;
            }
            .controls {
                position: fixed; top: 70px; right: 15px; z-index: 1500;
                background: rgba(52, 73, 94, 0.95); backdrop-filter: blur(5px);
                padding: 15px; border-radius: 8px; min-width: 250px; max-width: 300px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.3); border: 1px solid #3498db;
                max-height: 75vh; overflow-y: auto;
            }
            .control-section {
                margin-bottom: 15px; padding-bottom: 10px; 
                border-bottom: 1px solid #34495e;
            }
            .control-section:last-child { border-bottom: none; }
            .control-section h3 {
                margin: 0 0 8px 0; font-size: 14px; color: #3498db;
                text-transform: uppercase; letter-spacing: 0.5px;
            }
            .btn {
                background: linear-gradient(135deg, #3498db, #2980b9);
                color: white; border: none; padding: 6px 10px; border-radius: 4px;
                cursor: pointer; margin: 2px; font-size: 11px; font-weight: 600;
                transition: all 0.3s ease; text-transform: uppercase;
            }
            .btn:hover {
                background: linear-gradient(135deg, #2980b9, #1f4e79);
                transform: translateY(-1px);
            }
            .btn.secondary { background: linear-gradient(135deg, #95a5a6, #7f8c8d); }
            .btn.secondary:hover { background: linear-gradient(135deg, #7f8c8d, #6c7b7b); }
            .stats-grid {
                display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin: 8px 0;
            }
            .stat-item {
                background: rgba(52, 152, 219, 0.1); padding: 4px; border-radius: 3px;
                text-align: center; border: 1px solid rgba(52, 152, 219, 0.2);
            }
            .stat-value { font-weight: bold; font-size: 14px; color: #3498db; }
            .stat-label { font-size: 9px; color: #bdc3c7; text-transform: uppercase; }
            .search-input {
                width: 100%; padding: 4px; border: 1px solid #34495e; border-radius: 3px;
                background: #2c3e50; color: white; font-size: 12px;
            }
            .info-panel {
                position: fixed; bottom: 15px; left: 15px;
                background: rgba(52, 73, 94, 0.95); backdrop-filter: blur(5px);
                padding: 15px; border-radius: 8px; max-width: 300px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.3); border: 1px solid #3498db;
            }
            .info-panel h4 { margin: 0 0 8px 0; color: #3498db; font-size: 14px; }
            .info-panel p { margin: 4px 0; font-size: 12px; line-height: 1.3; }
            .info-panel ul { margin: 8px 0; padding-left: 15px; }
            .info-panel li { margin: 2px 0; font-size: 11px; }
            #mynetworkid { margin-top: 70px; height: calc(100vh - 70px) !important; }
            #filterStatus { font-size: 10px; color: #bdc3c7; margin-top: 5px; text-align: center; }
        </style>
        """
        
        # Robust JavaScript with all filtering features
        enhanced_js = f"""
        <script>
            // Global variables for network management
            let allNodes, allEdges, originalNodes, originalEdges;
            let currentFilter = 'none';
            let isPhysicsEnabled = true;
            let networkReady = false;
            
            // Wait for network to be fully initialized
            window.addEventListener('load', function() {{
                console.log('Window loaded, waiting for network...');
                setTimeout(initializeNetworkData, 2000);
            }});
            
            function initializeNetworkData() {{
                try {{
                    if (typeof network !== 'undefined' && network.body && network.body.data) {{
                        allNodes = network.body.data.nodes;
                        allEdges = network.body.data.edges;
                        originalNodes = allNodes.map(n => Object.assign({{}}, n));
                        originalEdges = allEdges.map(e => Object.assign({{}}, e));
                        networkReady = true;
                        console.log('Network initialized:', allNodes.length, 'nodes,', allEdges.length, 'edges');
                        updateFilterStatus();
                    }} else {{
                        console.log('Network not ready, retrying...');
                        setTimeout(initializeNetworkData, 1000);
                    }}
                }} catch (error) {{
                    console.error('Error initializing network data:', error);
                    setTimeout(initializeNetworkData, 1000);
                }}
            }}
            
            // Utility function to check if network is ready
            function checkNetworkReady() {{
                if (!networkReady || typeof network === 'undefined') {{
                    alert('Network is still loading. Please wait a moment and try again.');
                    return false;
                }}
                return true;
            }}
            
            // Reset to show all nodes
            function resetView() {{
                if (!checkNetworkReady()) return;
                try {{
                    network.setData({{nodes: originalNodes, edges: originalEdges}});
                    network.fit();
                    currentFilter = 'none';
                    updateFilterStatus();
                }} catch (error) {{
                    console.error('Error in resetView:', error);
                }}
            }}
            
            // Toggle physics
            function togglePhysics() {{
                if (!checkNetworkReady()) return;
                try {{
                    isPhysicsEnabled = !isPhysicsEnabled;
                    network.setOptions({{physics: {{enabled: isPhysicsEnabled}}}});
                    document.getElementById('physicsBtn').textContent = 
                        isPhysicsEnabled ? 'Disable Physics' : 'Enable Physics';
                }} catch (error) {{
                    console.error('Error in togglePhysics:', error);
                }}
            }}
            
            // Filter by minimum degree
            function filterByDegree(minDegree) {{
                if (!checkNetworkReady()) return;
                try {{
                    // Calculate node degrees
                    const nodeDegrees = {{}};
                    originalEdges.forEach(edge => {{
                        nodeDegrees[edge.from] = (nodeDegrees[edge.from] || 0) + 1;
                        nodeDegrees[edge.to] = (nodeDegrees[edge.to] || 0) + 1;
                    }});
                    
                    // Filter nodes by degree
                    const filteredNodes = originalNodes.filter(node => 
                        (nodeDegrees[node.id] || 0) >= minDegree
                    );
                    
                    const nodeIds = new Set(filteredNodes.map(n => n.id));
                    const filteredEdges = originalEdges.filter(edge =>
                        nodeIds.has(edge.from) && nodeIds.has(edge.to)
                    );
                    
                    network.setData({{nodes: filteredNodes, edges: filteredEdges}});
                    network.fit();
                    currentFilter = `degree-${{minDegree}}`;
                    updateFilterStatus();
                    
                    console.log(`Filtered to ${{filteredNodes.length}} nodes with degree >= ${{minDegree}}`);
                }} catch (error) {{
                    console.error('Error in filterByDegree:', error);
                }}
            }}
            
            // Filter by edge weight
            function filterByWeight(minWeight) {{
                if (!checkNetworkReady()) return;
                try {{
                    const filteredEdges = originalEdges.filter(edge => 
                        (edge.weight || 1) >= minWeight
                    );
                    
                    const connectedNodeIds = new Set();
                    filteredEdges.forEach(edge => {{
                        connectedNodeIds.add(edge.from);
                        connectedNodeIds.add(edge.to);
                    }});
                    
                    const filteredNodes = originalNodes.filter(node =>
                        connectedNodeIds.has(node.id)
                    );
                    
                    network.setData({{nodes: filteredNodes, edges: filteredEdges}});
                    network.fit();
                    currentFilter = `weight-${{minWeight}}`;
                    updateFilterStatus();
                    
                    console.log(`Filtered to ${{filteredEdges.length}} edges with weight >= ${{minWeight}}`);
                }} catch (error) {{
                    console.error('Error in filterByWeight:', error);
                }}
            }}
            
            // Filter by community
            function filterByCommunity(communityId) {{
                if (!checkNetworkReady()) return;
                try {{
                    const filteredNodes = originalNodes.filter(node =>
                        node.community == communityId
                    );
                    
                    const nodeIds = new Set(filteredNodes.map(n => n.id));
                    const filteredEdges = originalEdges.filter(edge =>
                        nodeIds.has(edge.from) && nodeIds.has(edge.to)
                    );
                    
                    network.setData({{nodes: filteredNodes, edges: filteredEdges}});
                    network.fit();
                    currentFilter = `community-${{communityId}}`;
                    updateFilterStatus();
                    
                    console.log(`Filtered to community ${{communityId}} with ${{filteredNodes.length}} nodes`);
                }} catch (error) {{
                    console.error('Error in filterByCommunity:', error);
                }}
            }}
            
            // Show top nodes by importance
            function showTopNodes(count) {{
                if (!checkNetworkReady()) return;
                try {{
                    const sortedNodes = [...originalNodes].sort((a, b) => {{
                        const aValue = a.centrality || a.degree || 0;
                        const bValue = b.centrality || b.degree || 0;
                        return bValue - aValue;
                    }});
                    
                    const topNodes = sortedNodes.slice(0, count);
                    const nodeIds = new Set(topNodes.map(n => n.id));
                    
                    const filteredEdges = originalEdges.filter(edge =>
                        nodeIds.has(edge.from) && nodeIds.has(edge.to)
                    );
                    
                    network.setData({{nodes: topNodes, edges: filteredEdges}});
                    network.fit();
                    currentFilter = `top-${{count}}`;
                    updateFilterStatus();
                    
                    console.log(`Showing top ${{count}} nodes by importance`);
                }} catch (error) {{
                    console.error('Error in showTopNodes:', error);
                }}
            }}
            
            // Search functionality
            function searchNodes() {{
                if (!checkNetworkReady()) return;
                try {{
                    const searchTerm = document.getElementById('searchInput').value.toLowerCase().trim();
                    if (!searchTerm) {{
                        resetView();
                        return;
                    }}
                    
                    const matchingNodes = originalNodes.filter(node => {{
                        const label = (node.label || node.id || '').toLowerCase();
                        return label.includes(searchTerm);
                    }});
                    
                    if (matchingNodes.length === 0) {{
                        alert('No nodes found matching: ' + searchTerm);
                        return;
                    }}
                    
                    const nodeIds = new Set(matchingNodes.map(n => n.id));
                    const filteredEdges = originalEdges.filter(edge =>
                        nodeIds.has(edge.from) && nodeIds.has(edge.to)
                    );
                    
                    network.setData({{nodes: matchingNodes, edges: filteredEdges}});
                    network.fit();
                    currentFilter = `search-${{searchTerm}}`;
                    updateFilterStatus();
                    
                    console.log(`Found ${{matchingNodes.length}} nodes matching "${{searchTerm}}"`);
                }} catch (error) {{
                    console.error('Error in searchNodes:', error);
                }}
            }}
            
            // Update filter status display
            function updateFilterStatus() {{
                try {{
                    const statusElement = document.getElementById('filterStatus');
                    if (statusElement && typeof network !== 'undefined') {{
                        const currentData = network.body.data;
                        statusElement.textContent = 
                            `Showing: ${{currentData.nodes.length}} nodes, ${{currentData.edges.length}} edges`;
                    }}
                }} catch (error) {{
                    console.error('Error updating filter status:', error);
                }}
            }}
            
            // Export network data
            function exportNetwork() {{
                if (!checkNetworkReady()) return;
                try {{
                    const currentData = network.body.data;
                    const exportData = {{
                        period: '{period}',
                        nodes: currentData.nodes.map(n => ({{
                            id: n.id, 
                            label: n.label, 
                            community: n.community,
                            degree: n.degree
                        }})),
                        edges: currentData.edges.map(e => ({{
                            from: e.from, 
                            to: e.to, 
                            weight: e.weight
                        }})),
                        filter: currentFilter,
                        timestamp: new Date().toISOString(),
                        stats: {{
                            total_nodes: currentData.nodes.length,
                            total_edges: currentData.edges.length,
                            communities: [...new Set(currentData.nodes.map(n => n.community))].length
                        }}
                    }};
                    
                    const blob = new Blob([JSON.stringify(exportData, null, 2)], {{
                        type: 'application/json'
                    }});
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = '{period}_network_filtered.json';
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                    
                    console.log('Network data exported successfully');
                }} catch (error) {{
                    console.error('Error exporting network:', error);
                    alert('Error exporting network data. Check console for details.');
                }}
            }}
            
            // Fit view
            function fitView() {{
                if (!checkNetworkReady()) return;
                try {{
                    network.fit();
                }} catch (error) {{
                    console.error('Error fitting view:', error);
                }}
            }}
            
            // Network event handlers
            if (typeof network !== 'undefined') {{
                network.on('stabilizationIterationsDone', function() {{
                    console.log('Network stabilization complete');
                    if (!networkReady) initializeNetworkData();
                }});
            }}
        </script>
        """
        
        # Control panel HTML with all features
        controls_html = f"""
        <div class="header">
            <h1>{self.period_labels.get(period, period)} - Network Analysis</h1>
        </div>
        
        <div class="controls">
            <div class="control-section">
                <h3>Network Statistics</h3>
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value">{total_nodes}</div>
                        <div class="stat-label">Nodes</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{total_edges}</div>
                        <div class="stat-label">Edges</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{num_communities}</div>
                        <div class="stat-label">Communities</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{avg_degree:.1f}</div>
                        <div class="stat-label">Avg Degree</div>
                    </div>
                </div>
                <div id="filterStatus">Loading network data...</div>
            </div>
            
            <div class="control-section">
                <h3>View Controls</h3>
                <button onclick="resetView()" class="btn">Show All</button>
                <button onclick="fitView()" class="btn secondary">Fit View</button><br>
                <button onclick="togglePhysics()" id="physicsBtn" class="btn secondary">Disable Physics</button>
                <button onclick="exportNetwork()" class="btn secondary">Export</button>
            </div>
            
            <div class="control-section">
                <h3>Filter by Connections</h3>
                <button onclick="filterByDegree(1)" class="btn">All</button>
                <button onclick="filterByDegree(3)" class="btn">3+</button>
                <button onclick="filterByDegree(5)" class="btn">5+</button>
                <button onclick="filterByDegree(10)" class="btn">10+</button>
            </div>
            
            <div class="control-section">
                <h3>Filter by Co-occurrence</h3>
                <button onclick="filterByWeight(3)" class="btn">3+</button>
                <button onclick="filterByWeight(5)" class="btn">5+</button>
                <button onclick="filterByWeight(10)" class="btn">10+</button>
                <button onclick="filterByWeight(15)" class="btn">15+</button>
            </div>
            
            <div class="control-section">
                <h3>Top Nodes</h3>
                <button onclick="showTopNodes(20)" class="btn">Top 20</button>
                <button onclick="showTopNodes(50)" class="btn">Top 50</button>
            </div>
            
            <div class="control-section">
                <h3>Search Entities</h3>
                <input type="text" id="searchInput" class="search-input" 
                       placeholder="Search entities..." 
                       onkeypress="if(event.key==='Enter') searchNodes()">
                <button onclick="searchNodes()" class="btn" style="margin-top: 4px; width: 100%;">Search</button>
            </div>
        </div>
        
        <div class="info-panel">
            <h4>Network Guide</h4>
            <p><strong>Period:</strong> {self.period_labels.get(period, period)}</p>
            <p><strong>How to use:</strong></p>
            <ul>
                <li>Drag nodes to reposition</li>
                <li>Hover for entity details</li>
                <li>Scroll to zoom in/out</li>
                <li>Use filters to focus analysis</li>
                <li>Search for specific entities</li>
                <li>Export filtered data</li>
            </ul>
        </div>
        """
        
        # Insert all enhancements into the HTML
        if '<head>' in base_html:
            base_html = base_html.replace('<head>', f'<head>{enhanced_css}')
        
        if '<body>' in base_html:
            base_html = base_html.replace('<body>', f'<body>{controls_html}')
        
        if '</body>' in base_html:
            base_html = base_html.replace('</body>', f'{enhanced_js}</body>')
        
        return base_html
    
    def create_fallback_network(self, period, G, community_dict):
        """Create a minimal fallback network if main creation fails"""
        try:
            print(f"Creating fallback network for {period}...")
            
            # Create very simple network
            simple_net = Network(height="600px", width="100%")
            
            # Add only a subset of nodes
            for i, node in enumerate(list(G.nodes())[:20]):  # Only first 20 nodes
                community = community_dict.get(node, 0)
                color = self.colors[community % len(self.colors)]
                simple_net.add_node(str(node), label=str(node)[:15], color=color)
            
            # Add edges between these nodes
            for edge in list(G.edges())[:30]:  # Only first 30 edges
                if str(edge[0]) in [str(n) for n in list(G.nodes())[:20]] and \
                   str(edge[1]) in [str(n) for n in list(G.nodes())[:20]]:
                    simple_net.add_edge(str(edge[0]), str(edge[1]))
            
            fallback_filename = f"{period}_fallback_network.html"
            simple_net.show(fallback_filename)
            print(f"✅ Created fallback network: {fallback_filename}")
            
        except Exception as e:
            print(f"❌ Even fallback network failed: {e}")
    
    def create_interactive_networks(self):
        """Create interactive network visualizations for each period"""
        print("🚀 Starting robust network creation process...")
        
        for period in self.periods:
            try:
                print(f"\n{'='*60}")
                print(f"🔄 PROCESSING: {period.upper()}")
                print(f"{'='*60}")
                
                # Load or create data
                edges_file = f'{period}_edges.csv'
                communities_file = f'{period}_communities.csv'
                
                edges_df, communities_df, stats_df = None, None, None
                
                # Try loading existing files
                if (self.check_file_exists(edges_file) and 
                    self.check_file_exists(communities_file)):
                    try:
                        edges_df = pd.read_csv(edges_file)
                        communities_df = pd.read_csv(communities_file)
                        print(f"📂 Loaded existing processed files for {period}")
                    except Exception as e:
                        print(f"❌ Error loading existing files: {e}")
                        edges_df, communities_df = None, None
                
                # Create from source if needed
                if edges_df is None or communities_df is None or edges_df.empty:
                    print(f"🔨 Creating network data from source for {period}")
                    edges_df, communities_df, stats_df = self.load_and_create_network_data(period)
                    
                    # Save processed files
                    if edges_df is not None and not edges_df.empty:
                        try:
                            edges_df.to_csv(edges_file, index=False)
                            communities_df.to_csv(communities_file, index=False)
                            if stats_df is not None:
                                stats_df.to_csv(f'{period}_community_stats.csv', index=False)
                            print(f"💾 Saved processed files for {period}")
                        except Exception as save_error:
                            print(f"❌ Error saving files: {save_error}")
                
                # Create visualization
                if edges_df is not None and not edges_df.empty:
                    print(f"🎨 Creating enhanced network visualization for {period}")
                    self.create_robust_network(period, edges_df, communities_df)
                else:
                    print(f"❌ No valid data available for {period}")
                    
            except Exception as e:
                print(f"❌ Critical error processing {period}: {e}")
                import traceback
                traceback.print_exc()
    
    def run_complete_visualization(self):
        """Execute complete visualization pipeline with robust error handling"""
        print("🎯 STARTING ENHANCED TEMPORAL NETWORK VISUALIZATION")
        print("="*70)
        print("🔧 Configuration:")
        print(f"   📊 Max nodes per network: {self.max_nodes}")
        print(f"   🔗 Max edges per network: {self.max_edges}")
        print(f"   ⚖️  Minimum edge weight: {self.min_edge_weight}")
        print("="*70)
        
        # Check for source files
        print("📁 Checking source files...")
        available_periods = []
        for period in self.periods:
            if self.check_file_exists(f'{period}.csv'):
                available_periods.append(period)
                print(f"   ✅ {period}.csv found")
            else:
                print(f"   ❌ {period}.csv missing")
        
        if not available_periods:
            print("❌ No source CSV files found! Expected files:")
            for period in self.periods:
                print(f"   - {period}.csv")
            return
        
        try:
            # Create networks for available periods
            print(f"\n🎨 Creating networks for {len(available_periods)} periods...")
            self.create_interactive_networks()
            
            print("\n" + "="*70)
            print("🎉 VISUALIZATION COMPLETE!")
            print("="*70)
            print("📄 Generated HTML files:")
            
            successful_files = []
            for period in self.periods:
                html_file = f"{period}_interactive_network.html"
                if os.path.exists(html_file) and os.path.getsize(html_file) > 5000:
                    file_size = os.path.getsize(html_file)
                    print(f"   ✅ {html_file} ({file_size:,} bytes)")
                    successful_files.append(html_file)
                else:
                    fallback_file = f"{period}_fallback_network.html"
                    if os.path.exists(fallback_file):
                        print(f"   ⚠️  {fallback_file} (fallback version)")
                        successful_files.append(fallback_file)
                    else:
                        print(f"   ❌ No file created for {period}")
            
            if successful_files:
                print(f"\n✨ SUCCESS: Created {len(successful_files)} working network visualizations!")
                print("\n🎯 ENHANCED FEATURES AVAILABLE:")
                print("   🔍 Smart filtering by connection count")
                print("   ⚖️  Filter by co-occurrence strength") 
                print("   🏆 Show top nodes by importance")
                print("   🔎 Entity search functionality")
                print("   📊 Real-time network statistics")
                print("   💾 Export filtered network data")
                print("   🎛️  Physics simulation toggle")
                print("   🎨 Enhanced visual styling")
                print("   📱 Responsive design")
                
                print(f"\n🚀 READY TO USE:")
                print("   1. Open any HTML file in your web browser")
                print("   2. Wait for the network to finish loading")
                print("   3. Use the control panel to filter and analyze")
                print("   4. Hover over nodes for detailed information")
                print("   5. Export your filtered results")
            else:
                print("\n❌ No successful network files were created.")
                print("   Check the error messages above for troubleshooting.")
                
        except Exception as e:
            print(f"\n❌ CRITICAL ERROR: {e}")
            import traceback
            traceback.print_exc()
            print("\n🔧 TROUBLESHOOTING TIPS:")
            print("   1. Check that your CSV files have 'Entity' and 'Article_ID' columns")
            print("   2. Ensure CSV files are properly formatted and not corrupted")
            print("   3. Try running on a single period first to isolate issues")
            print("   4. Check available memory and disk space")

# Execute the complete visualization
if __name__ == "__main__":
    print("🎯 Temporal Network Analyzer - Enhanced Version")
    print("="*50)
    visualizer = TemporalNetworkVisualizer()
    visualizer.run_complete_visualization()
