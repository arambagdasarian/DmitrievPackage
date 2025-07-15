import pandas as pd

# Load the Excel file
df = pd.read_excel('unique_entities.xlsx')

print(f"Original dataset: {len(df)} rows")
print(f"Unique entities before merging: {df['Entity'].nunique()}")

# Group by Entity and sum the Occurrences
merged_df = df.groupby('Entity', as_index=False)['Occurrences'].sum()

# Sort by occurrences in descending order
merged_df = merged_df.sort_values('Occurrences', ascending=False)

# Reset index
merged_df = merged_df.reset_index(drop=True)

# Save the merged dataset back to Excel
merged_df.to_excel('merged_dataset.xlsx', index=False)

print(f"\nMerged dataset: {len(merged_df)} rows")
print(f"Unique entities after merging: {merged_df['Entity'].nunique()}")

# Display the top 10 entities with highest occurrences
print(f"\nTop 10 entities by occurrence count:")
for i, row in merged_df.head(10).iterrows():
    print(f"{i+1}. {row['Entity']}: {row['Occurrences']:,}")

print(f"\nMerged dataset saved to 'merged_dataset.xlsx'")
