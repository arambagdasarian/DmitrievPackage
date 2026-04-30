"""
Network Change Analysis

Documents entities joining and leaving the network after the Pre-Crimea period.
"""

import os
import pandas as pd
import networkx as nx


def create_network_from_csv(file_path, min_edge_weight=20):
    """Create network from CSV file"""
    df = pd.read_csv(file_path)
    
    article_entities = df.groupby('Article_ID')['Entity'].apply(list).reset_index()
    
    edge_weights = {}
    for _, row in article_entities.iterrows():
        entities = row['Entity']
        if len(entities) < 2:
            continue
            
        for i in range(len(entities)):
            for j in range(i + 1, len(entities)):
                entity1, entity2 = entities[i], entities[j]
                edge = tuple(sorted([entity1, entity2]))
                edge_weights[edge] = edge_weights.get(edge, 0) + 1
    
    filtered_edges = [(e[0], e[1], w) for e, w in edge_weights.items() if w >= min_edge_weight]
    
    G = nx.Graph()
    G.add_weighted_edges_from(filtered_edges)
    
    # Get entity metadata
    entity_metadata = {}
    for entity in G.nodes():
        entity_df = df[df['Entity'] == entity]
        if len(entity_df) > 0:
            entity_metadata[entity] = {
                'sector': entity_df['Sector'].mode()[0] if len(entity_df['Sector'].mode()) > 0 else 'Unknown',
                'entity_type': entity_df['Entity_Type'].mode()[0] if len(entity_df['Entity_Type'].mode()) > 0 else 'Unknown',
                'state_private': entity_df['State/Private'].mode()[0] if 'State/Private' in entity_df.columns and len(entity_df['State/Private'].mode()) > 0 else 'Unknown',
                'total_occurrences': entity_df['Occurrences'].sum(),
                'jurisdiction': entity_df['Jurisdiction'].mode()[0] if 'Jurisdiction' in entity_df.columns and len(entity_df['Jurisdiction'].mode()) > 0 else 'Unknown'
            }
    
    return G, entity_metadata


def analyze_network_changes(output_dir='final visuals'):
    """Analyze entities joining and leaving the network"""
    
    print("="*80)
    print("NETWORK CHANGE ANALYSIS")
    print("="*80)
    
    period_files = {
        'Pre-Crimea': 'data/periods/pre_crimea.csv',
        'Post-Crimea': 'data/periods/post_crimea.csv',
        'COVID': 'data/periods/covid.csv',
        'War': 'data/periods/war.csv'
    }
    
    # Load all networks
    networks = {}
    metadata = {}
    
    for period_name, file_path in period_files.items():
        if not os.path.exists(file_path):
            print(f"⚠ Warning: {file_path} not found, skipping...")
            continue
        
        G, meta = create_network_from_csv(file_path, min_edge_weight=20)
        networks[period_name] = G
        metadata[period_name] = meta
        print(f"✓ Loaded {period_name}: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    # Get Pre-Crimea baseline
    baseline_nodes = set(networks['Pre-Crimea'].nodes())
    
    # Analyze each subsequent period
    results = []
    
    for period_name in ['Post-Crimea', 'COVID', 'War']:
        if period_name not in networks:
            continue
        
        current_nodes = set(networks[period_name].nodes())
        
        # New entities (joined)
        new_entities = current_nodes - baseline_nodes
        
        # Entities that left (were in previous period but not in current)
        left_entities = baseline_nodes - current_nodes
        
        print(f"\n{period_name}:")
        print(f"  New entities: {len(new_entities)}")
        print(f"  Left entities: {len(left_entities)}")
        
        # Document new entities
        for entity in new_entities:
            if entity in metadata[period_name]:
                meta = metadata[period_name][entity]
                results.append({
                    'Period': period_name,
                    'Change Type': 'Joined',
                    'Entity': entity,
                    'Sector': meta['sector'],
                    'Entity Type': meta['entity_type'],
                    'State/Private': meta['state_private'],
                    'Jurisdiction': meta['jurisdiction'],
                    'Total Occurrences': meta['total_occurrences']
                })
        
        # Document entities that left
        # Check if they existed in Pre-Crimea
        for entity in left_entities:
            if entity in metadata['Pre-Crimea']:
                meta = metadata['Pre-Crimea'][entity]
                results.append({
                    'Period': period_name,
                    'Change Type': 'Left',
                    'Entity': entity,
                    'Sector': meta['sector'],
                    'Entity Type': meta['entity_type'],
                    'State/Private': meta['state_private'],
                    'Jurisdiction': meta['jurisdiction'],
                    'Total Occurrences': meta['total_occurrences']
                })
    
    # Create DataFrame
    df_changes = pd.DataFrame(results)
    
    # Save to CSV
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'network_entity_changes.csv')
    df_changes.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"\n✓ Saved: {output_file}")
    
    # Create summary statistics
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    
    for period in ['Post-Crimea', 'COVID', 'War']:
        period_changes = df_changes[df_changes['Period'] == period]
        joined = len(period_changes[period_changes['Change Type'] == 'Joined'])
        left = len(period_changes[period_changes['Change Type'] == 'Left'])
        
        print(f"\n{period}:")
        print(f"  Entities joined: {joined}")
        print(f"  Entities left: {left}")
        print(f"  Net change: {joined - left:+d}")
        
        # Top sectors joining
        if joined > 0:
            joined_sectors = period_changes[period_changes['Change Type'] == 'Joined']['Sector'].value_counts()
            print(f"  Top sectors joining:")
            for sector, count in joined_sectors.head(5).items():
                print(f"    - {sector}: {count}")
    
    # Create detailed report
    report_file = os.path.join(output_dir, 'network_entity_changes_report.txt')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("NETWORK ENTITY CHANGES REPORT\n")
        f.write("="*80 + "\n\n")
        f.write("This document tracks entities joining and leaving Dmitriev's network\n")
        f.write("after the Pre-Crimea period (2012-2014).\n\n")
        f.write(f"Baseline Period: Pre-Crimea ({len(baseline_nodes)} entities)\n")
        f.write(f"Analysis Date: {pd.Timestamp.now().strftime('%Y-%m-%d')}\n")
        f.write("\n" + "="*80 + "\n\n")
        
        for period in ['Post-Crimea', 'COVID', 'War']:
            period_changes = df_changes[df_changes['Period'] == period]
            
            f.write(f"\n{'='*80}\n")
            f.write(f"{period} Period\n")
            f.write(f"{'='*80}\n\n")
            
            # New entities
            joined = period_changes[period_changes['Change Type'] == 'Joined'].sort_values('Total Occurrences', ascending=False)
            f.write(f"NEW ENTITIES JOINING THE NETWORK ({len(joined)} total):\n")
            f.write("-"*80 + "\n\n")
            
            for idx, row in joined.iterrows():
                f.write(f"• {row['Entity']}\n")
                f.write(f"  Sector: {row['Sector']}\n")
                f.write(f"  Type: {row['Entity Type']}\n")
                f.write(f"  State/Private: {row['State/Private']}\n")
                f.write(f"  Jurisdiction: {row['Jurisdiction']}\n")
                f.write(f"  Occurrences: {row['Total Occurrences']:,}\n\n")
            
            # Entities that left
            left = period_changes[period_changes['Change Type'] == 'Left'].sort_values('Total Occurrences', ascending=False)
            f.write(f"\n\nENTITIES LEAVING THE NETWORK ({len(left)} total):\n")
            f.write("-"*80 + "\n\n")
            
            for idx, row in left.iterrows():
                f.write(f"• {row['Entity']}\n")
                f.write(f"  Sector: {row['Sector']}\n")
                f.write(f"  Type: {row['Entity Type']}\n")
                f.write(f"  State/Private: {row['State/Private']}\n")
                f.write(f"  Jurisdiction: {row['Jurisdiction']}\n")
                f.write(f"  Occurrences in Pre-Crimea: {row['Total Occurrences']:,}\n\n")
    
    print(f"\n✓ Saved detailed report: {report_file}")
    
    return df_changes


if __name__ == "__main__":
    df_changes = analyze_network_changes()
    print("\n" + "="*80)
    print("✓ Network change analysis complete!")
    print("="*80)
