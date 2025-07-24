import pandas as pd

file_path = 'cleaned_articles_combined.csv'

# Load the dataset
df = pd.read_csv(file_path)

# Assign a unique ID to each article (starting from 1)
df['article_id'] = range(1, len(df) + 1)

# Save the updated DataFrame back to the same CSV file
df.to_csv(file_path, index=False)

# Optional: Preview the first 5 rows to confirm
print(df.head())
