import pandas as pd

# Load the dataset
df = pd.read_csv("matched_entities_post_crimea_cleaned.csv")

# Group by Article_ID and Entity, then count occurrences
duplicates = df.groupby(['Article_ID', 'Entity']).size().reset_index(name='count')

# Filter for duplicates (count > 1)
duplicates = duplicates[duplicates['count'] > 1]

# Print the result
if duplicates.empty:
    print("✅ No article contains the same entity more than once.")
else:
    print("⚠️ Duplicates found:")
    print(duplicates)
