import pandas as pd

# Load the dataset
df = pd.read_csv("ner_entity_dataset.csv")

# Show the first few rows
print("🔹 First 5 rows of the dataset:")
print(df.head())

# Show the distribution of entity types
print("\n🔹 Entity Type Distribution:")
print(df['Entity_Type'].value_counts())

# Count unique entities and articles
print("\n🔹 Number of unique entities:", df['Entity'].nunique())
print("🔹 Number of unique articles:", df['Article_ID'].nunique())

# Show the most common entities
print("\n🔹 Top 10 most frequent entities:")
print(df['Entity'].value_counts().head(10))

# Optional: show a sample of context text
print("\n🔹 Sample Contexts:")
print(df[['Entity', 'Context_Text']].drop_duplicates().sample(5, random_state=42))
