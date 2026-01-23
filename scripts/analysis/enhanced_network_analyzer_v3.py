import pandas as pd
import networkx as nx
import numpy as np
from collections import Counter
import warnings
import os
import json
import re
from datetime import datetime, date
warnings.filterwarnings('ignore')

class EnhancedNetworkAnalyzerV3:
    def __init__(self):
        # [Previous __init__ code remains the same]
        self.max_nodes_per_period = 2000
        self.min_edge_weight = 1
        self.max_edges_per_period = 1500
        
        self.period_dates = {
            'pre_crimea': ('2010-01-01', '2013-10-31'),
            'post_crimea': ('2014-01-01', '2017-01-31'),
            'covid': ('2020-01-01', '2022-01-31'),
            'war': ('2022-02-01', '2025-06-29')
        }
        
        self.community_colors = [
            '#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6',
            '#1abc9c', '#e67e22', '#34495e', '#f1c40f', '#e91e63',
            '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57',
            '#ff9ff3', '#54a0ff', '#5f27cd', '#00d2d3', '#ff9f43'
        ]
        
        self.russian_jurisdictions = {'RUS', 'RUSSIA', 'RF', 'RUSSIAN FEDERATION'}
        self.min_russian_occurrences = 150
        
        self.non_russian_entities = {
            'TRUMP', 'VSU', 'UKRAINIAN ARMED FORCES', 'NATO',
            'EU', 'UNITED STATES', 'CHINA', 'GERMANY'
        }
    
    def is_russian_actor(self, Jurisdiction, entity_name):
        """Enhanced check for Russian actors with explicit exclusions"""
        if entity_name.upper() in self.non_russian_entities:
            return False
        return str(Jurisdiction).upper() in self.russian_jurisdictions
    
    def process_network_data(self, df):
        """[Previous process_network_data code remains the same]"""
        print("Processing combined network data...")
        
        required_columns = ['Entity', 'Article_ID', 'Jurisdiction']
        if not all(col in df.columns for col in required_columns):
            print("Error: Missing required columns:", required_columns)
            return [], []
        
        entity_type_col = 'Entity_Type' if 'Entity_Type' in df.columns else None
        print(f"Available columns: {list(df.columns)}")
        
        edges_list = []
        entity_details = {}
        
        for article_id, group in df.groupby('Article_ID'):
            entities = group['Entity'].unique().tolist()
            if len(entities) < 2:
                continue
            
            for _, row in group.iterrows():
                entity = row['Entity']
                if entity not in entity_details:
                    details = {
                        'Jurisdiction': row['Jurisdiction'],
                        'occurrences': row.get('Occurrences', 1),  # Note: Changed to match actual column name
                        'is_russian': self.is_russian_actor(row['Jurisdiction'], entity),
                        'article_count': 0,
                        'periods': set()
                    }
                    if entity_type_col:
                        details['Entity_Type'] = row[entity_type_col]
                    else:
                        details['Entity_Type'] = 'Unknown'
                    
                    entity_details[entity] = details
                
                entity_details[entity]['article_count'] += 1
                if 'period' in row:
                    entity_details[entity]['periods'].add(row['period'])
            
            for i, entity1 in enumerate(entities):
                for entity2 in entities[i+1:]:
                    if entity1 != entity2:
                        edge = tuple(sorted([entity1, entity2]))
                        edges_list.append(edge)
        
        edge_counts = Counter(edges_list)
        filtered_edges = [
            {'from': edge[0], 'to': edge[1], 'weight': count}
            for edge, count in edge_counts.items()
            if count >= self.min_edge_weight
        ]
        
        G = nx.Graph()
        for edge in filtered_edges:
            G.add_edge(edge['from'], edge['to'], weight=edge['weight'])
        
        if len(G.nodes()) == 0:
            print("No nodes in graph")
            return [], []
        
        try:
            import networkx.algorithms.community as nx_comm
            communities = list(nx_comm.louvain_communities(G, seed=42, resolution=1.0))
        except:
            communities = list(nx.connected_components(G))
        
        community_map = {}
        for i, community in enumerate(communities):
            for node in community:
                community_map[node] = i
        
        metrics = {}
        try:
            metrics['degree_centrality'] = nx.degree_centrality(G)
            metrics['betweenness_centrality'] = nx.betweenness_centrality(G, k=min(100, len(G.nodes())))
            metrics['closeness_centrality'] = nx.closeness_centrality(G)
            metrics['eigenvector_centrality'] = nx.eigenvector_centrality_numpy(G, max_iter=1000)
        except:
            metrics['degree_centrality'] = {node: G.degree(node) / len(G.nodes()) for node in G.nodes()}
            metrics['betweenness_centrality'] = {node: 0 for node in G.nodes()}
            metrics['closeness_centrality'] = {node: 0 for node in G.nodes()}
            metrics['eigenvector_centrality'] = {node: 0 for node in G.nodes()}
        
        nodes = []
        for node in G.nodes():
            degree = G.degree(node)
            community = community_map.get(node, 0)
            details = entity_details.get(node, {})
            
            cent = metrics['degree_centrality'].get(node, 0)
            betw = metrics['betweenness_centrality'].get(node, 0)
            clos = metrics['closeness_centrality'].get(node, 0)
            eigen = metrics['eigenvector_centrality'].get(node, 0)
            article_count = details.get('article_count', 0)
            period_count = len(details.get('periods', set()))
            
            importance = (
                cent * 0.25 + 
                betw * 0.2 + 
                clos * 0.2 + 
                eigen * 0.15 + 
                (article_count / 100) * 0.1 + 
                (period_count / 4) * 0.1
            )
            
            size = max(10, min(40, 10 + importance * 150 + degree))
            
            nodes.append({
                'id': node,
                'label': str(node),
                'original_label': str(node),
                'periods': list(details.get('periods', [])),
                'community': community,
                'degree': degree,
                'centrality': round(cent, 4),
                'betweenness': round(betw, 4),
                'closeness': round(clos, 4),
                'eigenvector': round(eigen, 4),
                'importance': round(importance, 4),
                'article_count': article_count,
                'period_count': period_count,
                'size': int(size),
                'color': self.community_colors[community % len(self.community_colors)],
                'Jurisdiction': details.get('Jurisdiction', 'Unknown'),
                'Entity_Type': details.get('Entity_Type', 'Unknown'),
                'occurrences': details.get('occurrences', 0),
                'is_russian': details.get('is_russian', False)
            })
        
        edges = []
        for edge in filtered_edges:
            edges.append({
                'from': edge['from'],
                'to': edge['to'],
                'weight': edge['weight'],
                'width': max(0.2, min(3, edge['weight'] / 10)),
                'color': '#95a5a6'
            })
        
        print(f"✅ Combined network: {len(nodes)} nodes, {len(edges)} edges, {len(communities)} communities")
        return nodes, edges
    
    def create_enhanced_html(self, nodes_data, edges_data):
        """Create the enhanced HTML visualization"""
        # Read the template file
        template_path = os.path.join(os.path.dirname(__file__), 'network_template.html')
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
        except FileNotFoundError:
            print(f"Template file not found at {template_path}")
            return self.create_basic_html(nodes_data, edges_data)
        
        # Convert data to JSON
        nodes_json = json.dumps(nodes_data, indent=2)
        edges_json = json.dumps(edges_data, indent=2)
        
        # Replace placeholders in template
        html_content = template.replace('{nodes_json}', nodes_json).replace('{edges_json}', edges_json)
        
        return html_content
    
    def create_basic_html(self, nodes_data, edges_data):
        """Create a basic HTML visualization if template is not available"""
        nodes_json = json.dumps(nodes_data, indent=2)
        edges_json = json.dumps(edges_data, indent=2)
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Network Visualization</title>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        #network {{
            width: 100%;
            height: 100vh;
            background: #000000;
        }}
    </style>
</head>
<body>
    <div id="network"></div>
    <script>
        const nodes = new vis.DataSet({nodes_json});
        const edges = new vis.DataSet({edges_json});
        
        const container = document.getElementById('network');
        const data = {{
            nodes: nodes,
            edges: edges
        }};
        const options = {{
            physics: {{
                enabled: true,
                barnesHut: {{
                    gravitationalConstant: -2000,
                    centralGravity: 0.1,
                    springLength: 120,
                    springConstant: 0.04,
                    damping: 0.15
                }}
            }}
        }};
        
        const network = new vis.Network(container, data, options);
    </script>
</body>
</html>
        """
        
        return html_content
    
    def run_enhanced_analysis(self):
        """[Previous run_enhanced_analysis code remains the same]"""
        print("🚀 Starting Enhanced Network Analysis V3 - Combined Periods")
        print("=" * 80)
        
        try:
            df = pd.read_csv('final_nodes.csv')
            print("Loaded data with columns:", list(df.columns))
        except Exception as e:
            print(f"Error loading data: {e}")
            return None
        
        if df.empty:
            print("Error: Empty dataset")
            return None
        
        all_nodes, all_edges = self.process_network_data(df)
        
        if not all_nodes:
            print("Error: No nodes generated")
            return None
        
        html_content = self.create_enhanced_html(all_nodes, all_edges)
        
        filename = "enhanced_network_analyzer_v3.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print("\n✅ ENHANCED NETWORK ANALYZER V3 - COMBINED PERIODS ANALYSIS")
        print(f"📁 Output: {filename}")
        
        return filename

# Execute the analysis
if __name__ == "__main__":
    analyzer = EnhancedNetworkAnalyzerV3()
    result_file = analyzer.run_enhanced_analysis()