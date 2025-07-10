import pandas as pd

# Load your cleaned dataset
df = pd.read_csv('ner_entity_dataset_final_clean.csv')

# Filter actors with occurrences around 50 (adjust range as needed)
actors_around_50 = df[(df['Occurrences'] >= 45) & (df['Occurrences'] <= 55)]

# Get unique entities and their occurrence counts
snapshot = actors_around_50[['Entity', 'Entity_Type', 'Occurrences']].drop_duplicates()
snapshot = snapshot.sort_values(by='Occurrences', ascending=False)

# Display the results
print(f"Actors with 45-55 occurrences:")
print(snapshot)

# Break down by entity type
print(f"\nBreakdown by entity type:")
print(snapshot['Entity_Type'].value_counts())

# Show top entities in this range
print(f"\nTop entities in the 45-55 occurrence range:")
for _, row in snapshot.head(15).iterrows():
    print(f"{row['Entity']} ({row['Entity_Type']}): {row['Occurrences']} occurrences")
