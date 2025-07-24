import pandas as pd

# Load the CSV file
df = pd.read_csv("ner_entity_dataset_superclean.csv")

# Count the number of non-null entries in the 'Entity' column
entity_count = df['Entity'].nunique()

print(f"Number of entries in the 'Entity' column: {entity_count}")
