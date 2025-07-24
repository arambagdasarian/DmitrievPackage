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

class EnhancedNetworkAnalyzer:
    def __init__(self):
        # Updated network parameters for more nodes
        self.max_nodes_per_period = 150  # Can be adjusted dynamically
        self.min_edge_weight = 2
        self.max_edges_per_period = 400
        
        # Date ranges for periods
        self.period_dates = {
            'pre_crimea': ('2010-01-01', '2013-10-31'),
            'post_crimea': ('2013-11-01', '2019-12-31'),
            'covid': ('2020-01-01', '2022-01-31'),
            'war': ('2022-02-01', '2025-06-29')
        }
        
        self.period_labels = {
            'pre_crimea': 'Pre-Crimea (2010-2013)',
            'post_crimea': 'Post-Crimea (2013-2019)', 
            'covid': 'COVID Period (2020-2022)',
            'war': 'War Period (2022-2025)'
        }
        
        # Enhanced community colors for better distinction
        self.community_colors = [
            '#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6',
            '#1abc9c', '#e67e22', '#34495e', '#f1c40f', '#e91e63',
            '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57',
            '#ff9ff3', '#54a0ff', '#5f27cd', '#00d2d3', '#ff9f43'
        ]
        
        # Enhanced country flags including UAE, SA, KW
        self.country_flags = {
            'US': '🇺🇸', 'RU': '🇷🇺', 'UA': '🇺🇦', 'CN': '🇨🇳', 'UK': '🇬🇧',
            'DE': '🇩🇪', 'FR': '🇫🇷', 'IT': '🇮🇹', 'JP': '🇯🇵', 'CA': '🇨🇦',
            'BR': '🇧🇷', 'IN': '🇮🇳', 'AU': '🇦🇺', 'MX': '🇲🇽', 'ES': '🇪🇸',
            'CH': '🇨🇭', 'SE': '🇸🇪', 'NO': '🇳🇴',
            'UAE': '🇦🇪',  # United Arab Emirates
            'SA': '🇸🇦',   # Saudi Arabia  
            'KW': '🇰🇼',   # Kuwait
            'Unknown': '🏳️', 'International': '🌐'
        }
        
        # Define Russian actor jurisdictions
        self.russian_jurisdictions = {
            'RU', 'Russia', 'Russian', 'Moscow', 'RF', 'RussFed', 'Kremlin'
        }
        
        # Define International actor jurisdictions
        self.international_jurisdictions = {
            'International', 'EU', 'UN', 'NATO', 'OSCE', 'IMF', 'World Bank',
            'G7', 'G20', 'OECD', 'WTO', 'European Union'
        }
    
    def check_file_exists(self, filename):
        """Check if file exists and is not empty"""
        return os.path.exists(filename) and os.path.getsize(filename) > 0
    
    def clean_text(self, text):
        """Clean text for JavaScript compatibility"""
        if pd.isna(text) or text is None:
            return "unknown"
        
        text = str(text).strip()
        # Remove special characters that can break JavaScript
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'\s+', '_', text)
        
        if len(text) > 25:  # Increased from 20
            text = text[:25]
        
        return text if text else "node"
    
    def parse_date(self, date_str):
        """Parse date string to datetime object"""
        if pd.isna(date_str):
            return None
        
        try:
            # Try different date formats
            for fmt in ['%Y-%m-%d', '%d.%m.%Y', '%m/%d/%Y', '%Y/%m/%d']:
                try:
                    return datetime.strptime(str(date_str), fmt).date()
                except ValueError:
                    continue
            return None
        except:
            return None
    
    def get_period_from_date(self, article_date):
        """Determine period based on article date"""
        if not article_date:
            return None
        
        for period, (start_str, end_str) in self.period_dates.items():
            start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
            
            if start_date <= article_date <= end_date:
                return period
        
        return None
    
    def classify_actor_type(self, jurisdiction):
        """Classify actors as Russian, International, or Other"""
        if jurisdiction in self.russian_jurisdictions:
            return "Russian"
        elif jurisdiction in self.international_jurisdictions:
            return "International"
        else:
            return "Other"
    
    def load_final_nodes_data(self):
        """Load and process data from final_nodes.csv"""
        filename = 'final_nodes.csv'
        
        if not self.check_file_exists(filename):
            print(f"Warning: {filename} not found, creating sample data")
            return self.create_comprehensive_sample_data()
        
        try:
            print(f"Loading data from {filename}...")
            df = pd.read_csv(filename, encoding='utf-8')
            
            if df.empty:
                print("File is empty, creating sample data")
                return self.create_comprehensive_sample_data()
            
            print(f"Loaded {len(df)} rows from {filename}")
            print(f"Columns: {list(df.columns)}")
            
            # Check for required columns
            required_cols = ['Article_ID', 'Entity']
            if not all(col in df.columns for col in required_cols):
                print(f"Missing required columns. Found: {list(df.columns)}")
                return self.create_comprehensive_sample_data()
            
            # Clean and prepare data
            df['Entity'] = df['Entity'].apply(self.clean_text)
            df = df.dropna(subset=['Entity', 'Article_ID'])
            df = df[df['Entity'] != 'unknown']
            
            # Process dates if available
            if 'Date' in df.columns:
                df['parsed_date'] = df['Date'].apply(self.parse_date)
                df['period'] = df['parsed_date'].apply(self.get_period_from_date)
                df = df.dropna(subset=['period'])
            else:
                # If no date column, distribute randomly across periods
                periods = list(self.period_dates.keys())
                df['period'] = np.random.choice(periods, size=len(df))
            
            # Extract jurisdiction information
            df['jurisdiction'] = 'Unknown'
            if 'Jurisdiction' in df.columns:
                df['jurisdiction'] = df['Jurisdiction'].fillna('Unknown')
            elif 'Country' in df.columns:
                df['jurisdiction'] = df['Country'].fillna('Unknown')
            
            # Extract entity type information
            df['entity_type'] = 'Unknown'
            if 'Entity_Type' in df.columns:
                df['entity_type'] = df['Entity_Type'].fillna('Unknown')
            
            # Extract context if available
            df['context'] = ''
            if 'Context_Text' in df.columns:
                df['context'] = df['Context_Text'].fillna('')
            
            # Classify actor types
            df['actor_type'] = df['jurisdiction'].apply(self.classify_actor_type)
            
            print(f"After processing: {len(df)} valid rows")
            print(f"Periods distribution: {df['period'].value_counts().to_dict()}")
            print(f"Actor types distribution: {df['actor_type'].value_counts().to_dict()}")
            
            return self.process_periods_from_dataframe(df)
            
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return self.create_comprehensive_sample_data()
    
    def process_periods_from_dataframe(self, df):
        """Process network data for each period from the main dataframe"""
        all_nodes = []
        all_edges = []
        
        for period in self.period_dates.keys():
            period_df = df[df['period'] == period].copy()
            
            if period_df.empty:
                print(f"No data for {period}, creating sample data")
                sample_nodes, sample_edges = self.create_sample_data(period)
                all_nodes.extend(sample_nodes)
                all_edges.extend(sample_edges)
                continue
            
            print(f"Processing {period}: {len(period_df)} rows")
            
            # Create co-occurrence network
            edges_list = []
            entity_details = {}  # Store entity metadata
            
            for article_id, group in period_df.groupby('Article_ID'):
                entities = group['Entity'].unique().tolist()
                if len(entities) < 2:
                    continue
                
                # Store entity details
                for _, row in group.iterrows():
                    entity = row['Entity']
                    if entity not in entity_details:
                        entity_details[entity] = {
                            'jurisdiction': row['jurisdiction'],
                            'entity_type': row['entity_type'],
                            'context': row['context'][:100] if row['context'] else '',
                            'occurrences': 0,
                            'actor_type': row['actor_type']
                        }
                    entity_details[entity]['occurrences'] += 1
                
                # Limit entities per article
                if len(entities) > 15:  # Increased from 12
                    entities = entities[:15]
                
                # Create entity pairs
                for i, entity1 in enumerate(entities):
                    for entity2 in entities[i+1:]:
                        if entity1 != entity2:
                            edge = tuple(sorted([entity1, entity2]))
                            edges_list.append(edge)
            
            if not edges_list:
                print(f"No co-occurrences found for {period}")
                continue
            
            # Count edge frequencies and filter
            edge_counts = Counter(edges_list)
            filtered_edges = [
                {'from': edge[0], 'to': edge[1], 'weight': count, 'period': period}
                for edge, count in edge_counts.items()
                if count >= self.min_edge_weight
            ]
            
            # Limit edges for performance
            if len(filtered_edges) > self.max_edges_per_period:
                filtered_edges = sorted(filtered_edges, 
                                      key=lambda x: x['weight'], 
                                      reverse=True)[:self.max_edges_per_period]
            
            # Create graph
            G = nx.Graph()
            for edge in filtered_edges:
                G.add_edge(edge['from'], edge['to'], weight=edge['weight'])
            
            # Limit nodes if necessary (dynamic based on max_nodes_per_period)
            if G.number_of_nodes() > self.max_nodes_per_period:
                # Use degree and occurrence count for ranking
                node_scores = {}
                for node in G.nodes():
                    degree = G.degree(node)
                    occurrences = entity_details.get(node, {}).get('occurrences', 0)
                    node_scores[node] = degree * 0.7 + occurrences * 0.3
                
                top_nodes = sorted(node_scores.items(), 
                                 key=lambda x: x[1], 
                                 reverse=True)[:self.max_nodes_per_period]
                selected_nodes = set([node for node, _ in top_nodes])
                
                filtered_edges = [e for e in filtered_edges 
                                if e['from'] in selected_nodes and e['to'] in selected_nodes]
                G = G.subgraph(selected_nodes)
            
            # Enhanced community detection
            try:
                import networkx.algorithms.community as nx_comm
                communities = list(nx_comm.louvain_communities(G, seed=42, resolution=1.2))
            except:
                communities = list(nx.connected_components(G))
            
            # Create community mapping
            community_map = {}
            community_stats = {}
            for i, community in enumerate(communities):
                for node in community:
                    community_map[node] = i
                
                # Calculate community statistics
                subgraph = G.subgraph(community)
                community_stats[i] = {
                    'size': len(community),
                    'edges': subgraph.number_of_edges(),
                    'density': nx.density(subgraph) if len(community) > 1 else 0,
                    'avg_degree': sum(dict(subgraph.degree()).values()) / len(community) if community else 0
                }
            
            # Calculate centrality measures
            try:
                centrality = nx.degree_centrality(G)
                betweenness = nx.betweenness_centrality(G, k=min(50, len(G.nodes())))
                closeness = nx.closeness_centrality(G)
            except:
                centrality = {node: G.degree(node) / len(G.nodes()) for node in G.nodes()}
                betweenness = {node: 0 for node in G.nodes()}
                closeness = {node: 0 for node in G.nodes()}
            
            # Create enhanced node objects
            for node in G.nodes():
                degree = G.degree(node)
                community = community_map.get(node, 0)
                details = entity_details.get(node, {})
                
                # Enhanced node size calculation
                cent = centrality.get(node, 0)
                betw = betweenness.get(node, 0)
                clos = closeness.get(node, 0)
                importance = (cent * 0.4 + betw * 0.3 + clos * 0.3)
                size = max(20, min(60, 20 + importance * 200 + degree * 2))
                
                all_nodes.append({
                    'id': f"{period}_{node}",
                    'label': str(node),
                    'original_label': str(node),
                    'period': period,
                    'community': community,
                    'global_community': f"{period}_{community}",  # Unique across periods
                    'degree': degree,
                    'centrality': round(cent, 4),
                    'betweenness': round(betw, 4),
                    'closeness': round(clos, 4),
                    'importance': round(importance, 4),
                    'size': int(size),
                    'color': self.get_community_color(community),
                    'jurisdiction': details.get('jurisdiction', 'Unknown'),
                    'entity_type': details.get('entity_type', 'Unknown'),
                    'context': details.get('context', ''),
                    'occurrences': details.get('occurrences', 0),
                    'actor_type': details.get('actor_type', 'Other'),
                    'community_size': community_stats[community]['size'],
                    'community_density': round(community_stats[community]['density'], 3)
                })
            
            # Create enhanced edge objects
            for edge in filtered_edges:
                all_edges.append({
                    'from': f"{period}_{edge['from']}",
                    'to': f"{period}_{edge['to']}",
                    'weight': edge['weight'],
                    'period': period,
                    'width': max(2, min(10, edge['weight'] // 2)),
                    'color': self.get_edge_color(edge['weight'])
                })
            
            print(f"✅ {period}: {len(G.nodes())} nodes, {len(filtered_edges)} edges, {len(communities)} communities")
        
        return all_nodes, all_edges
    
    def get_community_color(self, community):
        """Get color for community with more variety"""
        return self.community_colors[community % len(self.community_colors)]
    
    def get_edge_color(self, weight):
        """Get edge color based on weight"""
        if weight >= 15:
            return '#ff4757'  # Strong - red
        elif weight >= 8:
            return '#ff6348'  # Medium-strong - orange-red
        elif weight >= 5:
            return '#ffa502'  # Medium - orange
        elif weight >= 3:
            return '#57606f'  # Weak-medium - gray
        else:
            return '#747d8c'  # Weak - light gray
    
    def create_sample_data(self, period):
        """Create enhanced sample data"""
        nodes = []
        edges = []
        
        # Create more sample nodes
        sample_entities = [
            'Putin', 'Biden', 'Zelensky', 'Xi_Jinping', 'Macron',
            'Russia', 'Ukraine', 'USA', 'China', 'NATO',
            'Moscow', 'Kyiv', 'Washington', 'Beijing', 'Brussels',
            'Sanctions', 'Military', 'Diplomacy', 'Economy', 'Energy'
        ]
        
        jurisdictions = ['RU', 'US', 'UA', 'CN', 'FR', 'UAE', 'SA', 'KW', 'Unknown']
        entity_types = ['Person', 'Organization', 'Location', 'Concept', 'Event']
        
        for i, entity in enumerate(sample_entities):
            community = i % 4
            jurisdiction = jurisdictions[i % len(jurisdictions)]
            entity_type = entity_types[i % len(entity_types)]
            actor_type = self.classify_actor_type(jurisdiction)
            
            nodes.append({
                'id': f"{period}_{entity}",
                'label': entity,
                'original_label': entity,
                'period': period,
                'community': community,
                'global_community': f"{period}_{community}",
                'degree': np.random.randint(3, 12),
                'centrality': round(np.random.random(), 4),
                'betweenness': round(np.random.random(), 4),
                'closeness': round(np.random.random(), 4),
                'importance': round(np.random.random(), 4),
                'size': np.random.randint(25, 55),
                'color': self.get_community_color(community),
                'jurisdiction': jurisdiction,
                'entity_type': entity_type,
                'context': f'Sample context for {entity}',
                'occurrences': np.random.randint(5, 25),
                'actor_type': actor_type,
                'community_size': np.random.randint(3, 8),
                'community_density': round(np.random.random(), 3)
            })
        
        # Create sample edges
        for i in range(len(sample_entities)):
            for j in range(i+1, min(i+6, len(sample_entities))):
                if np.random.random() > 0.6:
                    weight = np.random.randint(3, 15)
                    edges.append({
                        'from': f"{period}_{sample_entities[i]}",
                        'to': f"{period}_{sample_entities[j]}",
                        'weight': weight,
                        'period': period,
                        'width': max(2, min(10, weight // 2)),
                        'color': self.get_edge_color(weight)
                    })
        
        return nodes, edges
    
    def create_comprehensive_sample_data(self):
        """Create sample data for all periods"""
        all_nodes, all_edges = [], []
        
        for period in self.period_dates.keys():
            sample_nodes, sample_edges = self.create_sample_data(period)
            all_nodes.extend(sample_nodes)
            all_edges.extend(sample_edges)
        
        return all_nodes, all_edges
    
    def create_enhanced_html(self, nodes_data, edges_data):
        """Create enhanced HTML with all new features"""
        
        nodes_json = json.dumps(nodes_data, indent=2)
        edges_json = json.dumps(edges_data, indent=2)
        
        # Get unique jurisdictions and communities for filters
        jurisdictions = sorted(set(node['jurisdiction'] for node in nodes_data))
        communities = sorted(set(node['global_community'] for node in nodes_data))
        actor_types = sorted(set(node['actor_type'] for node in nodes_data))
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Enhanced Network Analyzer</title>
    <meta charset="utf-8">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%);
            color: #ffffff;
            overflow: hidden;
        }}
        
        .container {{
            display: flex;
            height: 100vh;
        }}
        
        .sidebar {{
            width: 380px;
            background: rgba(15, 15, 35, 0.95);
            border-right: 2px solid #3498db;
            padding: 20px;
            overflow-y: auto;
            box-shadow: 2px 0 15px rgba(0,0,0,0.3);
        }}
        
        .network-area {{
            flex: 1;
            position: relative;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #3498db;
        }}
        
        .header h1 {{
            font-size: 22px;
            color: #3498db;
            font-weight: 600;
            margin-bottom: 8px;
        }}
        
        .header .subtitle {{
            color: #bdc3c7;
            font-size: 13px;
        }}
        
        .section {{
            margin-bottom: 18px;
            background: rgba(52, 152, 219, 0.1);
            padding: 15px;
            border-radius: 8px;
            border: 1px solid rgba(52, 152, 219, 0.3);
        }}
        
        .section h3 {{
            color: #3498db;
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .btn {{
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white;
            border: none;
            padding: 8px 12px;
            margin: 3px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}
        
        .btn:hover {{
            background: linear-gradient(135deg, #2980b9, #1f4e79);
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(52, 152, 219, 0.3);
        }}
        
        .btn.active {{
            background: linear-gradient(135deg, #e74c3c, #c0392b);
        }}
        
        .btn.secondary {{
            background: linear-gradient(135deg, #95a5a6, #7f8c8d);
        }}
        
        .btn.jurisdiction {{
            font-size: 10px;
            padding: 6px 10px;
        }}
        
        .btn.russian {{
            background: linear-gradient(135deg, #e74c3c, #c0392b);
        }}
        
        .btn.international {{
            background: linear-gradient(135deg, #2ecc71, #27ae60);
        }}
        
        .period-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 5px;
        }}
        
        .jurisdiction-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 3px;
            max-height: 120px;
            overflow-y: auto;
        }}
        
        .actor-type-grid {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 5px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin: 10px 0;
        }}
        
        .stat-card {{
            background: rgba(44, 62, 80, 0.6);
            padding: 10px;
            border-radius: 6px;
            text-align: center;
            border: 1px solid rgba(52, 152, 219, 0.3);
            transition: all 0.3s ease;
        }}
        
        .stat-card:hover {{
            background: rgba(52, 152, 219, 0.2);
            transform: translateY(-1px);
        }}
        
        .stat-value {{
            font-size: 16px;
            font-weight: 700;
            color: #3498db;
        }}
        
        .stat-label {{
            font-size: 10px;
            color: #bdc3c7;
            text-transform: uppercase;
            margin-top: 2px;
        }}
        
        .slider-container {{
            margin: 10px 0;
        }}
        
        .slider-label {{
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            margin-bottom: 5px;
            color: #ecf0f1;
            font-weight: 600;
        }}
        
        .slider {{
            width: 100%;
            height: 8px;
            border-radius: 4px;
            background: #34495e;
            outline: none;
            -webkit-appearance: none;
        }}
        
        .slider::-webkit-slider-thumb {{
            -webkit-appearance: none;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: linear-gradient(135deg, #3498db, #2980b9);
            cursor: pointer;
            border: 2px solid #ffffff;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }}
        
        .search-box, .select-box {{
            width: 100%;
            padding: 8px;
            border: 2px solid #34495e;
            border-radius: 5px;
            background: rgba(44, 62, 80, 0.8);
            color: white;
            font-size: 12px;
            margin-bottom: 8px;
        }}
        
        .search-box:focus, .select-box:focus {{
            border-color: #3498db;
            outline: none;
            box-shadow: 0 0 5px rgba(52, 152, 219, 0.3);
        }}
        
        .select-box option {{
            background: #2c3e50;
            color: white;
        }}
        
        #network {{
            width: 100%;
            height: 100vh;
            background: #0a0a1a;
        }}
        
        .sidebar::-webkit-scrollbar {{
            width: 8px;
        }}
        
        .sidebar::-webkit-scrollbar-thumb {{
            background: linear-gradient(135deg, #3498db, #2980b9);
            border-radius: 4px;
        }}
        
        .sidebar::-webkit-scrollbar-track {{
            background: rgba(44, 62, 80, 0.3);
        }}
        
        .community-item {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 4px 8px;
            margin: 2px 0;
            background: rgba(44, 62, 80, 0.4);
            border-radius: 4px;
            cursor: pointer;
            font-size: 10px;
        }}
        
        .community-item:hover {{
            background: rgba(52, 152, 219, 0.2);
        }}
        
        .community-color {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 6px;
        }}
        
        .performance-warning {{
            background: rgba(243, 156, 18, 0.2);
            border: 1px solid #f39c12;
            color: #f39c12;
            padding: 8px;
            border-radius: 4px;
            font-size: 11px;
            margin-bottom: 8px;
        }}
    </style>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <div class="header">
                <h1>Enhanced Network Analyzer</h1>
                <div class="subtitle">Advanced Analysis with Performance Controls</div>
            </div>
            
            <div class="section">
                <h3> Network Statistics</h3>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value" id="node-count">0</div>
                        <div class="stat-label">Nodes</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="edge-count">0</div>
                        <div class="stat-label">Edges</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="community-count">0</div>
                        <div class="stat-label">Communities</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="jurisdiction-count">0</div>
                        <div class="stat-label">Jurisdictions</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h3>⚡ Performance Controls</h3>
                <div class="performance-warning" id="performance-warning" style="display: none;">
                    Large networks may cause lag. Use node limit controls below.
                </div>
                <div class="slider-container">
                    <div class="slider-label">
                        <span>Max Nodes</span>
                        <span id="node-limit-value">150</span>
                    </div>
                    <input type="range" class="slider" id="node-limit-slider" 
                           min="50" max="500" value="150" 
                           oninput="adjustNodeLimit(this.value)">
                </div>
                <button class="btn secondary" onclick="applyNodeLimit()" style="width: 100%; margin-top: 5px;">
                    Apply Node Limit
                </button>
            </div>
            
            <div class="section">
                <h3> Time Periods</h3>
                <div class="period-grid">
                    <button class="btn" onclick="filterByPeriod('pre_crimea')">Pre-Crimea</button>
                    <button class="btn" onclick="filterByPeriod('post_crimea')">Post-Crimea</button>
                    <button class="btn" onclick="filterByPeriod('covid')">COVID</button>
                    <button class="btn" onclick="filterByPeriod('war')">War</button>
                </div>
                <button class="btn secondary" onclick="showAllPeriods()" style="width: 100%; margin-top: 5px;">Show All Periods</button>
            </div>
            
            <div class="section">
                <h3> Actor Types</h3>
                <div class="actor-type-grid">
                    <button class="btn russian" onclick="filterByActorType('Russian')">Russian Actors</button>
                    <button class="btn international" onclick="filterByActorType('International')">International Actors</button>
                    <button class="btn secondary" onclick="filterByActorType('Other')">Other Actors</button>
                    <button class="btn" onclick="filterByActorType('all')" style="width: 100%; margin-top: 5px;">Show All Types</button>
                </div>
            </div>
            
            <div class="section">
                <h3> Filter by Jurisdiction</h3>
                <div class="jurisdiction-grid">
                    <button class="btn jurisdiction" onclick="filterByJurisdiction('all')">All</button>
                    {self.generate_jurisdiction_buttons(jurisdictions)}
                </div>
            </div>
            
            <div class="section">
                <h3> View Controls</h3>
                <button class="btn" onclick="resetView()">Reset View</button>
                <button class="btn secondary" onclick="fitNetwork()">Fit Network</button><br>
                <button class="btn secondary" onclick="togglePhysics()" id="physics-btn">Stop Physics</button>
                <button class="btn secondary" onclick="exportData()">Export Data</button>
            </div>
            
            <div class="section">
                <h3> Node Spacing</h3>
                <div class="slider-container">
                    <div class="slider-label">
                        <span>Distance</span>
                        <span id="spacing-value">180</span>px
                    </div>
                    <input type="range" class="slider" id="spacing-slider" 
                           min="80" max="500" value="180" 
                           oninput="adjustSpacing(this.value)">
                </div>
            </div>
            
            <div class="section">
                <h3> Node Scale</h3>
                <div class="slider-container">
                    <div class="slider-label">
                        <span>Size</span>
                        <span id="scale-value">1.0</span>x
                    </div>
                    <input type="range" class="slider" id="scale-slider" 
                           min="0.5" max="2.5" step="0.1" value="1.0" 
                           oninput="adjustNodeScale(this.value)">
                </div>
            </div>
            
            <div class="section">
                <h3> Filter by Connections</h3>
                <button class="btn" onclick="filterByDegree(1)">All</button>
                <button class="btn" onclick="filterByDegree(3)">3+</button>
                <button class="btn" onclick="filterByDegree(5)">5+</button>
                <button class="btn" onclick="filterByDegree(8)">8+</button>
                <button class="btn" onclick="filterByDegree(12)">12+</button>
            </div>
            
            <div class="section">
                <h3> Filter by Weight</h3>
                <button class="btn" onclick="filterByWeight(2)">2+</button>
                <button class="btn" onclick="filterByWeight(5)">5+</button>
                <button class="btn" onclick="filterByWeight(8)">8+</button>
                <button class="btn" onclick="filterByWeight(12)">12+</button>
                <button class="btn" onclick="filterByWeight(20)">20+</button>
            </div>
            
            <div class="section">
                <h3> Top Nodes</h3>
                <button class="btn" onclick="showTopNodes(30)">Top 30</button>
                <button class="btn" onclick="showTopNodes(50)">Top 50</button>
                <button class="btn" onclick="showTopNodes(100)">Top 100</button>
            </div>
            
            <div class="section">
                <h3> Communities</h3>
                <select class="select-box" id="community-select" onchange="filterByCommunity(this.value)">
                    <option value="">Select Community</option>
                    <option value="all">Show All</option>
                </select>
                <div id="community-list" style="max-height: 120px; overflow-y: auto; margin-top: 8px;">
                </div>
            </div>
            
            <div class="section">
                <h3> Search</h3>
                <input type="text" class="search-box" id="search-input" 
                       placeholder="Search entities..." 
                       onkeypress="if(event.key==='Enter') searchNodes()">
                <button class="btn" onclick="searchNodes()" style="width: 100%;">Search</button>
            </div>
        </div>
        
        <div class="network-area">
            <div id="network"></div>
        </div>
    </div>

    <script>
        // Embedded data
        const allNodesData = {nodes_json};
        const allEdgesData = {edges_json};
        const countryFlags = {json.dumps(self.country_flags)};
        
        // Network variables
        let network;
        let nodes, edges;
        let allNodes, allEdges;
        let physicsEnabled = true;
        let currentNodeScale = 1.0;
        let currentNodeLimit = 150;
        let isPerformanceWarningShown = false;
        
        // Initialize network when page loads
        document.addEventListener('DOMContentLoaded', function() {{
            initializeNetwork();
            populateCommunityList();
            checkPerformance();
        }});
        
        function checkPerformance() {{
            const totalNodes = allNodesData.length;
            if (totalNodes > 200 && !isPerformanceWarningShown) {{
                document.getElementById('performance-warning').style.display = 'block';
                isPerformanceWarningShown = true;
            }}
        }}
        
        function initializeNetwork() {{
            // Create datasets
            allNodes = new vis.DataSet(allNodesData);
            allEdges = new vis.DataSet(allEdgesData);
            
            // Apply initial node limit
            const limitedData = applyNodeLimitToData(allNodesData, allEdgesData, currentNodeLimit);
            nodes = new vis.DataSet(limitedData.nodes);
            edges = new vis.DataSet(limitedData.edges);
            
            // Enhanced network configuration
            const options = {{
                physics: {{
                    enabled: true,
                    stabilization: {{
                        enabled: true,
                        iterations: 150
                    }},
                    barnesHut: {{
                        gravitationalConstant: -3000,
                        centralGravity: 0.2,
                        springLength: 180,
                        springConstant: 0.05,
                        damping: 0.09,
                        avoidOverlap: 0.2
                    }}
                }},
                interaction: {{
                    hover: true,
                    tooltipDelay: 300,
                    hideEdgesOnDrag: true,
                    hideEdgesOnZoom: true
                }},
                nodes: {{
                    borderWidth: 2,
                    borderWidthSelected: 4,
                    font: {{
                        color: '#ffffff',
                        size: 13,
                        face: 'arial'
                    }},
                    shadow: {{
                        enabled: true,
                        color: 'rgba(0,0,0,0.3)',
                        size: 3
                    }}
                }},
                edges: {{
                    smooth: {{
                        type: 'continuous',
                        forceDirection: 'none'
                    }},
                    shadow: {{
                        enabled: true,
                        color: 'rgba(0,0,0,0.2)',
                        size: 1
                    }}
                }},
                layout: {{
                    improvedLayout: true,
                    clusterThreshold: 150
                }}
            }};
            
            // Create network
            const container = document.getElementById('network');
            network = new vis.Network(container, {{nodes: nodes, edges: edges}}, options);
            
            // Add click event for node details
            network.on('click', function(params) {{
                if (params.nodes.length > 0) {{
                    showNodeDetails(params.nodes[0]);
                }}
            }});
            
            // Update statistics
            updateStats();
            
            console.log('Enhanced network initialized');
        }}
        
        function applyNodeLimitToData(nodeData, edgeData, limit) {{
            if (nodeData.length <= limit) {{
                return {{nodes: nodeData, edges: edgeData}};
            }}
            
            // Sort nodes by importance and take top nodes
            const sortedNodes = nodeData
                .sort((a, b) => (b.importance || 0) - (a.importance || 0))
                .slice(0, limit);
            
            const nodeIds = new Set(sortedNodes.map(n => n.id));
            const filteredEdges = edgeData.filter(e => 
                nodeIds.has(e.from) && nodeIds.has(e.to)
            );
            
            return {{nodes: sortedNodes, edges: filteredEdges}};
        }}
        
        function adjustNodeLimit(value) {{
            currentNodeLimit = parseInt(value);
            document.getElementById('node-limit-value').textContent = currentNodeLimit;
        }}
        
        function applyNodeLimit() {{
            const limitedData = applyNodeLimitToData(allNodesData, allEdgesData, currentNodeLimit);
            nodes.clear();
            edges.clear();
            nodes.add(limitedData.nodes);
            edges.add(limitedData.edges);
            network.fit();
            updateStats();
            
            // Hide performance warning if nodes are reduced
            if (currentNodeLimit <= 200) {{
                document.getElementById('performance-warning').style.display = 'none';
            }}
        }}
        
        function updateStats() {{
            const currentNodes = nodes.get();
            const currentEdges = edges.get();
            
            document.getElementById('node-count').textContent = currentNodes.length;
            document.getElementById('edge-count').textContent = currentEdges.length;
            
            const communities = new Set(currentNodes.map(n => n.global_community)).size;
            document.getElementById('community-count').textContent = communities;
            
            const jurisdictions = new Set(currentNodes.map(n => n.jurisdiction)).size;
            document.getElementById('jurisdiction-count').textContent = jurisdictions;
        }}
        
        function populateCommunityList() {{
            const communities = new Map();
            allNodesData.forEach(node => {{
                const comm = node.global_community;
                if (!communities.has(comm)) {{
                    communities.set(comm, {{
                        color: node.color,
                        size: 0,
                        period: node.period
                    }});
                }}
                communities.get(comm).size++;
            }});
            
            const communitySelect = document.getElementById('community-select');
            const communityList = document.getElementById('community-list');
            
            // Clear existing options (except first two)
            while (communitySelect.options.length > 2) {{
                communitySelect.remove(2);
            }}
            
            communityList.innerHTML = '';
            
            // Sort communities by size
            const sortedCommunities = Array.from(communities.entries())
                .sort((a, b) => b[1].size - a[1].size);
            
            sortedCommunities.forEach(([comm, data]) => {{
                // Add to select
                const option = document.createElement('option');
                option.value = comm;
                option.textContent = `${{comm}} (${{data.size}} nodes)`;
                communitySelect.appendChild(option);
                
                // Add to visual list
                const item = document.createElement('div');
                item.className = 'community-item';
                item.onclick = () => filterByCommunity(comm);
                item.innerHTML = `
                    <div style="display: flex; align-items: center;">
                        <div class="community-color" style="background-color: ${{data.color}};"></div>
                        <span>${{comm.replace('_', ' ').toUpperCase()}}</span>
                    </div>
                    <span>${{data.size}} nodes</span>
                `;
                communityList.appendChild(item);
            }});
        }}
        
        function showNodeDetails(nodeId) {{
            const nodeData = nodes.get(nodeId);
            if (!nodeData) return;
            
            const flag = countryFlags[nodeData.jurisdiction] || '';
            alert(`
Entity: ${{nodeData.original_label}}
Period: ${{nodeData.period}}
Actor Type: ${{nodeData.actor_type}}
Jurisdiction: ${{flag}} ${{nodeData.jurisdiction}}
Entity Type: ${{nodeData.entity_type}}
Connections: ${{nodeData.degree}}
Community: ${{nodeData.global_community}}
Centrality: ${{nodeData.centrality}}
Importance: ${{nodeData.importance}}
Occurrences: ${{nodeData.occurrences}}
            `.trim());
        }}
        
        // Enhanced filtering functions
        function filterByPeriod(period) {{
            const filteredNodes = allNodes.get().filter(n => n.period === period);
            const nodeIds = new Set(filteredNodes.map(n => n.id));
            const filteredEdges = allEdges.get().filter(e => 
                nodeIds.has(e.from) && nodeIds.has(e.to)
            );
            
            updateNetworkData(filteredNodes, filteredEdges);
        }}
        
        function filterByActorType(actorType) {{
            if (actorType === 'all') {{
                resetView();
                return;
            }}
            
            const filteredNodes = allNodes.get().filter(n => n.actor_type === actorType);
            const nodeIds = new Set(filteredNodes.map(n => n.id));
            const filteredEdges = allEdges.get().filter(e => 
                nodeIds.has(e.from) && nodeIds.has(e.to)
            );
            
            updateNetworkData(filteredNodes, filteredEdges);
        }}
        
        function filterByJurisdiction(jurisdiction) {{
            if (jurisdiction === 'all') {{
                resetView();
                return;
            }}
            
            const filteredNodes = allNodes.get().filter(n => n.jurisdiction === jurisdiction);
            const nodeIds = new Set(filteredNodes.map(n => n.id));
            const filteredEdges = allEdges.get().filter(e => 
                nodeIds.has(e.from) && nodeIds.has(e.to)
            );
            
            updateNetworkData(filteredNodes, filteredEdges);
        }}
        
        function filterByCommunity(communityId) {{
            if (!communityId || communityId === 'all') {{
                resetView();
                return;
            }}
            
            const filteredNodes = allNodes.get().filter(n => n.global_community === communityId);
            const nodeIds = new Set(filteredNodes.map(n => n.id));
            const filteredEdges = allEdges.get().filter(e => 
                nodeIds.has(e.from) && nodeIds.has(e.to)
            );
            
            updateNetworkData(filteredNodes, filteredEdges);
        }}
        
        function filterByDegree(minDegree) {{
            const filteredNodes = allNodes.get().filter(n => (n.degree || 0) >= minDegree);
            const nodeIds = new Set(filteredNodes.map(n => n.id));
            const filteredEdges = allEdges.get().filter(e => 
                nodeIds.has(e.from) && nodeIds.has(e.to)
            );
            
            updateNetworkData(filteredNodes, filteredEdges);
        }}
        
        function filterByWeight(minWeight) {{
            const filteredEdges = allEdges.get().filter(e => (e.weight || 1) >= minWeight);
            const nodeIds = new Set();
            filteredEdges.forEach(e => {{
                nodeIds.add(e.from);
                nodeIds.add(e.to);
            }});
            const filteredNodes = allNodes.get().filter(n => nodeIds.has(n.id));
            
            updateNetworkData(filteredNodes, filteredEdges);
        }}
        
        function showTopNodes(count) {{
            const sortedNodes = allNodes.get().sort((a, b) => (b.importance || 0) - (a.importance || 0));
            const topNodes = sortedNodes.slice(0, count);
            const nodeIds = new Set(topNodes.map(n => n.id));
            const filteredEdges = allEdges.get().filter(e => 
                nodeIds.has(e.from) && nodeIds.has(e.to)
            );
            
            updateNetworkData(topNodes, filteredEdges);
        }}
        
        function searchNodes() {{
            const searchTerm = document.getElementById('search-input').value.toLowerCase().trim();
            if (!searchTerm) {{
                resetView();
                return;
            }}
            
            const matchingNodes = allNodes.get().filter(n => 
                (n.original_label || '').toLowerCase().includes(searchTerm) ||
                (n.jurisdiction || '').toLowerCase().includes(searchTerm) ||
                (n.entity_type || '').toLowerCase().includes(searchTerm) ||
                (n.actor_type || '').toLowerCase().includes(searchTerm)
            );
            
            if (matchingNodes.length === 0) {{
                alert('No nodes found matching: ' + searchTerm);
                return;
            }}
            
            const nodeIds = new Set(matchingNodes.map(n => n.id));
            const filteredEdges = allEdges.get().filter(e => 
                nodeIds.has(e.from) && nodeIds.has(e.to)
            );
            
            updateNetworkData(matchingNodes, filteredEdges);
        }}
        
        function updateNetworkData(nodeArray, edgeArray) {{
            // Apply node limit if the data is too large
            if (nodeArray.length > currentNodeLimit) {{
                const limitedData = applyNodeLimitToData(nodeArray, edgeArray, currentNodeLimit);
                nodeArray = limitedData.nodes;
                edgeArray = limitedData.edges;
            }}
            
            nodes.clear();
            edges.clear();
            nodes.add(nodeArray);
            edges.add(edgeArray);
            network.fit();
            updateStats();
        }}
        
        // Enhanced control functions
        function resetView() {{
            const limitedData = applyNodeLimitToData(allNodesData, allEdgesData, currentNodeLimit);
            nodes.clear();
            edges.clear();
            nodes.add(limitedData.nodes);
            edges.add(limitedData.edges);
            network.fit();
            updateStats();
            document.getElementById('community-select').value = '';
        }}
        
        function showAllPeriods() {{
            resetView();
        }}
        
        function fitNetwork() {{
            network.fit();
        }}
        
        function togglePhysics() {{
            physicsEnabled = !physicsEnabled;
            network.setOptions({{physics: {{enabled: physicsEnabled}}}});
            document.getElementById('physics-btn').textContent = 
                physicsEnabled ? 'Stop Physics' : 'Start Physics';
        }}
        
        function adjustSpacing(value) {{
            const spacing = parseInt(value);
            network.setOptions({{
                physics: {{
                    barnesHut: {{
                        springLength: spacing
                    }}
                }}
            }});
            document.getElementById('spacing-value').textContent = spacing;
        }}
        
        function adjustNodeScale(value) {{
            currentNodeScale = parseFloat(value);
            document.getElementById('scale-value').textContent = currentNodeScale.toFixed(1);
            
            // Update node sizes
            const currentNodes = nodes.get();
            const scaledNodes = currentNodes.map(node => ({{
                ...node,
                size: Math.round(node.size * currentNodeScale)
            }}));
            
            nodes.update(scaledNodes);
        }}
        
        function exportData() {{
            const exportData = {{
                nodes: nodes.get(),
                edges: edges.get(),
                timestamp: new Date().toISOString(),
                settings: {{
                    nodeScale: currentNodeScale,
                    physicsEnabled: physicsEnabled,
                    nodeLimit: currentNodeLimit
                }}
            }};
            
            const blob = new Blob([JSON.stringify(exportData, null, 2)], {{
                type: 'application/json'
            }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'enhanced_network_data.json';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }}
    </script>
</body>
</html>
        """
        
        return html_content
    
    def generate_jurisdiction_buttons(self, jurisdictions):
        """Generate HTML for jurisdiction filter buttons including UAE, SA, KW"""
        buttons = []
        for jurisdiction in jurisdictions[:15]:  # Show more jurisdictions now
            flag = self.country_flags.get(jurisdiction, '')
            buttons.append(f'<button class="btn jurisdiction" onclick="filterByJurisdiction(\'{jurisdiction}\')">{flag} {jurisdiction}</button>')
        return '\n'.join(buttons)
    
    def run_enhanced_analysis(self):
        """Run the enhanced analysis with all new features"""
        print("🚀 Starting Enhanced Network Analysis with Performance Controls")
        print("=" * 70)
        
        # Load and process data from final_nodes.csv
        all_nodes, all_edges = self.load_final_nodes_data()
        
        print(f"\n📊 Final Dataset Statistics:")
        print(f"   Total nodes: {len(all_nodes)}")
        print(f"   Total edges: {len(all_edges)}")
        
        if all_nodes:
            # Print distribution by period
            period_counts = Counter(node['period'] for node in all_nodes)
            print(f"   Period distribution: {dict(period_counts)}")
            
            # Print distribution by jurisdiction
            jurisdiction_counts = Counter(node['jurisdiction'] for node in all_nodes)
            top_jurisdictions = jurisdiction_counts.most_common(8)
            print(f"   Top jurisdictions: {dict(top_jurisdictions)}")
            
            # Print actor type distribution
            actor_type_counts = Counter(node['actor_type'] for node in all_nodes)
            print(f"   Actor types: {dict(actor_type_counts)}")
            
            # Print community statistics
            community_counts = Counter(node['global_community'] for node in all_nodes)
            print(f"   Total communities: {len(community_counts)}")
        
        # Create enhanced HTML
        html_content = self.create_enhanced_html(all_nodes, all_edges)
        
        # Save HTML file
        filename = "enhanced_network_analyzer.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print("\n" + "=" * 70)
        print("✅ ENHANCED NETWORK ANALYZER CREATED!")
        print("=" * 70)
        print(f"📁 File: {filename}")
        print(f"📏 File size: {os.path.getsize(filename):,} bytes")
        
        print("\n🎯 NEW ENHANCED FEATURES:")
        print("   🆕 Added UAE, SA, KW jurisdictions with flags")
        print("   🎭 Russian vs International actor classification")
        print("   ⚡ Performance controls with node limit slider (50-500)")
        print("   📊 Performance warning for large networks")
        print("   🔍 Enhanced search includes actor type")
        print("   📈 Smart node limiting by importance ranking")
        print("   🌍 Extended jurisdiction support")
        print("   👥 Advanced community analysis")
        print("   📐 Node scale and spacing controls")
        print("   🏆 Top nodes filtering")
        print("   💾 Enhanced data export")
        print("   🖱️ Detailed node information on click")
        
        print("\n📋 USAGE GUIDE:")
        print(f"   1. Open {filename} in your browser")
        print("   2. Adjust 'Max Nodes' slider if experiencing lag")
        print("   3. Use 'Russian Actors' vs 'International Actors' buttons")
        print("   4. Filter by new jurisdictions: UAE, SA, KW")
        print("   5. Click 'Apply Node Limit' after adjusting slider")
        print("   6. All filters work with performance controls")
        
        print("\n⚡ PERFORMANCE TIPS:")
        print("   • Start with 150 nodes or less for smooth operation")
        print("   • Use period filters to reduce network size")
        print("   • Apply actor type filters for focused analysis")
        print("   • Increase node limit gradually as needed")
        
        return filename

# Execute the enhanced analysis
if __name__ == "__main__":
    print("🌐 Enhanced Network Analyzer - Performance Edition")
    print("Advanced analysis with Russian/International actors and performance controls")
    print("=" * 70)
    
    analyzer = EnhancedNetworkAnalyzer()
    analyzer.run_enhanced_analysis()
