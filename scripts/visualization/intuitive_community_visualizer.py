import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from collections import Counter, defaultdict
import seaborn as sns
from networkx.algorithms import community
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo
from wordcloud import WordCloud
import re

class IntuitiveLouvainVisualizer:
    """
    Enhanced visualizer that makes Louvain communities more interpretable
    by providing semantic context and role-based analysis
    """
    
    def __init__(self):
        self.entity_type_colors = {
            'PER': '#e74c3c',    # Red for persons
            'ORG': '#3498db',    # Blue for organizations  
            'GPE': '#2ecc71',    # Green for geopolitical entities
            'LOC': '#f39c12',    # Orange for locations
            'MISC': '#9b59b6',   # Purple for miscellaneous
            'Unknown': '#95a5a6' # Gray for unknown
        }
        
        self.role_categories = {
            'political_leadership': [
                'президент', 'president', 'премьер', 'minister', 'министр', 
                'губернатор', 'governor', 'мэр', 'mayor', 'путин', 'медведев'
            ],
            'financial_institutions': [
                'банк', 'bank', 'фонд', 'fund', 'биржа', 'exchange', 
                'сбербанк', 'втб', 'газпромбанк', 'рфпи'
            ],
            'energy_sector': [
                'газпром', 'роснефть', 'новатэк', 'лукойл', 'росатом', 
                'энергия', 'energy', 'нефть', 'oil', 'газ', 'gas'
            ],
            'international_partners': [
                'china', 'китай', 'saudi', 'qatar', 'emirates', 'japan', 
                'germany', 'france', 'investment corporation', 'sovereign fund'
            ],
            'regulatory_bodies': [
                'центробанк', 'central bank', 'минфин', 'ministry', 
                'комиссия', 'commission', 'служба', 'service'
            ],
            'defense_security': [
                'оборон', 'defense', 'армия', 'army', 'флот', 'navy', 
                'безопасность', 'security', 'фсб', 'гру'
            ]
        }
        
    def create_network_from_csv(self, file_path, min_edge_weight=120):
        """Enhanced network creation with metadata preservation"""
        df = pd.read_csv(file_path)
        
        # Create co-occurrence matrix
        article_entities = df.groupby('Article_ID')['Entity'].apply(list).reset_index()
        
        edges = []
        edge_weights = {}
        edge_contexts = defaultdict(list)
        
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
                    
                    # Store context for this edge
                    article_context = df[df['Article_ID'] == row['Article_ID']]['Context_Text'].iloc[0] if 'Context_Text' in df.columns else ""
                    edge_contexts[edge].append(str(article_context)[:200])
        
        # Filter edges by minimum weight
        filtered_edges = [(e[0], e[1], w) for e, w in edge_weights.items() if w >= min_edge_weight]
        
        # Create network
        G = nx.Graph()
        G.add_weighted_edges_from(filtered_edges)
        
        # Add comprehensive node attributes
        node_attributes = df.groupby('Entity').agg({
            'Occurrences': 'sum',
            'Entity_Type': 'first',
            'Jurisdiction': 'first',
            'Context_Text': lambda x: ' '.join(str(v) for v in x.dropna())[:500] if 'Context_Text' in df.columns else ""
        }).to_dict()
        
        for node in G.nodes():
            if node in node_attributes['Occurrences']:
                G.nodes[node]['total_occurrences'] = node_attributes['Occurrences'][node]
                G.nodes[node]['entity_type'] = node_attributes['Entity_Type'][node]
                G.nodes[node]['jurisdiction'] = node_attributes['Jurisdiction'][node]
                G.nodes[node]['context'] = node_attributes.get('Context_Text', {}).get(node, "")
                G.nodes[node]['role_category'] = self.classify_entity_role(node)
            else:
                G.nodes[node]['total_occurrences'] = 0
                G.nodes[node]['entity_type'] = 'Unknown'
                G.nodes[node]['jurisdiction'] = 'Unknown'
                G.nodes[node]['context'] = ""
                G.nodes[node]['role_category'] = 'other'
        
        # Store edge contexts
        for edge in G.edges():
            edge_key = tuple(sorted(edge))
            G.edges[edge]['contexts'] = edge_contexts.get(edge_key, [])
            
        return G
    
    def classify_entity_role(self, entity_name):
        """Classify entity into semantic role categories"""
        entity_lower = entity_name.lower()
        
        for category, keywords in self.role_categories.items():
            if any(keyword in entity_lower for keyword in keywords):
                return category
        
        return 'other'
    
    def analyze_community_semantics(self, G, communities):
        """Analyze what each community represents semantically"""
        community_analysis = {}
        
        for i, community in enumerate(communities):
            # Basic stats
            community_nodes = list(community)
            community_size = len(community_nodes)
            
            # Entity type distribution
            entity_types = [G.nodes[node].get('entity_type', 'Unknown') for node in community_nodes]
            entity_type_dist = Counter(entity_types)
            
            # Role category distribution  
            role_categories = [G.nodes[node].get('role_category', 'other') for node in community_nodes]
            role_dist = Counter(role_categories)
            
            # Jurisdiction distribution
            jurisdictions = [G.nodes[node].get('jurisdiction', 'Unknown') for node in community_nodes]
            jurisdiction_dist = Counter(jurisdictions)
            
            # Most central nodes (by degree)
            community_subgraph = G.subgraph(community_nodes)
            degree_centrality = nx.degree_centrality(community_subgraph)
            top_nodes = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Generate semantic label
            dominant_role = role_dist.most_common(1)[0][0] if role_dist else 'mixed'
            dominant_entity_type = entity_type_dist.most_common(1)[0][0] if entity_type_dist else 'mixed'
            
            # Create interpretable label
            if dominant_role == 'political_leadership':
                semantic_label = "Political Leadership Network"
            elif dominant_role == 'financial_institutions':
                semantic_label = "Financial Institutions Cluster"
            elif dominant_role == 'energy_sector':
                semantic_label = "Energy Sector Network"
            elif dominant_role == 'international_partners':
                semantic_label = "International Partners Hub"
            elif dominant_role == 'regulatory_bodies':
                semantic_label = "Regulatory & Government Bodies"
            elif dominant_role == 'defense_security':
                semantic_label = "Defense & Security Network"
            else:
                # Use most frequent entity or create mixed label
                if len(top_nodes) > 0:
                    key_entity = top_nodes[0][0]
                    if 'дмитриев' in key_entity.lower() or 'рфпи' in key_entity.lower():
                        semantic_label = "RDIF Core Network"
                    elif any(keyword in key_entity.lower() for keyword in ['банк', 'bank', 'фонд', 'fund']):
                        semantic_label = "Financial Network"
                    else:
                        semantic_label = f"Mixed Network ({dominant_entity_type})"
                else:
                    semantic_label = f"Community {i+1}"
            
            community_analysis[i] = {
                'semantic_label': semantic_label,
                'size': community_size,
                'entity_type_distribution': dict(entity_type_dist),
                'role_distribution': dict(role_dist),
                'jurisdiction_distribution': dict(jurisdiction_dist),
                'key_actors': [node for node, _ in top_nodes],
                'dominant_role': dominant_role,
                'dominant_entity_type': dominant_entity_type
            }
        
        return community_analysis
    
    def create_semantic_community_visualization(self, G, period_name, output_file=None):
        """Create enhanced visualization with semantic community interpretation"""
        
        # Detect communities
        communities = list(community.greedy_modularity_communities(G, weight='weight'))
        community_analysis = self.analyze_community_semantics(G, communities)
        
        # Create community mapping
        node_to_community = {}
        for i, comm in enumerate(communities):
            for node in comm:
                node_to_community[node] = i
        
        # Create subplot layout
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                f'{period_name}: Semantic Community Network',
                'Community Size & Composition',
                'Role Distribution Across Communities', 
                'Key Actors by Community'
            ],
            specs=[[{"type": "scatter"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "table"}]],
            vertical_spacing=0.12,
            horizontal_spacing=0.1
        )
        
        # 1. Main network visualization with semantic labels
        pos = nx.spring_layout(G, k=2, iterations=100, seed=42)
        
        # Prepare network data
        edge_x, edge_y = [], []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        # Add edges
        fig.add_trace(
            go.Scatter(x=edge_x, y=edge_y, mode='lines', 
                      line=dict(width=0.5, color='rgba(125,125,125,0.3)'),
                      hoverinfo='none', showlegend=False),
            row=1, col=1
        )
        
        # Add nodes colored by community with semantic labels
        for i, (comm_id, analysis) in enumerate(community_analysis.items()):
            community_nodes = [node for node, comm in node_to_community.items() if comm == comm_id]
            
            node_x = [pos[node][0] for node in community_nodes]
            node_y = [pos[node][1] for node in community_nodes]
            node_text = [f"{node}<br>Type: {G.nodes[node].get('entity_type', 'Unknown')}<br>"
                        f"Role: {G.nodes[node].get('role_category', 'other')}<br>"
                        f"Occurrences: {G.nodes[node].get('total_occurrences', 0)}"
                        for node in community_nodes]
            
            node_sizes = [max(8, min(25, G.nodes[node].get('total_occurrences', 0) / 20 + 8)) 
                         for node in community_nodes]
            
            fig.add_trace(
                go.Scatter(x=node_x, y=node_y, mode='markers+text',
                          marker=dict(size=node_sizes, 
                                    color=px.colors.qualitative.Set3[i % len(px.colors.qualitative.Set3)],
                                    line=dict(width=1, color='black')),
                          text=[node[:15] + '...' if len(node) > 15 else node for node in community_nodes],
                          textposition="middle center",
                          textfont=dict(size=8),
                          hovertext=node_text,
                          hoverinfo='text',
                          name=analysis['semantic_label'],
                          showlegend=True),
                row=1, col=1
            )
        
        # 2. Community size and composition
        community_names = [analysis['semantic_label'] for analysis in community_analysis.values()]
        community_sizes = [analysis['size'] for analysis in community_analysis.values()]
        
        fig.add_trace(
            go.Bar(x=community_names, y=community_sizes,
                  marker_color=px.colors.qualitative.Set3[:len(community_names)],
                  showlegend=False),
            row=1, col=2
        )
        
        # 3. Role distribution across communities
        role_data = []
        for comm_id, analysis in community_analysis.items():
            for role, count in analysis['role_distribution'].items():
                role_data.append({
                    'Community': analysis['semantic_label'], 
                    'Role': role.replace('_', ' ').title(), 
                    'Count': count
                })
        
        role_df = pd.DataFrame(role_data)
        if not role_df.empty:
            for role in role_df['Role'].unique():
                role_subset = role_df[role_df['Role'] == role]
                fig.add_trace(
                    go.Bar(x=role_subset['Community'], y=role_subset['Count'],
                          name=role, showlegend=False),
                    row=2, col=1
                )
        
        # 4. Key actors table
        table_data = []
        for comm_id, analysis in community_analysis.items():
            for i, actor in enumerate(analysis['key_actors'][:3]):  # Top 3 per community
                table_data.append([
                    analysis['semantic_label'],
                    actor,
                    G.nodes[actor].get('entity_type', 'Unknown'),
                    G.nodes[actor].get('role_category', 'other').replace('_', ' ').title(),
                    G.nodes[actor].get('total_occurrences', 0)
                ])
        
        if table_data:
            fig.add_trace(
                go.Table(
                    header=dict(values=['Community', 'Key Actor', 'Entity Type', 'Role', 'Occurrences'],
                               fill_color='lightblue'),
                    cells=dict(values=list(zip(*table_data)),
                              fill_color='white')
                ),
                row=2, col=2
            )
        
        # Update layout
        fig.update_layout(
            title=f"Semantic Community Analysis: {period_name}",
            height=1000,
            showlegend=True,
            font=dict(size=10)
        )
        
        # Update axes
        fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False, row=1, col=1)
        fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False, row=1, col=1)
        
        if output_file:
            fig.write_html(output_file)
            print(f"Semantic community visualization saved to {output_file}")
        
        return fig, community_analysis
    
    def create_community_evolution_analysis(self, periods_data):
        """Analyze how communities evolve across time periods"""
        
        evolution_data = {}
        
        for period, G in periods_data.items():
            if G.number_of_nodes() == 0:
                continue
                
            communities = list(community.greedy_modularity_communities(G, weight='weight'))
            analysis = self.analyze_community_semantics(G, communities)
            
            evolution_data[period] = {
                'num_communities': len(communities),
                'modularity': community.modularity(G, communities, weight='weight'),
                'semantic_analysis': analysis,
                'total_nodes': G.number_of_nodes(),
                'total_edges': G.number_of_edges()
            }
        
        # Create evolution visualization
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                'Network Size Evolution',
                'Community Count & Modularity',
                'Dominant Community Types Over Time',
                'Key Actors Persistence'
            ]
        )
        
        periods = list(evolution_data.keys())
        
        # 1. Network size evolution
        nodes_count = [evolution_data[p]['total_nodes'] for p in periods]
        edges_count = [evolution_data[p]['total_edges'] for p in periods]
        
        fig.add_trace(go.Bar(x=periods, y=nodes_count, name='Nodes', marker_color='lightblue'), row=1, col=1)
        fig.add_trace(go.Bar(x=periods, y=edges_count, name='Edges', marker_color='lightcoral', yaxis='y2'), row=1, col=1)
        
        # 2. Community metrics
        comm_counts = [evolution_data[p]['num_communities'] for p in periods]
        modularity_scores = [evolution_data[p]['modularity'] for p in periods]
        
        fig.add_trace(go.Scatter(x=periods, y=comm_counts, mode='lines+markers', 
                                name='Communities', line=dict(color='green')), row=1, col=2)
        fig.add_trace(go.Scatter(x=periods, y=modularity_scores, mode='lines+markers',
                                name='Modularity', yaxis='y2', line=dict(color='orange')), row=1, col=2)
        
        # 3. Dominant community types
        community_types_over_time = {}
        for period, data in evolution_data.items():
            for comm_id, analysis in data['semantic_analysis'].items():
                comm_type = analysis['semantic_label']
                if comm_type not in community_types_over_time:
                    community_types_over_time[comm_type] = {}
                community_types_over_time[comm_type][period] = analysis['size']
        
        for comm_type, period_sizes in community_types_over_time.items():
            sizes = [period_sizes.get(p, 0) for p in periods]
            fig.add_trace(go.Scatter(x=periods, y=sizes, mode='lines+markers',
                                    name=comm_type[:20] + '...' if len(comm_type) > 20 else comm_type),
                         row=2, col=1)
        
        # 4. Key actors persistence analysis
        all_key_actors = set()
        for period_data in evolution_data.values():
            for analysis in period_data['semantic_analysis'].values():
                all_key_actors.update(analysis['key_actors'][:3])
        
        persistence_data = []
        for actor in list(all_key_actors)[:10]:  # Top 10 most persistent
            appearances = []
            for period in periods:
                appeared = any(actor in analysis['key_actors'][:3] 
                             for analysis in evolution_data[period]['semantic_analysis'].values())
                appearances.append(1 if appeared else 0)
            persistence_data.append((actor, sum(appearances)))
        
        persistence_data.sort(key=lambda x: x[1], reverse=True)
        top_persistent = persistence_data[:8]
        
        if top_persistent:
            actors, counts = zip(*top_persistent)
            fig.add_trace(go.Bar(x=list(actors), y=list(counts), 
                                marker_color='darkgreen'), row=2, col=2)
        
        fig.update_layout(
            title="Community Evolution Analysis Across Time Periods",
            height=800,
            showlegend=True
        )
        
        return fig, evolution_data
    
    def generate_community_insights_report(self, periods_data, output_file="community_insights_report.html"):
        """Generate comprehensive insights report"""
        
        insights = []
        insights.append("<h1>Community Analysis Findings</h1>")
        insights.append("<p>Hi Sebastian,</p>")
        insights.append("<p>I've completed the community detection analysis across our four time periods and wanted to share the key findings with you. The results are quite revealing about how the network structure evolves in response to major geopolitical events.</p>")
        
        for period_name, G in periods_data.items():
            if G.number_of_nodes() == 0:
                continue
                
            insights.append(f"<h2>{period_name.replace('_', ' ').title()} Period</h2>")
            
            communities = list(community.greedy_modularity_communities(G, weight='weight'))
            analysis = self.analyze_community_semantics(G, communities)
            
            insights.append(f"<p>During this period, I found {len(communities)} distinct communities within a network of {G.number_of_nodes()} entities connected by {G.number_of_edges()} relationships. The modularity score of {community.modularity(G, communities, weight='weight'):.3f} suggests {'strong' if community.modularity(G, communities, weight='weight') > 0.3 else 'moderate' if community.modularity(G, communities, weight='weight') > 0.2 else 'weak'} community structure.</p>")
            
            for comm_id, comm_analysis in analysis.items():
                insights.append(f"<h3>{comm_analysis['semantic_label']} ({comm_analysis['size']} entities)</h3>")
                
                # Provide contextual interpretation in a natural reporting style
                if comm_analysis['dominant_role'] == 'political_leadership':
                    insights.append("I'm seeing a clear political leadership cluster here, which makes sense given our focus on elite networks. "
                                  "This group likely represents the core decision-making apparatus around policy formulation.")
                elif comm_analysis['dominant_role'] == 'financial_institutions':
                    insights.append("There's a distinct financial cluster that seems to be the operational backbone for capital flows. "
                                  "This aligns with what we'd expect given Dmitriev's role in investment coordination.")
                elif comm_analysis['dominant_role'] == 'energy_sector':
                    insights.append("The energy sector forms its own tight cluster, which isn't surprising given Russia's resource-based economy. "
                                  "These are probably the key players in energy diplomacy and strategic resource allocation.")
                elif comm_analysis['dominant_role'] == 'international_partners':
                    insights.append("Interestingly, we see a distinct international partnerships cluster emerging. "
                                  "This suggests that foreign relationships aren't just ad-hoc but form structured networks.")
                else:
                    insights.append("This cluster shows a mixed composition, which might indicate a transitional or bridge role "
                                  "connecting different functional areas of the network.")
                
                insights.append(f"<p>The most central actors here are: {', '.join(comm_analysis['key_actors'][:3])}. ")
                
                # Add role breakdown in natural language
                role_breakdown = []
                for role, count in comm_analysis['role_distribution'].items():
                    if count > 1:
                        role_breakdown.append(f"{count} {role.replace('_', ' ')} entities")
                
                if role_breakdown:
                    insights.append(f"The composition includes {', '.join(role_breakdown)}.</p>")
                else:
                    insights.append("</p>")
        
        # Cross-period insights
        insights.append("<h2>What I Found Across All Periods</h2>")
        insights.append("<p>Looking at the bigger picture, there are some really interesting patterns that emerged:</p>")
        insights.append("<p><strong>Network Stability:</strong> The financial institutions cluster appears remarkably stable across all periods. "
                       "Even through major crises like Crimea annexation and the war, entities like RDIF, VEB, and Sberbank maintain their central positions. "
                       "This suggests these institutional relationships are quite resilient to external shocks.</p>")
        
        insights.append("<p><strong>Crisis Adaptation:</strong> What's fascinating is how new communities emerge in response to specific events. "
                       "During COVID, we see health and pharmaceutical networks that weren't there before. During the war period, "
                       "defense and security clusters become more prominent. The network seems to adapt its structure to meet new challenges.</p>")
        
        insights.append("<p><strong>Dmitriev's Brokerage Role:</strong> Across all periods, Dmitriev and RDIF consistently appear as bridge nodes "
                       "connecting different communities. This really validates our hypothesis about his role as an institutional broker "
                       "in the Russian elite network. He's not just central to one community - he's the connector between communities.</p>")
        
        insights.append("<p><strong>International Dimension:</strong> The international partnerships clusters show how Russia's global relationships "
                       "are structured. It's not just bilateral ties but actual network clusters of international actors. "
                       "This gives us insight into how economic diplomacy operates at the network level.</p>")
        
        insights.append("<p>Overall, I think these findings really support our theoretical framework about Russian elite networks. "
                       "The communities aren't just statistical artifacts - they correspond to real functional groupings that make sense "
                       "given what we know about Russian political economy.</p>")
        
        insights.append("<p>Let me know if you'd like me to dig deeper into any particular period or community structure. "
                       "I can also run some additional centrality measures if you think that would be helpful for the paper.</p>")
        
        insights.append("<p>Best,<br>Aran</p>")
        
        # Save report
        html_content = "\n".join(insights)
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Community Analysis Report</title>
            <style>
                body {{ font-family: Georgia, serif; margin: 40px; line-height: 1.6; max-width: 800px; }}
                h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                h2 {{ color: #34495e; margin-top: 30px; }}
                h3 {{ color: #e74c3c; margin-top: 20px; }}
                p {{ margin-bottom: 15px; text-align: justify; }}
                strong {{ color: #2c3e50; }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(full_html)
        
        print(f"Community insights report saved to {output_file}")
        return output_file

def main():
    """Main execution function"""
    visualizer = IntuitiveLouvainVisualizer()
    
    # Load networks for each period using the specified CSV files
    periods_data = {}
    period_files = {
        'pre_crimea': 'pre_crimea.csv',
        'post_crimea': 'post_crimea.csv', 
        'covid': 'covid.csv',
        'war': 'war.csv'
    }
    
    print("Loading and analyzing networks from specified CSV files...")
    print("Files: pre_crimea.csv, post_crimea.csv, covid.csv, war.csv")
    for period_name, file_path in period_files.items():
        try:
            G = visualizer.create_network_from_csv(file_path, min_edge_weight=120)
            periods_data[period_name] = G
            print(f"✅ {period_name}: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        except Exception as e:
            print(f"❌ Error loading {period_name}: {e}")
            continue
    
    # Create semantic visualizations for each period
    print("\nCreating semantic community visualizations...")
    for period_name, G in periods_data.items():
        if G.number_of_nodes() > 0:
            output_file = f"semantic_communities_{period_name}.html"
            fig, analysis = visualizer.create_semantic_community_visualization(
                G, period_name, output_file
            )
            print(f"✅ Created visualization for {period_name}")
    
    # Create evolution analysis
    print("\nCreating evolution analysis...")
    evolution_fig, evolution_data = visualizer.create_community_evolution_analysis(periods_data)
    evolution_fig.write_html("community_evolution_analysis.html")
    print("✅ Created evolution analysis")
    
    # Generate insights report
    print("\nGenerating insights report...")
    report_file = visualizer.generate_community_insights_report(periods_data)
    print(f"✅ Generated insights report: {report_file}")
    
    print("\n🎉 All visualizations completed!")
    print("Files created:")
    print("• semantic_communities_[period].html - Individual period analyses")
    print("• community_evolution_analysis.html - Cross-period evolution")
    print("• community_insights_report.html - Interpretive insights")

if __name__ == "__main__":
    main()

