# Enhanced Network Analyzer V2 - Scraping-Based Analysis

## Overview

This enhanced version of the network analyzer has been specifically designed to handle the context of scraping-based datasets, where data is collected from articles mentioning Kirill Dmitriev. The analysis focuses on co-occurrence networks where entities that appear together in the same articles are connected.

## Key Enhancements

### 1. Co-occurrence Network Construction

**Problem**: The original code didn't properly account for the scraping-based nature of the dataset.

**Solution**: 
- **Article_ID Grouping**: Entities are grouped by Article_ID to identify co-occurrences
- **Edge Weight Calculation**: Edge weights represent the frequency of entities appearing together in the same articles
- **Proper Network Structure**: Networks are built based on actual co-occurrence patterns rather than arbitrary connections

```python
def calculate_co_occurrence_network(self, period_df):
    """
    Calculate co-occurrence network based on entities appearing together in articles.
    This is the core network construction method for scraping-based data.
    """
    edges_list = []
    entity_details = {}
    
    # Group by Article_ID to find co-occurrences
    for article_id, group in period_df.groupby('Article_ID'):
        entities = group['Entity'].unique().tolist()
        if len(entities) < 2:
            continue
        
        # Create entity pairs for co-occurrence
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                if entity1 != entity2:
                    edge = tuple(sorted([entity1, entity2]))
                    edges_list.append(edge)
    
    return edges_list, entity_details
```

### 2. Enhanced Network Metrics

**Problem**: Standard centrality measures weren't appropriate for co-occurrence networks.

**Solution**:
- **Article Coverage**: Tracks how many articles mention each entity
- **Co-occurrence Strength**: Average weight of connections for each entity
- **Eigenvector Centrality**: Measures influence in the network
- **Multi-metric Importance**: Combines multiple metrics for comprehensive importance scoring

```python
def calculate_network_metrics(self, G, entity_details):
    """
    Calculate network metrics appropriate for co-occurrence networks.
    Enhanced for scraping-based dataset context.
    """
    metrics = {}
    
    # Additional metrics for co-occurrence networks
    metrics['article_coverage'] = {}
    metrics['co_occurrence_strength'] = {}
    
    for node in G.nodes():
        # Article coverage: how many articles mention this entity
        metrics['article_coverage'][node] = entity_details.get(node, {}).get('article_count', 0)
        
        # Co-occurrence strength: average weight of edges
        neighbors = list(G.neighbors(node))
        if neighbors:
            avg_weight = sum(G[node][neighbor]['weight'] for neighbor in neighbors) / len(neighbors)
            metrics['co_occurrence_strength'][node] = avg_weight
        else:
            metrics['co_occurrence_strength'][node] = 0
    
    return metrics
```

### 3. Dataset Context Awareness

**Problem**: The analyzer didn't understand the scraping-based data structure.

**Solution**:
- **Article_ID Processing**: Proper handling of article-based grouping
- **Occurrences Tracking**: Accurate counting of entity mentions across articles
- **Context-Appropriate Filtering**: Filtering based on the actual data structure

### 4. Performance Optimizations

**Problem**: Large datasets (852,866 rows) caused performance issues.

**Solution**:
- **Increased Node Limits**: Up to 2000 nodes per view (from 1054)
- **Smart Physics Management**: Auto-disables physics for networks with >500 nodes
- **Efficient Edge Processing**: Optimized edge weight calculations
- **Memory Management**: Better handling of large datasets

### 5. Accurate Calculations

**Problem**: Network metrics weren't appropriate for co-occurrence networks.

**Solution**:
- **Proper Edge Weighting**: Edge weights represent actual co-occurrence frequency
- **Enhanced Centrality**: Centrality measures optimized for co-occurrence patterns
- **Community Detection**: Louvain algorithm with appropriate resolution for co-occurrence networks

### 6. User Interface Enhancements

**Problem**: Interface didn't reflect the scraping-based context.

**Solution**:
- **Dataset Context Display**: Shows information about the scraping-based nature
- **Enhanced Node Details**: Displays article coverage and co-occurrence strength
- **Improved Filtering**: Filter options appropriate for co-occurrence networks

## Technical Improvements

### Network Construction
```python
# Enhanced co-occurrence calculation
for article_id, group in period_df.groupby('Article_ID'):
    entities = group['Entity'].unique().tolist()
    if len(entities) < 2:
        continue
    
    # Create entity pairs for co-occurrence
    for i, entity1 in enumerate(entities):
        for entity2 in entities[i+1:]:
            if entity1 != entity2:
                edge = tuple(sorted([entity1, entity2]))
                edges_list.append(edge)
```

### Importance Calculation
```python
# Enhanced importance calculation for co-occurrence networks
importance = (cent * 0.25 + betw * 0.2 + clos * 0.2 + eigen * 0.15 + 
            (article_cov / 100) * 0.1 + (co_occur_strength / 10) * 0.1)
```

### Performance Optimization
```python
# Smart physics management
const MAX_NODES_PHYSICS = 500; // Disable physics above this threshold

# Efficient node limiting
const sortedNodes = nodeData
    .sort((a, b) => {
        const scoreA = (a.importance || 0) * 0.7 + (a.degree || 0) * 0.3;
        const scoreB = (b.importance || 0) * 0.7 + (b.degree || 0) * 0.3;
        return scoreB - scoreA;
    })
    .slice(0, limit);
```

## Dataset Context Understanding

### Data Structure
- **Article_ID**: Unique identifier for each scraped article
- **Entity**: Named entities extracted from articles
- **Occurrences**: Count of entity mentions across all articles
- **Jurisdiction**: Country/jurisdiction classification (RUS for Russian entities)
- **Date**: Article publication date for temporal analysis

### Network Interpretation
- **Nodes**: Entities mentioned in articles
- **Edges**: Co-occurrence relationships (entities appearing in same articles)
- **Edge Weights**: Frequency of co-occurrence
- **Communities**: Groups of entities that frequently appear together

### Filtering Logic
- **Russian Actors**: RUS jurisdiction with 150+ occurrences
- **International Actors**: Non-RUS jurisdiction (all occurrences)
- **Temporal Periods**: Pre-Crimea, Post-Crimea, COVID, War periods

## Usage Instructions

1. **Run the Analyzer**:
   ```bash
   python3 enhanced_network_analyzer_v2.py
   ```

2. **Open the HTML File**:
   - Generated file: `enhanced_network_analyzer_v2.html`
   - Open in any modern web browser

3. **Interactive Features**:
   - Click nodes to highlight connections
   - Use filters to explore different aspects
   - Export data for further analysis

## Key Benefits

1. **Accuracy**: Properly handles scraping-based data structure
2. **Performance**: Optimized for large datasets
3. **Context**: Understands the nature of co-occurrence networks
4. **Usability**: Enhanced interface with dataset context
5. **Scalability**: Handles up to 2000 nodes efficiently
6. **Insights**: Provides meaningful metrics for co-occurrence analysis

## File Structure

```
ML_Louvain/
├── enhanced_network_analyzer_v2.py    # Main enhanced analyzer
├── enhanced_network_analyzer_v2.html  # Generated interactive visualization
└── ENHANCEMENT_SUMMARY.md            # This documentation
```

## Future Enhancements

1. **Temporal Analysis**: Enhanced time-based filtering and analysis
2. **Entity Type Analysis**: Deeper analysis of entity types and their relationships
3. **Dynamic Filtering**: Real-time filtering based on multiple criteria
4. **Export Options**: Additional export formats for further analysis
5. **Comparative Analysis**: Tools for comparing networks across periods

## Conclusion

The Enhanced Network Analyzer V2 provides a comprehensive solution for analyzing scraping-based datasets, with particular attention to the co-occurrence nature of the data. The improvements ensure accurate network construction, meaningful metrics, and efficient performance for large datasets. 