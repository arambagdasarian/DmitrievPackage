import pandas as pd
import ace_tools

# Load the clustered entities CSV
csv_path = "/mnt/data/dmitriev_entities_clustered.csv"
df = pd.read_csv(csv_path)

# Display a snippet of the data to the user
ace_tools.display_dataframe_to_user("Clustered Entities Snippet (first 10 rows)", df.head(10))

# Print structure and basic distributions
print("=== DataFrame Info ===")
print(df.info())

print("\n=== Label Distribution ===")
print(df['label'].value_counts())
