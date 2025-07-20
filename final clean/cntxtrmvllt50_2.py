import pandas as pd
import re
import numpy as np


# Load the radically filtered dataset
df = pd.read_csv('ner_entity_dataset_RADICALLY_FILTERED.csv')

print(f"Starting with radically filtered dataset: {len(df):,} rows")
print(f"Unique entities before filtering: {df['Entity'].nunique():,}")

# Strategic filtering for ~100 entities
# First, let's analyze what we have
entity_stats = df.groupby('Entity').agg({
    'Occurrences': 'first',
    'Context_Text': lambda x: len(set(str(context)[:100] for context in x)),
    'Entity_Type': 'first'
}).reset_index()

entity_stats.columns = ['Entity', 'Occurrences', 'Context_Diversity', 'Entity_Type']

print(f"\nEntity occurrence distribution:")
print(f"Min: {entity_stats['Occurrences'].min()}")
print(f"Max: {entity_stats['Occurrences'].max()}")
print(f"Mean: {entity_stats['Occurrences'].mean():.1f}")
print(f"Median: {entity_stats['Occurrences'].median():.1f}")

# Calculate quality score for ranking
entity_stats['Quality_Score'] = (
    entity_stats['Occurrences'] * 0.6 +  # Weight occurrences heavily
    entity_stats['Context_Diversity'] * 5 * 0.4  # Weight diversity moderately
)

# Sort by quality score
entity_stats_sorted = entity_stats.sort_values('Quality_Score', ascending=False)

# Take top 100 entities (or fewer if we don't have 100)
target_entities = min(100, len(entity_stats_sorted))
top_entities = entity_stats_sorted.head(target_entities)['Entity'].tolist()

print(f"\nSelecting top {target_entities} entities by quality score...")

# Filter the original dataset to only include these top entities
df_filtered = df[df['Entity'].isin(top_entities)].copy()

print(f"\n🎯 TARGET ACHIEVED 🎯")
print(f"Final dataset: {len(df_filtered):,} rows")
print(f"Unique entities: {df_filtered['Entity'].nunique():,}")
print(f"Reduction from original: {((len(df) - len(df_filtered)) / len(df) * 100):.1f}%")

# Save the targeted dataset
output_file = 'ner_entity_dataset_TOP_100.csv'
df_filtered.to_csv(output_file, index=False)
print(f"\nTop 100 entities dataset saved: {output_file}")

# Show detailed statistics
print(f"\n=== TOP 100 ENTITIES STATISTICS ===")
print(f"Entity types:")
print(df_filtered['Entity_Type'].value_counts())

print(f"\nOccurrence statistics:")
print(f"Min: {df_filtered['Occurrences'].min()}")
print(f"Max: {df_filtered['Occurrences'].max()}")
print(f"Mean: {df_filtered['Occurrences'].mean():.1f}")
print(f"Median: {df_filtered['Occurrences'].median():.1f}")

print(f"\nTop 20 entities:")
final_top_entities = df_filtered.groupby('Entity')['Occurrences'].first().sort_values(ascending=False).head(20)
for i, (entity, count) in enumerate(final_top_entities.items(), 1):
    entity_type = df_filtered[df_filtered['Entity'] == entity]['Entity_Type'].iloc[0]
    print(f"  {i:2d}. {entity} ({entity_type}): {count:,} occurrences")

print(f"\nContext diversity analysis:")
final_diversity = df_filtered.groupby('Entity')['Context_Text'].apply(
    lambda x: len(set(str(context)[:100] for context in x))
)
print(f"Average contexts per entity: {final_diversity.mean():.1f}")
print(f"Min contexts per entity: {final_diversity.min()}")
print(f"Max contexts per entity: {final_diversity.max()}")

# Show sample high-quality contexts
print(f"\nSample contexts from top entities:")
top_3_entities = final_top_entities.head(3)
for i, (entity, count) in enumerate(top_3_entities.items(), 1):
    sample_context = df_filtered[df_filtered['Entity'] == entity]['Context_Text'].iloc[0]
    context_preview = str(sample_context)[:200] + "..." if len(str(sample_context)) > 200 else str(sample_context)
    print(f"\n{i}. {entity} ({count} occurrences):")
    print(f"   {context_preview}")

print(f"\n🎯 FINAL ANSWER: {df_filtered['Entity'].nunique():,} UNIQUE ENTITIES 🎯")
print(f"🎯 TOTAL NODES: {len(df_filtered):,} NODES 🎯")
