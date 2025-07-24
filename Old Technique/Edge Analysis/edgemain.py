import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from itertools import combinations
from collections import defaultdict, Counter
import warnings
warnings.filterwarnings('ignore')

# Set up plotting parameters
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10
sns.set_style("whitegrid")

class NetworkAnalyzer:
    def __init__(self, datasets):
        """
        Initialize with dictionary of datasets for each time period
        """
        self.datasets = datasets
        self.networks = {}
        self.edge_data = {}
        self.node_data = {}
        
    def create_co_occurrence_edges(self, df, period_name):
        """
        Create co-occurrence edges from dataset based on shared Article_IDs
        """
        print(f"Creating co-occurrence edges for {period_name}...")
        
        # Group by Article_ID to get entities that co-occur
        article_groups = df.groupby('Article_ID')['Entity'].apply(list).reset_index()
        
        # Generate all pairwise combinations of entities within each article
        edges = []
        for _, row in article_groups.iterrows():
            entities = row['Entity']
            if len(entities) > 1:  # Only create edges if more than one entity
                # Generate all combinations of entity pairs
                for entity1, entity2 in combinations(entities, 2):
                    if entity1 != entity2:  # Avoid self-loops
                        edges.append((entity1, entity2))
        
        # Count co-occurrences
        edge_counts = Counter(edges)
        
        # Create edge list with weights
        edge_list = []
        for (entity1, entity2), weight in edge_counts.items():
            edge_list.append({
                'source': entity1,
                'target': entity2,
                'weight': weight,
                'period': period_name
            })
        
        print(f"  Generated {len(edge_list)} unique edges")
        return edge_list
    
    def create_network_graph(self, edge_list, min_weight=1):
        """
        Create NetworkX graph from edge list
        """
        G = nx.Graph()
        
        # Add edges with weights
        for edge in edge_list:
            if edge['weight'] >= min_weight:
                G.add_edge(edge['source'], edge['target'], weight=edge['weight'])
        
        return G
    
    def calculate_network_metrics(self, G, period_name):
        """
        Calculate various network metrics
        """
        metrics = {
            'period': period_name,
            'nodes': G.number_of_nodes(),
            'edges': G.number_of_edges(),
            'density': nx.density(G),
            'avg_clustering': nx.average_clustering(G),
            'num_components': nx.number_connected_components(G)
        }
        
        if G.number_of_nodes() > 0:
            # Get largest connected component
            largest_cc = max(nx.connected_components(G), key=len)
            gcc = G.subgraph(largest_cc)
            
            metrics['largest_component_size'] = len(largest_cc)
            metrics['largest_component_density'] = nx.density(gcc)
            
            if len(largest_cc) > 1:
                metrics['avg_path_length'] = nx.average_shortest_path_length(gcc)
                metrics['diameter'] = nx.diameter(gcc)
            else:
                metrics['avg_path_length'] = 0
                metrics['diameter'] = 0
        
        return metrics
    
    def analyze_all_periods(self, min_weight=2):
        """
        Analyze all time periods
        """
        all_metrics = []
        
        for period_name, df in self.datasets.items():
            print(f"\n=== Processing {period_name} ===")
            
            # Create co-occurrence edges
            edge_list = self.create_co_occurrence_edges(df, period_name)
            self.edge_data[period_name] = edge_list
            
            # Create network graph
            G = self.create_network_graph(edge_list, min_weight)
            self.networks[period_name] = G
            
            # Calculate metrics
            metrics = self.calculate_network_metrics(G, period_name)
            all_metrics.append(metrics)
            
            print(f"  Network: {metrics['nodes']} nodes, {metrics['edges']} edges")
            print(f"  Density: {metrics['density']:.4f}")
            print(f"  Clustering: {metrics['avg_clustering']:.4f}")
        
        return pd.DataFrame(all_metrics)
    
    def plot_network_evolution(self, metrics_df):
        """
        Plot network evolution over time periods
        """
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        periods = metrics_df['period'].tolist()
        
        # Plot 1: Network Size Evolution
        ax1 = axes[0, 0]
        ax1.plot(periods, metrics_df['nodes'], 'o-', linewidth=2, markersize=8, label='Nodes')
        ax1.plot(periods, metrics_df['edges'], 's-', linewidth=2, markersize=8, label='Edges')
        ax1.set_title('Network Size Evolution', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Count')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Network Density
        ax2 = axes[0, 1]
        ax2.plot(periods, metrics_df['density'], 'o-', linewidth=2, markersize=8, color='red')
        ax2.set_title('Network Density Evolution', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Density')
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Clustering Coefficient
        ax3 = axes[1, 0]
        ax3.plot(periods, metrics_df['avg_clustering'], 'o-', linewidth=2, markersize=8, color='green')
        ax3.set_title('Average Clustering Coefficient', fontsize=14, fontweight='bold')
        ax3.set_ylabel('Clustering Coefficient')
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Connected Components
        ax4 = axes[1, 1]
        ax4.plot(periods, metrics_df['num_components'], 'o-', linewidth=2, markersize=8, color='purple')
        ax4.set_title('Number of Connected Components', fontsize=14, fontweight='bold')
        ax4.set_ylabel('Components')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('network_evolution.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_degree_distributions(self):
        """
        Plot degree distributions for all periods
        """
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        axes = axes.flatten()
        
        for i, (period_name, G) in enumerate(self.networks.items()):
            if G.number_of_nodes() > 0:
                degrees = [d for n, d in G.degree()]
                
                axes[i].hist(degrees, bins=20, alpha=0.7, edgecolor='black')
                axes[i].set_title(f'Degree Distribution - {period_name}', fontsize=12, fontweight='bold')
                axes[i].set_xlabel('Degree')
                axes[i].set_ylabel('Frequency')
                axes[i].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('degree_distributions.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_top_entities_by_centrality(self, top_n=10):
        """
        Plot top entities by different centrality measures
        """
        fig, axes = plt.subplots(2, 2, figsize=(20, 15))
        
        centrality_measures = ['degree', 'betweenness', 'closeness', 'eigenvector']
        
        for i, (period_name, G) in enumerate(self.networks.items()):
            if G.number_of_nodes() > 0:
                # Calculate centralities
                degree_cent = nx.degree_centrality(G)
                betweenness_cent = nx.betweenness_centrality(G)
                closeness_cent = nx.closeness_centrality(G)
                
                # Only calculate eigenvector centrality if graph is connected
                if nx.is_connected(G):
                    eigenvector_cent = nx.eigenvector_centrality(G)
                else:
                    # Use largest connected component
                    largest_cc = max(nx.connected_components(G), key=len)
                    gcc = G.subgraph(largest_cc)
                    eigenvector_cent = nx.eigenvector_centrality(gcc)
                
                # Get top entities for degree centrality
                top_entities = sorted(degree_cent.items(), key=lambda x: x[1], reverse=True)[:top_n]
                entities, values = zip(*top_entities)
                
                # Plot
                ax = axes[i]
                bars = ax.barh(range(len(entities)), values)
                ax.set_yticks(range(len(entities)))
                ax.set_yticklabels(entities, fontsize=8)
                ax.set_title(f'Top {top_n} Entities by Degree Centrality - {period_name}', 
                            fontsize=12, fontweight='bold')
                ax.set_xlabel('Degree Centrality')
                ax.grid(True, alpha=0.3)
                
                # Add value labels on bars
                for j, bar in enumerate(bars):
                    width = bar.get_width()
                    ax.text(width + 0.001, bar.get_y() + bar.get_height()/2, 
                           f'{width:.3f}', ha='left', va='center', fontsize=8)
        
        plt.tight_layout()
        plt.savefig('top_entities_centrality.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def analyze_entity_persistence(self):
        """
        Analyze which entities persist across time periods
        """
        # Get all entities from each period
        period_entities = {}
        for period_name, G in self.networks.items():
            period_entities[period_name] = set(G.nodes())
        
        # Find entities that appear in multiple periods
        all_entities = set()
        for entities in period_entities.values():
            all_entities.update(entities)
        
        # Create persistence matrix
        persistence_data = []
        for entity in all_entities:
            row = {'entity': entity}
            for period_name in period_entities.keys():
                row[period_name] = entity in period_entities[period_name]
            persistence_data.append(row)
        
        persistence_df = pd.DataFrame(persistence_data)
        
        # Count persistence
        period_columns = [col for col in persistence_df.columns if col != 'entity']
        persistence_df['periods_count'] = persistence_df[period_columns].sum(axis=1)
        
        # Plot persistence distribution
        plt.figure(figsize=(10, 6))
        persistence_counts = persistence_df['periods_count'].value_counts().sort_index()
        plt.bar(persistence_counts.index, persistence_counts.values, alpha=0.7, edgecolor='black')
        plt.title('Entity Persistence Across Time Periods', fontsize=14, fontweight='bold')
        plt.xlabel('Number of Periods Entity Appears In')
        plt.ylabel('Number of Entities')
        plt.grid(True, alpha=0.3)
        plt.savefig('entity_persistence.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # Show most persistent entities
        most_persistent = persistence_df[persistence_df['periods_count'] >= 3].sort_values('periods_count', ascending=False)
        print("\nMost Persistent Entities (appear in 3+ periods):")
        print(most_persistent[['entity', 'periods_count']].head(20))
        
        return persistence_df
    
    def create_network_visualizations(self, layout_type='spring'):
        """
        Create network visualizations for each period
        """
        fig, axes = plt.subplots(2, 2, figsize=(20, 16))
        axes = axes.flatten()
        
        for i, (period_name, G) in enumerate(self.networks.items()):
            ax = axes[i]
            
            if G.number_of_nodes() > 0:
                # Filter to show only nodes with degree > 1 for clarity
                degrees = dict(G.degree())
                nodes_to_show = [n for n, d in degrees.items() if d > 1]
                G_filtered = G.subgraph(nodes_to_show)
                
                if G_filtered.number_of_nodes() > 0:
                    # Choose layout
                    if layout_type == 'spring':
                        pos = nx.spring_layout(G_filtered, k=0.5, iterations=50)
                    elif layout_type == 'circular':
                        pos = nx.circular_layout(G_filtered)
                    else:
                        pos = nx.kamada_kawai_layout(G_filtered)
                    
                    # Node sizes based on degree
                    node_sizes = [degrees[n] * 50 for n in G_filtered.nodes()]
                    
                    # Draw network
                    nx.draw(G_filtered, pos, ax=ax, 
                           node_size=node_sizes,
                           node_color='lightblue',
                           edge_color='gray',
                           with_labels=True,
                           font_size=8,
                           font_weight='bold',
                           alpha=0.7)
                    
                    ax.set_title(f'Network - {period_name}\n({G.number_of_nodes()} nodes, {G.number_of_edges()} edges)', 
                               fontsize=12, fontweight='bold')
                else:
                    ax.text(0.5, 0.5, f'No connected entities\nin {period_name}', 
                           ha='center', va='center', transform=ax.transAxes, fontsize=12)
            else:
                ax.text(0.5, 0.5, f'No data for {period_name}', 
                       ha='center', va='center', transform=ax.transAxes, fontsize=12)
        
        plt.tight_layout()
        plt.savefig('network_visualizations.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def export_results(self, metrics_df, persistence_df):
        """
        Export analysis results to CSV files
        """
        # Export network metrics
        metrics_df.to_csv('network_metrics_by_period.csv', index=False)
        
        # Export entity persistence
        persistence_df.to_csv('entity_persistence_analysis.csv', index=False)
        
        # Export edge lists for each period
        for period_name, edge_list in self.edge_data.items():
            edge_df = pd.DataFrame(edge_list)
            edge_df.to_csv(f'edges_{period_name.lower().replace("-", "_")}.csv', index=False)
        
        print("Results exported to CSV files:")
        print("- network_metrics_by_period.csv")
        print("- entity_persistence_analysis.csv")
        print("- edges_[period].csv for each time period")

def main():
    """
    Main analysis function
    """
    # Load datasets
    datasets = {
        'Pre-Crimea': pd.read_csv('matched_entities_pre_crimea.csv'),
        'Post-Crimea': pd.read_csv('matched_entities_post_crimea.csv'),
        'Covid': pd.read_csv('matched_entities_covid.csv'),
        'War': pd.read_csv('matched_entities_war.csv')
    }
    
    print("=== ENTITY NETWORK ANALYSIS ===")
    for name, df in datasets.items():
        print(f"{name}: {len(df):,} rows, {df['Entity'].nunique():,} unique entities")
    
    # Initialize analyzer
    analyzer = NetworkAnalyzer(datasets)
    
    # 1. Analyze all periods
    print("\n1. Analyzing all time periods...")
    metrics_df = analyzer.analyze_all_periods(min_weight=2)
    
    # 2. Plot network evolution
    print("\n2. Creating network evolution plots...")
    analyzer.plot_network_evolution(metrics_df)
    
    # 3. Plot degree distributions
    print("\n3. Creating degree distribution plots...")
    analyzer.plot_degree_distributions()
    
    # 4. Plot top entities by centrality
    print("\n4. Creating centrality analysis plots...")
    analyzer.plot_top_entities_by_centrality(top_n=15)
    
    # 5. Analyze entity persistence
    print("\n5. Analyzing entity persistence...")
    persistence_df = analyzer.analyze_entity_persistence()
    
    # 6. Create network visualizations
    print("\n6. Creating network visualizations...")
    analyzer.create_network_visualizations(layout_type='spring')
    
    # 7. Export results
    print("\n7. Exporting results...")
    analyzer.export_results(metrics_df, persistence_df)
    
    print("\n=== ANALYSIS COMPLETE ===")
    print("Generated files:")
    print("- network_evolution.png: Network metrics over time")
    print("- degree_distributions.png: Degree distributions by period")
    print("- top_entities_centrality.png: Most central entities")
    print("- entity_persistence.png: Entity persistence analysis")
    print("- network_visualizations.png: Network graphs")
    print("- CSV files with detailed results")

if __name__ == "__main__":
    main()
