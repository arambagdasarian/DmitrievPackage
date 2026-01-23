import pandas as pd
import networkx as nx
import community as louvain  # pip install python-louvain
from collections import Counter, defaultdict
import numpy as np

def create_edges_from_nodes(nodes_file_path, edges_file_path):
    """
    Create edges from nodes based on entity co-occurrence within articles
    """
    df = pd.read_csv(nodes_file_path)
    
    # Group entities by Article_ID to find co-occurrences
    grouped = df.groupby('Article_ID')['Entity'].apply(list)
    
    # Create edges based on co-occurrence of entities within the same article
    edge_weights = defaultdict(int)
    
    for entities in grouped:
        # Create all unique pairs of entities in the article (undirected edges)
        unique_entities = list(set(entities))
        n = len(unique_entities)
        
        # Generate all possible pairs
        for i in range(n):
            for j in range(i+1, n):
                # Sort to ensure consistent edge representation
                edge = tuple(sorted([unique_entities[i], unique_entities[j]]))
                edge_weights[edge] += 1
    
    # Convert to DataFrame
    edges_df = pd.DataFrame([
        {'src': src, 'dst': dst, 'weight': weight} 
        for (src, dst), weight in edge_weights.items()
    ])
    
    # Save edges to CSV
    edges_df.to_csv(edges_file_path, index=False)
    print(f"Created {len(edges_df)} edges from {edges_file_path}")
    
    return edges_df

def run_robust_louvain(edges_csv_path, output_prefix=""):
    """
    Run robust Louvain community detection with stability evaluation
    """
    # 1. Load and build graph
    edges = pd.read_csv(edges_csv_path)
    G = nx.from_pandas_edgelist(edges, 'src', 'dst', 
                               edge_attr='weight', 
                               create_using=nx.Graph())
    
    print(f"Graph loaded: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    # Handle isolated nodes or empty graphs
    if G.number_of_nodes() == 0:
        print("Warning: Empty graph - no analysis possible")
        return None, None, 0.0
    
    if G.number_of_edges() == 0:
        print("Warning: No edges - creating singleton communities")
        singleton_partition = {node: i for i, node in enumerate(G.nodes())}
        return G, singleton_partition, 0.0
    
    # 2. Run Louvain multiple times for stability
    runs = []
    modularities = []
    
    for i in range(10):
        partition = louvain.best_partition(G, weight='weight', 
                                         resolution=1.0, 
                                         random_state=i)
        runs.append(partition)
        mod = louvain.modularity(partition, G, weight='weight')
        modularities.append(mod)
    
    # 3. Consensus via majority vote
    consensus_partition = {}
    for node in G.nodes():
        labels = [run[node] for run in runs if node in run]
        if labels:
            consensus_partition[node] = Counter(labels).most_common(1)[0][0]
        else:
            consensus_partition[node] = 0  # fallback for isolated nodes
    
    # Set community attributes
    nx.set_node_attributes(G, consensus_partition, 'community')
    
    # 4. Calculate final modularity
    final_modularity = louvain.modularity(consensus_partition, G, weight='weight')
    
    # Results summary
    num_communities = len(set(consensus_partition.values()))
    avg_modularity = np.mean(modularities)
    std_modularity = np.std(modularities)
    
    print(f"\n{output_prefix.upper()} PERIOD RESULTS:")
    print(f"Communities detected: {num_communities}")
    print(f"Average modularity: {avg_modularity:.3f}")
    print(f"Consensus modularity: {final_modularity:.3f}")
    print(f"Modularity stability (std): {std_modularity:.3f}")
    
    # Save detailed results
    community_df = pd.DataFrame([
        {'node': node, 'community': community} 
        for node, community in consensus_partition.items()
    ])
    community_df.to_csv(f"{output_prefix}_communities.csv", index=False)
    
    # Save community statistics
    community_sizes = Counter(consensus_partition.values())
    stats_df = pd.DataFrame([
        {'community': comm, 'size': size} 
        for comm, size in community_sizes.items()
    ]).sort_values('size', ascending=False)
    stats_df.to_csv(f"{output_prefix}_community_stats.csv", index=False)
    
    return G, consensus_partition, final_modularity

def analyze_temporal_communities():
    """
    Complete temporal analysis workflow
    """
    periods = ['pre_crimea', 'post_crimea', 'covid', 'war']
    results = {}
    temporal_summary = []
    
    print("TEMPORAL ENTITY NETWORK ANALYSIS")
    print("="*60)
    
    for period in periods:
        print(f"\n{'='*20} {period.upper()} PERIOD {'='*20}")
        
        # Step 1: Create edges from nodes
        nodes_file = f"{period}.csv"
        edges_file = f"{period}_edges.csv"
        
        try:
            edges_df = create_edges_from_nodes(nodes_file, edges_file)
            
            # Step 2: Run Louvain community detection
            G, partition, modularity = run_robust_louvain(edges_file, period)
            
            if G is not None:
                results[period] = {
                    'graph': G, 
                    'partition': partition, 
                    'modularity': modularity,
                    'nodes': G.number_of_nodes(),
                    'edges': G.number_of_edges(),
                    'communities': len(set(partition.values())) if partition else 0
                }
                
                temporal_summary.append({
                    'period': period,
                    'nodes': G.number_of_nodes(),
                    'edges': G.number_of_edges(),
                    'communities': len(set(partition.values())),
                    'modularity': modularity,
                    'avg_community_size': G.number_of_nodes() / len(set(partition.values())) if partition else 0
                })
            else:
                print(f"Skipping {period} due to insufficient data")
                
        except FileNotFoundError:
            print(f"Error: {nodes_file} not found. Please ensure all period files exist.")
        except Exception as e:
            print(f"Error processing {period}: {str(e)}")
    
    # Create temporal summary
    if temporal_summary:
        summary_df = pd.DataFrame(temporal_summary)
        summary_df.to_csv("temporal_analysis_summary.csv", index=False)
        
        print(f"\n{'='*20} TEMPORAL SUMMARY {'='*20}")
        print(summary_df.to_string(index=False))
        
        # Find period with highest modularity
        best_period = summary_df.loc[summary_df['modularity'].idxmax()]
        print(f"\nPeriod with strongest community structure: {best_period['period'].upper()}")
        print(f"Modularity: {best_period['modularity']:.3f}")
    
    return results

# Execute the complete analysis
if __name__ == "__main__":
    results = analyze_temporal_communities()
