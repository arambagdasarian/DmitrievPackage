import pandas as pd

# Load the dataset
df = pd.read_csv('ner_entity_dataset_superclean_lt50.csv')

print(f"Original dataset size: {len(df):,} rows")
print(f"Original unique entities: {df['Entity'].nunique():,}")

# Count LOC entities before filtering
loc_entities_before = df[df['Entity_Type'] == 'LOC']['Entity'].nunique()
print(f"LOC entities before filtering: {loc_entities_before:,}")

# Filter out LOC entities except 'Эр-Рияде'
# Keep all non-LOC entities OR keep LOC entities that are 'Эр-Рияде'
df_filtered = df[(df['Entity_Type'] != 'LOC') | (df['Entity'] == 'Эр-Рияде')].copy()

print(f"Filtered dataset size: {len(df_filtered):,} rows")
print(f"Filtered unique entities: {df_filtered['Entity'].nunique():,}")

# Count LOC entities after filtering
loc_entities_after = df_filtered[df_filtered['Entity_Type'] == 'LOC']['Entity'].nunique()
print(f"LOC entities after filtering: {loc_entities_after:,}")

# Show the remaining LOC entities (should only be 'Эр-Рияде')
remaining_loc_entities = df_filtered[df_filtered['Entity_Type'] == 'LOC']['Entity'].unique()
print(f"Remaining LOC entities: {remaining_loc_entities}")

# Show entity type distribution after filtering
print(f"\nEntity type distribution after filtering:")
print(df_filtered['Entity_Type'].value_counts())

# Save the filtered dataset back to the same file
df_filtered.to_csv('ner_entity_dataset_superclean_lt50.csv', index=False)

print(f"\nFiltered dataset saved to ner_entity_dataset_superclean.csv")
print(f"Removed {len(df) - len(df_filtered):,} rows")
print(f"Removed {loc_entities_before - loc_entities_after:,} LOC entities (kept 'Эр-Рияде')")
