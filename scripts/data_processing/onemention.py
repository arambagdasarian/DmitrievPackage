import pandas as pd

# Load the TOP_100 dataset
df = pd.read_csv('ner_entity_dataset_TOP_100.csv')

print(f"Starting with TOP_100 dataset: {len(df):,} rows")
print(f"Unique entities: {df['Entity'].nunique():,}")

# Keep only one row per entity - choosing the one with highest occurrences
# (in case there are ties, it will pick the first one)
df_unique = df.loc[df.groupby('Entity')['Occurrences'].idxmax()].copy()

# Alternative approach: if you want to keep the row with the longest context instead:
# df_unique = df.loc[df.groupby('Entity')['Context_Text'].apply(lambda x: x.str.len().idxmax())].copy()

print(f"\nAfter keeping one mention per entity:")
print(f"Final dataset: {len(df_unique):,} rows")
print(f"Unique entities: {df_unique['Entity'].nunique():,}")

# Verify no duplicates
duplicate_check = df_unique['Entity'].duplicated().sum()
print(f"Duplicate entities: {duplicate_check} (should be 0)")

# Save the unique dataset
output_file = 'ner_entity_dataset_TOP_100_UNIQUE.csv'
df_unique.to_csv(output_file, index=False)
print(f"\nUnique entities dataset saved: {output_file}")

# Show statistics
print(f"\n=== UNIQUE ENTITIES STATISTICS ===")
print(f"Entity types:")
print(df_unique['Entity_Type'].value_counts())

print(f"\nOccurrence statistics:")
print(f"Min: {df_unique['Occurrences'].min()}")
print(f"Max: {df_unique['Occurrences'].max()}")
print(f"Mean: {df_unique['Occurrences'].mean():.1f}")
print(f"Median: {df_unique['Occurrences'].median():.1f}")

print(f"\nTop 20 unique entities:")
top_unique = df_unique.sort_values('Occurrences', ascending=False).head(20)
for i, (idx, row) in enumerate(top_unique.iterrows(), 1):
    print(f"  {i:2d}. {row['Entity']} ({row['Entity_Type']}): {row['Occurrences']:,} occurrences")

# Show sample contexts
print(f"\nSample contexts from top unique entities:")
for i, (idx, row) in enumerate(top_unique.head(3).iterrows(), 1):
    context_preview = str(row['Context_Text'])[:200] + "..." if len(str(row['Context_Text'])) > 200 else str(row['Context_Text'])
    print(f"\n{i}. {row['Entity']} ({row['Occurrences']} occurrences):")
    print(f"   {context_preview}")

print(f"\n🎯 FINAL UNIQUE DATASET 🎯")
print(f"🎯 ENTITIES: {len(df_unique):,} unique entities 🎯")
print(f"🎯 ROWS: {len(df_unique):,} rows (one per entity) 🎯")
