import pandas as pd

# Load the CSV file
df = pd.read_csv("matched_entities_filtered.csv")

# Count the number of non-null entries in the 'Entity' column
entity_count = df['Entity'].count()

print(f"Number of entries in the 'Entity' column: {entity_count}")
