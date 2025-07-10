import pandas as pd

# Load the cleaned dataset
input_file = 'ner_entity_dataset_superclean.csv'
df = pd.read_csv(input_file)

# Split into two DataFrames based on occurrence threshold
df_50_or_more = df[df['Occurrences'] >= 50].copy()
df_less_than_50 = df[df['Occurrences'] < 50].copy()

# Save to new CSV files
df_50_or_more.to_csv('ner_entity_dataset_superclean_50plus.csv', index=False)
df_less_than_50.to_csv('ner_entity_dataset_superclean_lt50.csv', index=False)

print(f"Entities with ≥50 occurrences: {df_50_or_more['Entity'].nunique():,}")
print(f"Entities with <50 occurrences: {df_less_than_50['Entity'].nunique():,}")
